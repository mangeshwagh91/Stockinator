"""Indicator calculation service using TA-Lib and pandas"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("[WARNING] TA-Lib not installed. Indicator calculations will be limited.")

from app.core.exceptions import InvalidIndicatorError


class IndicatorService:
    """Service for calculating technical indicators"""

    def _calculate_all_indicators_fallback(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pandas/numpy fallback when TA-Lib is unavailable."""
        out = df.copy()

        close = out["close"]
        high = out["high"]
        low = out["low"]
        volume = out["volume"]

        out["sma_20"] = close.rolling(window=20, min_periods=1).mean()
        out["sma_50"] = close.rolling(window=50, min_periods=1).mean()
        out["sma_200"] = close.rolling(window=200, min_periods=1).mean()
        out["ema_12"] = close.ewm(span=12, adjust=False).mean()
        out["ema_26"] = close.ewm(span=26, adjust=False).mean()

        delta = close.diff().fillna(0.0)
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14, min_periods=14).mean()
        avg_loss = loss.rolling(window=14, min_periods=14).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        out["rsi"] = (100 - (100 / (1 + rs))).fillna(50.0)

        out["macd"] = out["ema_12"] - out["ema_26"]
        out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()
        out["macd_histogram"] = out["macd"] - out["macd_signal"]

        lowest_low = low.rolling(window=14, min_periods=1).min()
        highest_high = high.rolling(window=14, min_periods=1).max()
        denom = (highest_high - lowest_low).replace(0, np.nan)
        out["stochastic_k"] = (((close - lowest_low) / denom) * 100).fillna(50.0)
        out["stochastic_d"] = out["stochastic_k"].rolling(window=3, min_periods=1).mean()
        out["roc"] = (close.pct_change(periods=10) * 100).fillna(0.0)

        out["bollinger_middle"] = close.rolling(window=20, min_periods=1).mean()
        rolling_std = close.rolling(window=20, min_periods=1).std().fillna(0.0)
        out["bollinger_upper"] = out["bollinger_middle"] + (2 * rolling_std)
        out["bollinger_lower"] = out["bollinger_middle"] - (2 * rolling_std)

        tr_components = pd.concat(
            [
                (high - low).abs(),
                (high - close.shift(1)).abs(),
                (low - close.shift(1)).abs(),
            ],
            axis=1,
        )
        true_range = tr_components.max(axis=1)
        out["atr"] = true_range.rolling(window=14, min_periods=1).mean().fillna(0.0)

        direction = np.sign(close.diff().fillna(0.0))
        out["obv"] = (direction * volume).cumsum().fillna(0.0)
        typical_price = (high + low + close) / 3
        out["vwap"] = (typical_price * volume).cumsum() / volume.cumsum().replace(0, np.nan)
        out["vwap"] = out["vwap"].fillna(close)

        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

        atr_for_adx = out["atr"].replace(0, np.nan)
        plus_di = (100 * (plus_dm.rolling(window=14, min_periods=1).sum() / atr_for_adx)).fillna(0.0)
        minus_di = (100 * (minus_dm.rolling(window=14, min_periods=1).sum() / atr_for_adx)).fillna(0.0)
        dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)).fillna(0.0)

        out["adx"] = dx.rolling(window=14, min_periods=1).mean().fillna(25.0)
        out["adx_pos"] = plus_di
        out["adx_neg"] = minus_di

        return out
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators for the given OHLCV dataframe
        
        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
        
        Returns:
            DataFrame with all indicator columns added
        """
        if df.empty or len(df) < 30:
            raise InvalidIndicatorError("Insufficient data for indicator calculation")

        if not TALIB_AVAILABLE:
            print("[WARNING] TA-Lib not installed. Using pandas fallback indicators")
            return self._calculate_all_indicators_fallback(df)
        
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
