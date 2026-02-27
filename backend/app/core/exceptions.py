"""Custom exceptions for the application"""


class StockinatorException(Exception):
    """Base exception for Stockinator"""
    pass


class DatabaseError(StockinatorException):
    """Database operation failed"""
    pass


class BrokerAPIError(StockinatorException):
    """Broker API call failed"""
    pass


class InsufficientFundsError(StockinatorException):
    """Not enough funds for trade"""
    pass


class RiskLimitExceededError(StockinatorException):
    """Trade would exceed risk limits"""
    pass


class ModelNotFoundError(StockinatorException):
    """ML model not loaded"""
    pass


class InvalidIndicatorError(StockinatorException):
    """Indicator calculation failed"""
    pass


class CooldownActiveError(StockinatorException):
    """Trading cooldown period still active"""
    pass
