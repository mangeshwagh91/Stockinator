"""Model retraining Celery task"""
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.signal import Signal
from app.models.trade import Trade, TradeStatus
from app.services.ml_service import ml_service


@celery_app.task(name='retrain_model_task')
def retrain_model_task(days_lookback: int = 30):
    """
    Retrain the ML model with recent data
    
    Args:
        days_lookback: Number of days of historical data to use
    """
    db = SessionLocal()
    
    try:
        print(f"🤖 Starting model retraining with {days_lookback} days of data...")
        
        # Fetch training data
        cutoff_date = datetime.now() - timedelta(days=days_lookback)
        
        # Get all signals with their outcomes
        signals = db.query(Signal).filter(
            Signal.created_at >= cutoff_date,
            Signal.executed == True,
            Signal.trade_id.isnot(None)
        ).all()
        
        if len(signals) < 50:
            print(f"⚠️ Insufficient data for retraining ({len(signals)} samples)")
            return {"status": "skipped", "reason": "insufficient_data"}
        
        print(f"📊 Found {len(signals)} signals for training")
        
        # Build training dataset
        X_data = []
        y_data = []
        
        for signal in signals:
            # Get the corresponding trade
            trade = db.query(Trade).filter(Trade.id == signal.trade_id).first()
            
            if not trade or trade.status != TradeStatus.FILLED or trade.profit_loss is None:
                continue
            
            # Features from signal
            features = signal.features or {}
            feature_vector = [
                features.get('rsi', 50.0),
                features.get('macd', 0.0),
                features.get('macd_signal', 0.0),
                features.get('macd_histogram', 0.0),
                features.get('stochastic_k', 50.0),
                features.get('stochastic_d', 50.0),
                features.get('roc', 0.0),
                features.get('adx', 25.0),
                features.get('adx_pos', 25.0),
                features.get('adx_neg', 25.0),
                features.get('atr', 0.0),
                features.get('bollinger_position', 0.5),
                features.get('price_to_sma20', 1.0),
                features.get('price_to_sma50', 1.0),
                signal.sentiment_score or 0.0
            ]
            
            # Label: 1 if profitable, 0 if not
            label = 1 if trade.profit_loss > 0 else 0
            
            X_data.append(feature_vector)
            y_data.append(label)
        
        if len(X_data) < 50:
            print(f"⚠️ Insufficient valid samples ({len(X_data)} samples)")
            return {"status": "skipped", "reason": "insufficient_valid_data"}
        
        # Convert to numpy arrays
        X = np.array(X_data)
        y = np.array(y_data)
        
        print(f"📊 Training set: {len(X)} samples, {sum(y)} wins, {len(y) - sum(y)} losses")
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train XGBoost model
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            objective='binary:logistic',
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        print(f"🎯 Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")
        
        # Save model
        feature_names = [
            'rsi', 'macd', 'macd_signal', 'macd_histogram',
            'stochastic_k', 'stochastic_d', 'roc',
            'adx', 'adx_pos', 'adx_neg', 'atr',
            'bollinger_position', 'price_to_sma20', 'price_to_sma50',
            'sentiment_score'
        ]
        
        ml_service.save_model(
            model=model,
            scaler=scaler,
            feature_names=feature_names,
            model_name=f"xgboost_model_{datetime.now().strftime('%Y%m%d')}.pkl"
        )
        
        # Load the new model
        ml_service.model = model
        ml_service.scaler = scaler
        ml_service.feature_names = feature_names
        
        print(f"✅ Model retrained and saved successfully!")
        
        return {
            "status": "completed",
            "samples": len(X),
            "train_accuracy": float(train_score),
            "test_accuracy": float(test_score),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"❌ Error retraining model: {e}")
        return {"status": "error", "message": str(e)}
    
    finally:
        db.close()


@celery_app.task(name='backtest_strategy')
def backtest_strategy(symbol: str, days: int = 30):
    """
    Backtest the trading strategy on historical data
    
    Args:
        symbol: Trading symbol
        days: Number of days to backtest
    """
    # This would implement backtesting logic
    # Placeholder for now
    print(f"🔄 Backtesting {symbol} for {days} days...")
    
    return {
        "status": "completed",
        "symbol": symbol,
        "days": days,
        "message": "Backtest functionality to be implemented"
    }
