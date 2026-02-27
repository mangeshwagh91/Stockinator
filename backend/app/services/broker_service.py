"""Broker service for executing trades via various broker APIs"""
from typing import Optional, Dict
from datetime import datetime
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
import ccxt

from app.core.config import settings
from app.core.exceptions import BrokerAPIError, InsufficientFundsError


class BrokerService:
    """Service for interacting with broker APIs"""
    
    def __init__(self):
        self.alpaca_client = None
        self.ccxt_exchange = None
        self.is_paper = settings.PAPER_TRADING
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize broker clients"""
        # Alpaca for stocks
        if settings.ALPACA_API_KEY and settings.ALPACA_SECRET_KEY:
            self.alpaca_client = TradingClient(
                api_key=settings.ALPACA_API_KEY,
                secret_key=settings.ALPACA_SECRET_KEY,
                paper=self.is_paper
            )
        
        # CCXT for crypto
        self.ccxt_exchange = ccxt.binance({
            'enableRateLimit': True,
        })
    
    def place_order(
        self,
        symbol: str,
        side: str,  # 'BUY' or 'SELL'
        quantity: float,
        order_type: str = "market",  # 'market' or 'limit'
        limit_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        asset_type: str = "stock"
    ) -> Dict:
        """
        Place an order with the broker
        
        Args:
            symbol: Trading symbol
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            order_type: 'market' or 'limit'
            limit_price: Limit price for limit orders
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            asset_type: 'stock' or 'crypto'
        
        Returns:
            Dictionary with order details
        """
        try:
            if asset_type == "stock":
                return self._place_alpaca_order(
                    symbol, side, quantity, order_type, limit_price, stop_loss, take_profit
                )
            elif asset_type == "crypto":
                return self._place_crypto_order(
                    symbol, side, quantity, order_type, limit_price
                )
            else:
                raise BrokerAPIError(f"Unknown asset type: {asset_type}")
        except Exception as e:
            raise BrokerAPIError(f"Failed to place order: {str(e)}")
    
    def _place_alpaca_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str,
        limit_price: Optional[float],
        stop_loss: Optional[float],
        take_profit: Optional[float]
    ) -> Dict:
        """Place order with Alpaca"""
        if not self.alpaca_client:
            raise BrokerAPIError("Alpaca client not initialized")
        
        order_side = OrderSide.BUY if side == "BUY" else OrderSide.SELL
        
        if order_type == "market":
            request = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
        else:
            request = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price
            )
        
        order = self.alpaca_client.submit_order(request)
        
        # Place bracket orders for stop loss and take profit if provided
        if stop_loss or take_profit:
            # Note: Alpaca bracket orders would be implemented here
            pass
        
        return {
            "broker_order_id": order.id,
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": float(order.qty),
            "status": order.status.value,
            "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
            "filled_price": float(order.filled_avg_price) if order.filled_avg_price else None,
            "created_at": order.created_at
        }
    
    def _place_crypto_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str,
        limit_price: Optional[float]
    ) -> Dict:
        """Place order with CCXT (crypto)"""
        side_lower = side.lower()
        
        if order_type == "market":
            order = self.ccxt_exchange.create_market_order(
                symbol, side_lower, quantity
            )
        else:
            order = self.ccxt_exchange.create_limit_order(
                symbol, side_lower, quantity, limit_price
            )
        
        return {
            "broker_order_id": order['id'],
            "symbol": order['symbol'],
            "side": side,
            "quantity": order['amount'],
            "status": order['status'],
            "filled_qty": order.get('filled', 0),
            "filled_price": order.get('average'),
            "created_at": datetime.now()
        }
    
    def get_order_status(self, order_id: str, asset_type: str = "stock") -> Dict:
        """
        Get status of an order
        
        Args:
            order_id: Broker order ID
            asset_type: 'stock' or 'crypto'
        
        Returns:
            Order status information
        """
        try:
            if asset_type == "stock" and self.alpaca_client:
                order = self.alpaca_client.get_order_by_id(order_id)
                return {
                    "order_id": order.id,
                    "status": order.status.value,
                    "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                    "filled_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                }
            elif asset_type == "crypto":
                order = self.ccxt_exchange.fetch_order(order_id)
                return {
                    "order_id": order['id'],
                    "status": order['status'],
                    "filled_qty": order.get('filled', 0),
                    "filled_price": order.get('average'),
                }
        except Exception as e:
            raise BrokerAPIError(f"Failed to get order status: {str(e)}")
    
    def cancel_order(self, order_id: str, asset_type: str = "stock") -> bool:
        """
        Cancel an order
        
        Args:
            order_id: Broker order ID
            asset_type: 'stock' or 'crypto'
        
        Returns:
            True if cancelled successfully
        """
        try:
            if asset_type == "stock" and self.alpaca_client:
                self.alpaca_client.cancel_order_by_id(order_id)
                return True
            elif asset_type == "crypto":
                self.ccxt_exchange.cancel_order(order_id)
                return True
            return False
        except Exception as e:
            raise BrokerAPIError(f"Failed to cancel order: {str(e)}")
    
    def get_account(self, asset_type: str = "stock") -> Dict:
        """
        Get account information
        
        Args:
            asset_type: 'stock' or 'crypto'
        
        Returns:
            Account information
        """
        try:
            if asset_type == "stock" and self.alpaca_client:
                account = self.alpaca_client.get_account()
                return {
                    "equity": float(account.equity),
                    "cash": float(account.cash),
                    "buying_power": float(account.buying_power),
                    "portfolio_value": float(account.portfolio_value),
                }
            elif asset_type == "crypto":
                balance = self.ccxt_exchange.fetch_balance()
                return {
                    "equity": balance.get('total', {}).get('USDT', 0),
                    "cash": balance.get('free', {}).get('USDT', 0),
                }
            return {}
        except Exception as e:
            raise BrokerAPIError(f"Failed to get account info: {str(e)}")
    
    def get_positions(self, asset_type: str = "stock") -> list:
        """
        Get open positions
        
        Args:
            asset_type: 'stock' or 'crypto'
        
        Returns:
            List of positions
        """
        try:
            if asset_type == "stock" and self.alpaca_client:
                positions = self.alpaca_client.get_all_positions()
                return [
                    {
                        "symbol": pos.symbol,
                        "qty": float(pos.qty),
                        "avg_entry_price": float(pos.avg_entry_price),
                        "current_price": float(pos.current_price),
                        "unrealized_pl": float(pos.unrealized_pl),
                        "unrealized_plpc": float(pos.unrealized_plpc)
                    }
                    for pos in positions
                ]
            return []
        except Exception as e:
            raise BrokerAPIError(f"Failed to get positions: {str(e)}")


# Global instance
broker_service = BrokerService()
