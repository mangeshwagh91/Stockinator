"""Example test file"""
import pytest
from app.services.indicator_service import indicator_service
import pandas as pd
import numpy as np


def test_indicator_calculation():
    """Test basic indicator calculation"""
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    data = {
        'open': np.random.uniform(100, 110, 100),
        'high': np.random.uniform(110, 120, 100),
        'low': np.random.uniform(90, 100, 100),
        'close': np.random.uniform(100, 110, 100),
        'volume': np.random.uniform(1000, 10000, 100)
    }
    df = pd.DataFrame(data, index=dates)
    
    # Calculate indicators
    df_with_indicators = indicator_service.calculate_all_indicators(df)
    
    # Verify indicators were calculated
    assert 'rsi' in df_with_indicators.columns
    assert 'macd' in df_with_indicators.columns
    assert 'sma_20' in df_with_indicators.columns
    assert 'adx' in df_with_indicators.columns
    
    # Check that we have some non-NaN values
    assert df_with_indicators['rsi'].notna().sum() > 0
    assert df_with_indicators['macd'].notna().sum() > 0


def test_feature_extraction():
    """Test feature extraction for ML"""
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    data = {
        'open': np.random.uniform(100, 110, 100),
        'high': np.random.uniform(110, 120, 100),
        'low': np.random.uniform(90, 100, 100),
        'close': np.random.uniform(100, 110, 100),
        'volume': np.random.uniform(1000, 10000, 100)
    }
    df = pd.DataFrame(data, index=dates)
    
    df_with_indicators = indicator_service.calculate_all_indicators(df)
    features = indicator_service.extract_latest_features(df_with_indicators)
    
    # Check that features is a dictionary
    assert isinstance(features, dict)
    
    # Check that expected features are present
    expected_features = ['rsi', 'macd', 'adx', 'sma_20', 'sma_50']
    for feature in expected_features:
        assert feature in features
    
    # Check that values are floats
    for value in features.values():
        assert isinstance(value, float)
