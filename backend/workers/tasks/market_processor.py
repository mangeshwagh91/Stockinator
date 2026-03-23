"""Market data processor - consumes market data and runs trading pipeline"""
from datetime import datetime
from sqlalchemy.orm import Session

from workers.celery_app import celery_app
from app.core.database import SessionLocal, influx_db
from app.services.market_data import market_data_service
from app.services.indicator_service import indicator_service
from app.services.ml_service import ml_service
from app.services.news_service import news_service
from app.services.decision_engine import decision_engine
from app.services.strategies import strategy_registry
from app.services.broker_service import broker_service
from app.models.signal import Signal
from app.models.trade import Trade, TradeType, TradeStatus
from app.api.v1.endpoints.ws import broadcast_score_update, broadcast_trade_execution


@celery_app.task(name='process_market_candle')
def process_market_candle(symbol: str, interval: str, candle_data: dict):
    """
    Process a new market candle and run the trading pipeline
    
    Args:
        symbol: Trading symbol
        interval: Time interval
        candle_data: OHLCV data
    """
    db = SessionLocal()
    
    try:
        print(f"📊 Processing {symbol} {interval} candle at {candle_data.get('timestamp')}")
        
        # Step 1: Fetch recent historical data for indicator calculation
        df = market_data_service.fetch_historical_data(
            symbol=symbol,
            interval=interval,
            limit=200
        )
        
        if df.empty or len(df) < 50:
            print(f"⚠️ Insufficient data for {symbol}")
            return {"status": "skipped", "reason": "insufficient_data"}
        
        # Step 2: Calculate indicators
        df_with_indicators = indicator_service.calculate_all_indicators(df)
        
        # Store indicators to InfluxDB
        latest_row = df_with_indicators.iloc[-1]
        _store_indicators_to_influx(symbol, interval, latest_row, df_with_indicators.index[-1])
        
        # Step 3: Extract features for ML
        features = indicator_service.extract_latest_features(df_with_indicators)
        
        # Step 4: Get latest news sentiment
        sentiment_score = news_service.get_latest_sentiment(symbol, db, hours=24)
        
        # Step 5: Calculate success score using ML model
        success_score = ml_service.predict_success_score(features, sentiment_score)

        # Step 5b: Evaluate algo strategies (ensemble)
        strategy_eval = strategy_registry.evaluate(
            features=features,
            sentiment_score=sentiment_score,
        )

        # Build multi-agent component scores in 0-100 range.
        component_scores = {
            "ml": success_score,
            "news": max(0.0, min(100.0, (sentiment_score + 1.0) * 50.0)),
            "algo": strategy_eval["algo_score"],
            "regime": max(0.0, min(100.0, (features.get("adx", 25.0) / 50.0) * 100.0)),
        }
        direction_hint = strategy_eval["direction_hint"]
        
        print(f"🎯 Success score for {symbol}: {success_score:.2f}")
        
        # Save signal to database
        signal = Signal(
            symbol=symbol,
            interval=interval,
            success_score=success_score,
            threshold=decision_engine.threshold,
            features={
                **features,
                "strategy_breakdown": strategy_eval["breakdown"],
            },
            rsi=features.get('rsi'),
            macd=features.get('macd'),
            macd_signal=features.get('macd_signal'),
            adx=features.get('adx'),
            sma_20=features.get('sma_20'),
            sma_50=features.get('sma_50'),
            price=float(latest_row['close']),
            volume=float(latest_row['volume']),
            sentiment_score=sentiment_score
        )
        db.add(signal)
        db.commit()
        db.refresh(signal)
        
        # Broadcast score update via WebSocket
        import asyncio
        try:
            asyncio.create_task(broadcast_score_update(symbol, success_score, features))
        except:
            pass  # WebSocket might not be available
        
        # Step 6: Check if we should trade
        current_price = float(latest_row['close'])
        
        # Check if trading is active (would be checked via Redis flag)
        from app.api.v1.endpoints.control import trading_active
        
        if not trading_active:
            print(f"💤 Trading not active")
            signal.action = "HOLD"
            db.commit()
            return {"status": "hold", "reason": "trading_inactive", "score": success_score}
        
        # Make trading decision
        try:
            decision = decision_engine.should_trade(
                symbol=symbol,
                success_score=success_score,
                current_price=current_price,
                db=db,
                features=features,
                component_scores=component_scores,
                direction_hint=direction_hint,
            )
            
            signal.action = decision['action']
            signal.confidence = decision.get('final_score', success_score)
            
            if decision['should_trade']:
                # Execute trade
                trade_result = _execute_trade(
                    symbol=symbol,
                    decision=decision,
                    success_score=success_score,
                    db=db
                )
                
                signal.executed = True
                signal.trade_id = trade_result['trade_id']
                
                print(f"✅ Trade executed: {trade_result}")
                
                db.commit()
                return {
                    "status": "traded",
                    "score": success_score,
                    "final_score": decision.get('final_score', success_score),
                    "trade_id": trade_result['trade_id']
                }
            else:
                print(f"⏸️ No trade: {decision['reason']}")
                db.commit()
                return {
                    "status": "no_trade",
                    "score": success_score,
                    "final_score": decision.get('final_score', success_score),
                    "reason": decision['reason']
                }
        
        except Exception as e:
            print(f"❌ Decision/execution error: {e}")
            signal.action = "ERROR"
            db.commit()
            return {"status": "error", "message": str(e)}
    
    except Exception as e:
        print(f"❌ Error processing candle: {e}")
        return {"status": "error", "message": str(e)}
    
    finally:
        db.close()


