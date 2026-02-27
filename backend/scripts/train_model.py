"""Train initial ML model using historical data"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.services.ml_service import ml_service


def generate_synthetic_training_data(n_samples: int = 1000):
    """
    Generate synthetic training data for initial model
    In production, replace this with actual historical data
    """
    print(f"📊 Generating {n_samples} synthetic training samples...")
    
    np.random.seed(42)
    
    X_data = []
    y_data = []
    
    for _ in range(n_samples):
        # Generate random indicator values
        rsi = np.random.uniform(20, 80)
        macd = np.random.uniform(-2, 2)
        macd_signal = np.random.uniform(-2, 2)
        macd_histogram = macd - macd_signal
        stochastic_k = np.random.uniform(20, 80)
        stochastic_d = np.random.uniform(20, 80)
        roc = np.random.uniform(-5, 5)
        adx = np.random.uniform(10, 50)
        adx_pos = np.random.uniform(10, 40)
        adx_neg = np.random.uniform(10, 40)
        atr = np.random.uniform(0.5, 3.0)
        bollinger_position = np.random.uniform(0, 1)
        price_to_sma20 = np.random.uniform(0.95, 1.05)
        price_to_sma50 = np.random.uniform(0.95, 1.05)
        sentiment_score = np.random.uniform(-0.5, 0.5)
        
        features = [
            rsi, macd, macd_signal, macd_histogram,
            stochastic_k, stochastic_d, roc,
            adx, adx_pos, adx_neg, atr,
            bollinger_position, price_to_sma20, price_to_sma50,
            sentiment_score
        ]
        
        # Simple rule-based labeling (success probability)
        # This is a simplified model - replace with actual historical outcomes
        success_score = 0
        
        # RSI contributes
        if 30 <= rsi <= 40:
            success_score += 20
        elif 60 <= rsi <= 70:
            success_score += 10
        elif rsi > 80 or rsi < 20:
            success_score -= 15
        
        # MACD contributes
        if macd > macd_signal:
            success_score += 15
        else:
            success_score -= 10
        
        # ADX contributes (trend strength)
        if adx > 25:
            success_score += 15
        
        # Price vs MA
        if price_to_sma20 > 1.02:
            success_score += 10
        elif price_to_sma20 < 0.98:
            success_score -= 10
        
        # Sentiment contributes
        success_score += sentiment_score * 20
        
        # Add some noise
        success_score += np.random.normal(0, 10)
        
        # Label: 1 if success_score > 50, else 0
        label = 1 if success_score > 50 else 0
        
        X_data.append(features)
        y_data.append(label)
    
    return np.array(X_data), np.array(y_data)


def train_initial_model():
    """Train the initial XGBoost model"""
    print("🤖 Training initial ML model...")
    
    # Generate training data
    X, y = generate_synthetic_training_data(n_samples=2000)
    
    print(f"✓ Generated {len(X)} samples")
    print(f"  - Positive samples (winners): {sum(y)}")
    print(f"  - Negative samples (losers): {len(y) - sum(y)}")
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train XGBoost model
    print("\n📈 Training XGBoost classifier...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        objective='binary:logistic',
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False
    )
    
    # Evaluate
    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)
    
    print(f"\n📊 Model Performance:")
    print(f"  Train Accuracy: {train_score:.3f}")
    print(f"  Test Accuracy:  {test_score:.3f}")
    
    # Predictions
    y_pred = model.predict(X_test_scaled)
    
    print(f"\n📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Loss', 'Win']))
    
    print(f"\n🔢 Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Feature importance
    feature_names = [
        'rsi', 'macd', 'macd_signal', 'macd_histogram',
        'stochastic_k', 'stochastic_d', 'roc',
        'adx', 'adx_pos', 'adx_neg', 'atr',
        'bollinger_position', 'price_to_sma20', 'price_to_sma50',
        'sentiment_score'
    ]
    
    importances = model.feature_importances_
    feature_importance = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    
    print(f"\n🎯 Feature Importance (Top 10):")
    for name, importance in feature_importance[:10]:
        print(f"  {name:20s}: {importance:.3f}")
    
    # Save model
    print(f"\n💾 Saving model...")
    ml_service.save_model(
        model=model,
        scaler=scaler,
        feature_names=feature_names,
        model_name="xgboost_model.pkl"
    )
    
    print("\n✅ Initial model training completed!")
    print("\n⚠️  Note: This is a synthetic model. Retrain with real data for production use.")


if __name__ == "__main__":
    train_initial_model()
