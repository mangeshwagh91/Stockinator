"""Indicator calculation service using TA-Lib and pandas"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("⚠️  TA-Lib not installed. Indicator calculations will be limited.")

from app.core.exceptions import InvalidIndicatorError


class IndicatorService:
    """Service for calculating technical indicators"""
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators for the given OHLCV dataframe
        
        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
        
        Returns:
            DataFrame with all indicator columns added
        """
        if not TALIB_AVAILABLE:
            print("⚠️  Skipping indicator calculation - TA-Lib not installed")
            return df  # Return dataframe as-is without indicators
            
        if df.empty or len(df) < 200:
            raise InvalidIndicatorError("Insufficient data for indicator calculation")
        
        df = df.copy()
        
        # Trend indicators
        df = self._calculate_moving_averages(df)
        
        # Momentum indicators
        df = self._calculate_momentum(df)
        
        # Volatility indicators
        df = self._calculate_volatility(df)
        
        # Volume indicators
        df = self._calculate_volume(df)
        
        # Trend strength
        df = self._calculate_trend_strength(df)
        
        return df
    
    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages"""
        close = df['close'].values
        
        # Simple Moving Averages
        df['sma_20'] = talib.SMA(close, timeperiod=20)
        df['sma_50'] = talib.SMA(close, timeperiod=50)
        df['sma_200'] = talib.SMA(close, timeperiod=200)
        
        # Exponential Moving Averages
        df['ema_12'] = talib.EMA(close, timeperiod=12)
        df['ema_26'] = talib.EMA(close, timeperiod=26)
        
        return df
    
    def _calculate_momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum indicators"""
        close = df['close'].values
        
        # RSI - Relative Strength Index
        df['rsi'] = talib.RSI(close, timeperiod=14)
        
        # MACD - Moving Average Convergence Divergence
        macd, macdsignal, macdhist = talib.MACD(
            close,
            fastperiod=12,
            slowperiod=26,
            signalperiod=9
        )
        df['macd'] = macd
        df['macd_signal'] = macdsignal
        df['macd_histogram'] = macdhist
        
        # Stochastic Oscillator
        high = df['high'].values
        low = df['low'].values
        slowk, slowd = talib.STOCH(
            high, low, close,
            fastk_period=14,
            slowk_period=3,
            slowd_period=3
        )
        df['stochastic_k'] = slowk
        df['stochastic_d'] = slowd
        
        # ROC - Rate of Change
        df['roc'] = talib.ROC(close, timeperiod=10)
        
        return df
    
    def _calculate_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility indicators"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(
            close,
            timeperiod=20,
            nbdevup=2,
            nbdevdn=2,
            matype=0
        )
        df['bollinger_upper'] = upper
        df['bollinger_middle'] = middle
        df['bollinger_lower'] = lower
        
        # ATR - Average True Range
        df['atr'] = talib.ATR(high, low, close, timeperiod=14)
        
        return df
    
    def _calculate_volume(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volume indicators"""
        close = df['close'].values
        volume = df['volume'].values
        
        # OBV - On Balance Volume
        df['obv'] = talib.OBV(close, volume)
        
        # VWAP - Volume Weighted Average Price (manual calculation)
        df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
        
        return df
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate trend strength indicators"""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # ADX - Average Directional Index
        df['adx'] = talib.ADX(high, low, close, timeperiod=14)
        df['adx_pos'] = talib.PLUS_DI(high, low, close, timeperiod=14)
        df['adx_neg'] = talib.MINUS_DI(high, low, close, timeperiod=14)
        
        return df
    
    def extract_latest_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Extract latest indicator values as features for ML model
        
        Args:
            df: DataFrame with calculated indicators
        
        Returns:
            Dictionary of feature names and values
        """
        if df.empty:
            raise InvalidIndicatorError("Cannot extract features from empty dataframe")
        
        latest = df.iloc[-1]
        
        features = {
            # Momentum
            'rsi': latest.get('rsi', 50.0),
            'macd': latest.get('macd', 0.0),
            'macd_signal': latest.get('macd_signal', 0.0),
            'macd_histogram': latest.get('macd_histogram', 0.0),
            'stochastic_k': latest.get('stochastic_k', 50.0),
            'stochastic_d': latest.get('stochastic_d', 50.0),
            'roc': latest.get('roc', 0.0),
            
            # Trend
            'sma_20': latest.get('sma_20', latest['close']),
            'sma_50': latest.get('sma_50', latest['close']),
            'ema_12': latest.get('ema_12', latest['close']),
            'ema_26': latest.get('ema_26', latest['close']),
            
            # Volatility
            'atr': latest.get('atr', 0.0),
            'bollinger_position': self._calculate_bollinger_position(latest),
            
            # Trend strength
            'adx': latest.get('adx', 25.0),
            'adx_pos': latest.get('adx_pos', 25.0),
            'adx_neg': latest.get('adx_neg', 25.0),
            
            # Price position
            'price_to_sma20': latest['close'] / latest.get('sma_20', latest['close']),
            'price_to_sma50': latest['close'] / latest.get('sma_50', latest['close']),
        }
        
        # Remove NaN values
        features = {k: float(v) if not pd.isna(v) else 0.0 for k, v in features.items()}
        
        return features
    
    def _calculate_bollinger_position(self, row: pd.Series) -> float:
        """Calculate position within Bollinger Bands (0 to 1)"""
        upper = row.get('bollinger_upper', row['close'])
        lower = row.get('bollinger_lower', row['close'])
        close = row['close']
        
        if upper == lower:
            return 0.5
        
        return (close - lower) / (upper - lower)


# Global instance
indicator_service = IndicatorService()
