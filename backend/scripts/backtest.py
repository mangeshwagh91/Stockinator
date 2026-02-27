"""Backtesting script for testing strategy on historical data"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.market_data import market_data_service
from app.services.indicator_service import indicator_service
from app.services.ml_service import ml_service


def backtest(
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 100000.0,
    threshold: float = 80.0
):
    """
    Backtest the trading strategy
    
    Args:
        symbol: Trading symbol
        start_date: Start date for backtest
        end_date: End date for backtest
        initial_capital: Initial capital amount
        threshold: ML score threshold for trades
    """
    print(f"🔄 Backtesting {symbol} from {start_date.date()} to {end_date.date()}")
    print(f"💰 Initial capital: ${initial_capital:,.2f}")
    print(f"🎯 Threshold: {threshold}")
    print("-" * 60)
    
    # Fetch historical data
    print("📊 Fetching historical data...")
    df = market_data_service.fetch_historical_data(
        symbol=symbol,
        interval="1h",
        start_time=start_date,
        end_time=end_date,
        limit=10000
    )
    
    if df.empty:
        print("❌ No data available for backtesting")
        return
    
    print(f"✓ Loaded {len(df)} candles")
    
    # Calculate indicators
    print("📈 Calculating indicators...")
    df_with_indicators = indicator_service.calculate_all_indicators(df)
    
    # Remove NaN rows
    df_with_indicators = df_with_indicators.dropna()
    
    print(f"✓ {len(df_with_indicators)} valid candles with indicators")
    
    # Try to load ML model
    try:
        ml_service.load_model()
        print("✓ ML model loaded")
    except:
        print("⚠️  ML model not found, using fallback scoring")
    
    # Run backtest
    capital = initial_capital
    position = None
    trades = []
    
    for i in range(len(df_with_indicators)):
        row = df_with_indicators.iloc[i]
        
        # Extract features
        features = indicator_service.extract_latest_features(
            df_with_indicators.iloc[:i+1]
        )
        
        # Get success score
        success_score = ml_service.predict_success_score(features, sentiment_score=0.0)
        
        # Trading logic
        if position is None and success_score > threshold:
            # Enter position
            entry_price = row['close']
            position_size = capital * 0.95  # Use 95% of capital
            shares = position_size / entry_price
            
            position = {
                'entry_timestamp': row.name,
                'entry_price': entry_price,
                'shares': shares,
                'success_score': success_score
            }
            
            print(f"📈 BUY  @ {entry_price:.2f} | Score: {success_score:.1f} | Shares: {shares:.2f}")
        
        elif position is not None:
            # Check exit conditions
            current_price = row['close']
            entry_price = position['entry_price']
            
            # Simple exit: 2% profit or 1% loss
            pnl_pct = (current_price - entry_price) / entry_price * 100
            
            should_exit = False
            exit_reason = ""
            
            if pnl_pct >= 2.0:
                should_exit = True
                exit_reason = "Take Profit (+2%)"
            elif pnl_pct <= -1.0:
                should_exit = True
                exit_reason = "Stop Loss (-1%)"
            
            if should_exit:
                # Exit position
                exit_price = current_price
                pnl = (exit_price - entry_price) * position['shares']
                pnl_pct = (exit_price / entry_price - 1) * 100
                
                # Update capital
                capital += pnl
                
                trade = {
                    'entry_timestamp': position['entry_timestamp'],
                    'exit_timestamp': row.name,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'shares': position['shares'],
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'success_score': position['success_score'],
                    'exit_reason': exit_reason
                }
                
                trades.append(trade)
                
                print(f"📉 SELL @ {exit_price:.2f} | P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%) | {exit_reason}")
                print(f"💰 Capital: ${capital:,.2f}")
                
                position = None
    
    # Close any open position at end
    if position is not None:
        exit_price = df_with_indicators.iloc[-1]['close']
        pnl = (exit_price - position['entry_price']) * position['shares']
        capital += pnl
        
        print(f"\n📉 Position closed at end @ {exit_price:.2f}")
    
    # Results
    print("\n" + "=" * 60)
    print("📊 BACKTEST RESULTS")
    print("=" * 60)
    
    total_return = capital - initial_capital
    total_return_pct = (capital / initial_capital - 1) * 100
    
    print(f"\n💰 Final Capital:     ${capital:,.2f}")
    print(f"📈 Total Return:      ${total_return:,.2f} ({total_return_pct:+.2f}%)")
    print(f"🔢 Number of Trades:  {len(trades)}")
    
    if trades:
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / len(trades) * 100
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        print(f"✅ Winning Trades:    {len(winning_trades)} ({win_rate:.1f}%)")
        print(f"❌ Losing Trades:     {len(losing_trades)}")
        print(f"📊 Average Win:       ${avg_win:,.2f}")
        print(f"📊 Average Loss:      ${avg_loss:,.2f}")
        
        best_trade = max(trades, key=lambda t: t['pnl'])
        worst_trade = min(trades, key=lambda t: t['pnl'])
        
        print(f"🏆 Best Trade:        ${best_trade['pnl']:,.2f} ({best_trade['pnl_pct']:+.2f}%)")
        print(f"💔 Worst Trade:       ${worst_trade['pnl']:,.2f} ({worst_trade['pnl_pct']:+.2f}%)")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backtest trading strategy")
    parser.add_argument('symbol', type=str, help='Trading symbol (e.g., AAPL)')
    parser.add_argument('--days', type=int, default=30, help='Number of days to backtest')
    parser.add_argument('--capital', type=float, default=100000, help='Initial capital')
    parser.add_argument('--threshold', type=float, default=80, help='ML score threshold')
    
    args = parser.parse_args()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    backtest(
        symbol=args.symbol,
        start_date=start_date,
        end_date=end_date,
        initial_capital=args.capital,
        threshold=args.threshold
    )
