"""ML service for loading and using the trained model"""
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Optional
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from app.core.exceptions import ModelNotFoundError


class MLService:
    """Service for ML model predictions"""
    
    def __init__(self):
        self.model: Optional[xgb.XGBClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: Optional[list] = None
        self.model_path = Path("backend/models")
        self.model_path.mkdir(parents=True, exist_ok=True)
    
    def load_model(self, model_name: str = "xgboost_model.pkl"):
        """
        Load the trained model from disk
        
        Args:
            model_name: Name of the model file
        """
        model_file = self.model_path / model_name
        
        if not model_file.exists():
            raise ModelNotFoundError(f"Model file not found: {model_file}")
        
        with open(model_file, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data.get('scaler')
        self.feature_names = model_data.get('feature_names', [])
        
        print(f"✓ Model loaded: {model_name}")
    
    def predict_success_score(self, features: Dict[str, float], sentiment_score: float = 0.0) -> float:
        """
        Predict success score for a trade
        
        Args:
            features: Dictionary of indicator features
            sentiment_score: Sentiment score from news (-1 to 1)
        
        Returns:
            Success score (0 to 100)
        """
        if self.model is None:
            # If model not loaded, return a default score based on simple rules
            return self._fallback_score(features, sentiment_score)
        
        # Add sentiment to features
        features_with_sentiment = features.copy()
        features_with_sentiment['sentiment_score'] = sentiment_score
        
        # Convert to numpy array in correct order
        if self.feature_names:
            feature_vector = np.array([
                features_with_sentiment.get(name, 0.0)
                for name in self.feature_names
            ]).reshape(1, -1)
        else:
            feature_vector = np.array(list(features_with_sentiment.values())).reshape(1, -1)
        
        # Scale features if scaler is available
        if self.scaler:
            feature_vector = self.scaler.transform(feature_vector)
        
        # Predict probability
        probability = self.model.predict_proba(feature_vector)[0][1]
        
        # Convert to 0-100 score
        score = probability * 100
        
        return float(score)
    
    def _fallback_score(self, features: Dict[str, float], sentiment_score: float) -> float:
        """
        Fallback scoring when model is not available
        Uses simple technical analysis rules
        
        Args:
            features: Dictionary of indicator features
            sentiment_score: Sentiment score
        
        Returns:
            Score (0 to 100)
        """
        score = 50.0  # Base score
        
        # RSI scoring
        rsi = features.get('rsi', 50)
        if 30 <= rsi <= 40:
            score += 10  # Oversold, good for buying
        elif 60 <= rsi <= 70:
            score += 5   # Moderate bullish
        elif rsi > 80:
            score -= 10  # Overbought
        
        # MACD scoring
        macd = features.get('macd', 0)
        macd_signal = features.get('macd_signal', 0)
        if macd > macd_signal:
            score += 10  # Bullish crossover
        else:
            score -= 5
        
        # Trend scoring (ADX)
        adx = features.get('adx', 25)
        if adx > 25:
            score += 10  # Strong trend
        
        # Price vs SMA
        price_to_sma20 = features.get('price_to_sma20', 1.0)
        if price_to_sma20 > 1.02:
            score += 10  # Price above SMA
        elif price_to_sma20 < 0.98:
            score -= 10
        
        # Sentiment bonus
        score += sentiment_score * 10  # -10 to +10 based on sentiment
        
        # Clamp to 0-100
        score = max(0, min(100, score))
        
        return score
    
    def save_model(self, model, scaler=None, feature_names=None, model_name: str = "xgboost_model.pkl"):
        """
        Save a trained model to disk
        
        Args:
            model: Trained model
            scaler: Feature scaler (optional)
            feature_names: List of feature names
            model_name: Name for the model file
        """
        model_data = {
            'model': model,
            'scaler': scaler,
            'feature_names': feature_names
        }
        
        model_file = self.model_path / model_name
        with open(model_file, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✓ Model saved: {model_file}")


# Global instance
ml_service = MLService()