def _store_indicators_to_influx(symbol: str, interval: str, row, timestamp):
    """Store indicator values to InfluxDB"""
    tags = {
        "symbol": symbol,
        "interval": interval
    }
    
    fields = {
        "rsi": float(row.get('rsi', 0)) if not pd.isna(row.get('rsi')) else 50.0,
        "macd": float(row.get('macd', 0)) if not pd.isna(row.get('macd')) else 0.0,
        "macd_signal": float(row.get('macd_signal', 0)) if not pd.isna(row.get('macd_signal')) else 0.0,
        "adx": float(row.get('adx', 0)) if not pd.isna(row.get('adx')) else 25.0,
        "sma_20": float(row.get('sma_20', 0)) if not pd.isna(row.get('sma_20')) else float(row['close']),
        "sma_50": float(row.get('sma_50', 0)) if not pd.isna(row.get('sma_50')) else float(row['close']),
        "atr": float(row.get('atr', 0)) if not pd.isna(row.get('atr')) else float(row['close']) * 0.02,
    }
    
    import pandas as pd
    influx_db.write_point(
        measurement="indicators",
        tags=tags,
        fields=fields,
        timestamp=timestamp
    )


def _execute_trade(symbol: str, decision: dict, success_score: float, db: Session) -> dict:
    """Execute a trade based on decision"""
    # Place order with broker
    order_result = broker_service.place_order(
        symbol=symbol,
        side=decision['action'],
        quantity=decision['quantity'],
        stop_loss=decision.get('stop_loss'),
        take_profit=decision.get('take_profit')
    )
    
    # Create trade record
    trade = Trade(
        symbol=symbol,
        trade_type=TradeType.BUY if decision['action'] == 'BUY' else TradeType.SELL,
        quantity=decision['quantity'],
        entry_price=order_result.get('filled_price'),
        stop_loss=decision.get('stop_loss'),
        take_profit=decision.get('take_profit'),
        success_score=success_score,
        broker_order_id=order_result.get('broker_order_id'),
        status=TradeStatus.PENDING,
        is_paper=True  # Based on settings
    )
    
    db.add(trade)
    db.commit()
    db.refresh(trade)
    
    # Broadcast trade execution
    import asyncio
    try:
        trade_data = {
            "id": trade.id,
            "symbol": trade.symbol,
            "type": trade.trade_type.value,
            "quantity": trade.quantity,
            "price": trade.entry_price,
            "score": success_score
        }
        asyncio.create_task(broadcast_trade_execution(trade_data))
    except:
        pass
    
    return {
        "trade_id": trade.id,
        "broker_order_id": order_result.get('broker_order_id'),
        "status": "executed"
    }


@celery_app.task(name='monitor_open_trades')
def monitor_open_trades():
    """Monitor open trades for stop loss / take profit"""
    db = SessionLocal()
    
    try:
        # Get all open trades
        open_trades = db.query(Trade).filter(
            Trade.status.in_([TradeStatus.PENDING, TradeStatus.PARTIAL, TradeStatus.FILLED]),
            Trade.closed_at.is_(None)
        ).all()
        
        for trade in open_trades:
            # Check order status with broker
            try:
                order_status = broker_service.get_order_status(trade.broker_order_id)
                
                # Update trade status
                if order_status['status'] == 'filled' and trade.status != TradeStatus.FILLED:
                    trade.status = TradeStatus.FILLED
                    trade.filled_at = datetime.now()
                    trade.entry_price = order_status.get('filled_price', trade.entry_price)
                
                # Check if stop loss / take profit hit
                if trade.status == TradeStatus.FILLED:
                    current_price = market_data_service.get_latest_price(trade.symbol)
                    
                    should_close = False
                    reason = ""
                    
                    if trade.stop_loss and current_price <= trade.stop_loss:
                        should_close = True
                        reason = "stop_loss"
                    elif trade.take_profit and current_price >= trade.take_profit:
                        should_close = True
                        reason = "take_profit"
                    
                    if should_close:
                        # Close the position
                        _close_trade(trade, current_price, reason, db)
            
            except Exception as e:
                print(f"Error monitoring trade {trade.id}: {e}")
        
        db.commit()
    
    except Exception as e:
        print(f"Error in monitor_open_trades: {e}")
    
    finally:
        db.close()


def _close_trade(trade: Trade, exit_price: float, reason: str, db: Session):
    """Close a trade"""
    # Calculate P&L
    if trade.trade_type == TradeType.BUY:
        pnl = (exit_price - trade.entry_price) * trade.quantity
    else:
        pnl = (trade.entry_price - exit_price) * trade.quantity
    
    trade.exit_price = exit_price
    trade.profit_loss = pnl - trade.brokerage - trade.slippage
    trade.profit_loss_percentage = (pnl / (trade.entry_price * trade.quantity)) * 100
    trade.status = TradeStatus.FILLED
    trade.closed_at = datetime.now()
    trade.notes = f"{trade.notes or ''} Closed by {reason}"
    
    print(f"🔒 Trade {trade.id} closed: {reason}, P&L: {trade.profit_loss:.2f}")
