"""Market data service for fetching and storing market data"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import ccxt
import yfinance as yf
import requests
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from app.core.config import settings
from app.core.database import influx_db, redis_manager
from app.core.mongodb import mongodb_manager
from app.core.exceptions import DatabaseError


class MarketDataService:
    """Service for handling market data operations"""
    
    def __init__(self):
        self.alpaca_client = None
        self.ccxt_exchange = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize broker clients"""
        # Initialize Alpaca for US stocks
        if settings.ALPACA_API_KEY and settings.ALPACA_SECRET_KEY:
            self.alpaca_client = StockHistoricalDataClient(
                api_key=settings.ALPACA_API_KEY,
                secret_key=settings.ALPACA_SECRET_KEY
            )
        
        # Initialize CCXT for crypto
        self.ccxt_exchange = ccxt.binance()  # Can be configured
    
    def _is_indian_stock(self, symbol: str) -> bool:
        """Check if symbol is an Indian stock"""
        normalized = symbol.upper().strip()
        indian_indices = {
            "NIFTY",
            "NIFTY50",
            "NIFTYBANK",
            "BANKNIFTY",
            "FINNIFTY",
            "SENSEX",
            "BANKEX",
            "MIDCPNIFTY",
        }

        if normalized.endswith('.NS') or normalized.endswith('.BO'):
            return True

        if normalized in indian_indices:
            return True

        # India-first default for plain cash-equity style symbols.
        return '.' not in normalized and '/' not in normalized and ':' not in normalized

    def _has_real_itick_key(self) -> bool:
        """Return true only when iTick key appears to be a configured non-placeholder value."""
        return bool(settings.ITICK_API_KEY and not settings.ITICK_API_KEY.lower().startswith("your-"))

    def _normalize_indian_symbol(self, symbol: str) -> str:
        """Normalize Indian stock symbols to Yahoo-compatible NSE format when suffix is missing."""
        alias_map = {
            "NIFTY": "^NSEI",
            "NIFTY50": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "SENSEX": "^BSESN",
            "USDINR": "INR=X",
        }

        upper_symbol = symbol.upper().strip()
        if upper_symbol in alias_map:
            return alias_map[upper_symbol]

        if symbol.endswith('.NS') or symbol.endswith('.BO'):
            return symbol

        # Default to NSE for plain symbols in India-first setup.
        if '.' not in symbol:
            return f"{symbol}.NS"

        return symbol
    
    def fetch_historical_data(
        self,
        symbol: str,
        interval: str = "1m",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
        asset_type: str = "stock"
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data
        
        Args:
            symbol: Trading symbol
            interval: Time interval (1m, 5m, 15m, 1h, 1d)
            start_time: Start datetime
            end_time: End datetime
            limit: Maximum number of candles
            asset_type: 'stock' or 'crypto'
        
        Returns:
            DataFrame with OHLCV data
        """
        if asset_type == "stock":
            return self._fetch_stock_data(symbol, interval, start_time, end_time)
        elif asset_type == "crypto":
            return self._fetch_crypto_data(symbol, interval, start_time, end_time, limit)
        else:
            raise ValueError(f"Unknown asset type: {asset_type}")

    def _build_mongo_symbol_candidates(self, symbol: str) -> List[str]:
        """Build symbol aliases that may exist in historical Mongo collections."""
        clean = symbol.strip()
        upper_symbol = clean.upper()
        normalized = self._normalize_indian_symbol(upper_symbol)

        candidates: List[str] = [clean, upper_symbol, normalized]

        if normalized.endswith(".NS"):
            candidates.append(normalized[:-3])
        if normalized.endswith(".BO"):
            candidates.append(normalized[:-3])

        if upper_symbol in {"NIFTY", "NIFTY50"}:
            candidates.extend(["^NSEI"])
        if upper_symbol == "BANKNIFTY":
            candidates.extend(["^NSEBANK", "NIFTYBANK"])
        if upper_symbol == "SENSEX":
            candidates.extend(["^BSESN"])

        # Preserve order while removing duplicates.
        return list(dict.fromkeys(candidates))

    def _fetch_mongo_historical_data(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLCV history from MongoDB if present; return None when unavailable."""
        try:
            collection = mongodb_manager.get_collection("market_data")
            symbol_candidates = self._build_mongo_symbol_candidates(symbol)

            query = {
                "symbol": {"$in": symbol_candidates},
                "interval": interval,
            }

            if start_time or end_time:
                query["timestamp"] = {}
                if start_time:
                    query["timestamp"]["$gte"] = start_time
                if end_time:
                    query["timestamp"]["$lte"] = end_time

            cursor = collection.find(query).sort("timestamp", 1)
            records = list(cursor)

            if not records:
                return None

            df = pd.DataFrame(records)
            if df.empty:
                return None

            if "_id" in df.columns:
                df = df.drop(columns=["_id"])

            # Handle older dumps that used uppercase OHLCV keys.
            df.columns = [c.lower() for c in df.columns]
            if "date" in df.columns and "timestamp" not in df.columns:
                df = df.rename(columns={"date": "timestamp"})

            required_cols = ["open", "high", "low", "close", "volume"]
            if "timestamp" not in df.columns or not all(col in df.columns for col in required_cols):
                return None

            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.dropna(subset=["timestamp"])
            if df.empty:
                return None

            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.dropna(subset=required_cols)
            if df.empty:
                return None

            df = df.sort_values("timestamp").set_index("timestamp")
            return df[required_cols]
        except Exception:
            return None
    
    def _fetch_stock_data(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> pd.DataFrame:
        """Fetch stock data from appropriate source (Alpaca/Yahoo/iTick)"""
        mongo_df = self._fetch_mongo_historical_data(symbol, interval, start_time, end_time)
        if mongo_df is not None and not mongo_df.empty:
            return mongo_df

        # Check if it's an Indian stock
        if self._is_indian_stock(symbol):
            normalized_symbol = self._normalize_indian_symbol(symbol)

            # Use iTick first whenever configured for Indian-market historical candles.
            if self._has_real_itick_key():
                try:
                    return self._fetch_itick_data(normalized_symbol, interval, start_time, end_time)
                except Exception:
                    # Fall back to Yahoo if iTick call fails for any reason.
                    pass

            return self._fetch_yfinance_data(normalized_symbol, interval, start_time, end_time)
        
        # For US stocks, use Alpaca
        return self._fetch_alpaca_data(symbol, interval, start_time, end_time)
    
    def _fetch_alpaca_data(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> pd.DataFrame:
        """Fetch stock data from Alpaca (US stocks)"""
        if not self.alpaca_client:
            raise DatabaseError("Alpaca client not initialized")
        
        # Map interval to Alpaca TimeFrame
        timeframe_map = {
            "1m": TimeFrame.Minute,
            "5m": TimeFrame(5, "Min"),
            "15m": TimeFrame(15, "Min"),
            "1h": TimeFrame.Hour,
            "1d": TimeFrame.Day
        }
        
        timeframe = timeframe_map.get(interval, TimeFrame.Minute)
        
        # Default time range if not provided
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(days=7)
        
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=start_time,
            end=end_time
        )
        
        bars = self.alpaca_client.get_stock_bars(request_params)
        
        # Convert to DataFrame
        df = bars.df
        if symbol in df.index.get_level_values(0):
            df = df.loc[symbol]
        
        return df
    
    def _fetch_yfinance_data(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> pd.DataFrame:
        """Fetch stock data from Yahoo Finance (for Indian stocks)"""
        # Map interval to yfinance format
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "1h": "1h",
            "1d": "1d"
        }
        
        yf_interval = interval_map.get(interval, "1m")
        
        # Default time range if not provided
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            # yfinance has limits on intraday data (7 days for 1m, 60 days for others)
            if interval in ["1m", "5m"]:
                start_time = end_time - timedelta(days=7)
            else:
                start_time = end_time - timedelta(days=60)
        
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            df = ticker.history(
                start=start_time,
                end=end_time,
                interval=yf_interval
            )
            
            if df.empty:
                raise DatabaseError(f"No data found for {symbol}")
            
            # Rename columns to match our standard format (lowercase)
            df.columns = df.columns.str.lower()
            
            # Ensure we have the required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                raise DatabaseError(f"Missing required columns in Yahoo Finance data")
            
            return df[required_cols]
            
        except Exception as e:
            raise DatabaseError(f"Error fetching Yahoo Finance data for {symbol}: {str(e)}")
    
    def _fetch_itick_data(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> pd.DataFrame:
        """Fetch historical Indian stock data from iTick"""
        # Remove .NS or .BO suffix if present
        clean_symbol = symbol.replace('.NS', '').replace('.BO', '')
        
        # Map interval to iTick format
        interval_map = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "1h": "60",
            "1d": "D"
        }
        
        itick_interval = interval_map.get(interval, "D")
        
        # Default time range if not provided
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(days=365)
        
        try:
            # iTick API configuration
            base_url = settings.ITICK_API_URL or "https://api.itick.in/api/v1"
            api_key = settings.ITICK_API_KEY
            
            if not self._has_real_itick_key():
                raise DatabaseError("iTick API key not configured")
            
            # Format dates for iTick API
            from_date = start_time.strftime("%Y-%m-%d")
            to_date = end_time.strftime("%Y-%m-%d")
            
            # Make API request to iTick
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "symbol": clean_symbol,
                "interval": itick_interval,
                "from_date": from_date,
                "to_date": to_date
            }
            
            response = requests.get(
                f"{base_url}/historical",
                headers=headers,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data or 'data' not in data:
                raise DatabaseError(f"No data found for {symbol} from iTick")
            
            # Convert to DataFrame
            df = pd.DataFrame(data['data'])
            
            # Standardize column names
            column_mapping = {
                'time': 'timestamp',
                'date': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }
            
            df.rename(columns=column_mapping, inplace=True)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Ensure we have the required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                raise DatabaseError(f"Missing required columns in iTick data")
            
            return df[required_cols]
            
        except requests.exceptions.RequestException as e:
            # If iTick fails, fall back to yfinance
            print(f"iTick API error: {e}. Falling back to Yahoo Finance...")
            return self._fetch_yfinance_data(symbol, interval, start_time, end_time)
        except Exception as e:
            raise DatabaseError(f"Error fetching iTick data for {symbol}: {str(e)}")
    
    def _fetch_crypto_data(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        limit: int
    ) -> pd.DataFrame:
        """Fetch crypto data from CCXT"""
        # Map interval to CCXT format
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "1h": "1h",
            "1d": "1d"
        }
        
        ccxt_interval = interval_map.get(interval, "1m")
        
        # Fetch OHLCV data
        if start_time:
            since = int(start_time.timestamp() * 1000)
            ohlcv = self.ccxt_exchange.fetch_ohlcv(
                symbol, ccxt_interval, since=since, limit=limit
            )
        else:
            ohlcv = self.ccxt_exchange.fetch_ohlcv(
                symbol, ccxt_interval, limit=limit
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(
            ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def store_to_influxdb(
        self,
        symbol: str,
        interval: str,
        df: pd.DataFrame
    ):
        """
        Store OHLCV data to InfluxDB
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            df: DataFrame with OHLCV data
        """
        for timestamp, row in df.iterrows():
            tags = {
                "symbol": symbol,
                "interval": interval
            }
            
            fields = {
                "open": float(row.get('open', 0)),
                "high": float(row.get('high', 0)),
                "low": float(row.get('low', 0)),
                "close": float(row.get('close', 0)),
                "volume": float(row.get('volume', 0))
            }
            
            influx_db.write_point(
                measurement="market_data",
                tags=tags,
                fields=fields,
                timestamp=timestamp
            )
    
    def publish_to_redis(
        self,
        symbol: str,
        interval: str,
        data: dict
    ):
        """
        Publish new market data to Redis for Celery workers
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            data: Dictionary with OHLCV data
        """
        import json
        
        channel = f"market:{symbol}:{interval}"
        message = json.dumps(data)
        redis_manager.publish(channel, message)
    
    def get_latest_price(self, symbol: str, asset_type: str = "stock") -> float:
        """
        Get the latest price for a symbol
        
        Args:
            symbol: Trading symbol
            asset_type: 'stock' or 'crypto'
        
        Returns:
            Latest price
        """
        # Crypto: use exchange ticker directly for latest trade price.
        if asset_type == "crypto":
            try:
                ticker = self.ccxt_exchange.fetch_ticker(symbol)
                if ticker and ticker.get("last") is not None:
                    return float(ticker["last"])
            except Exception:
                pass

        # For Indian stocks, use iTick first (if configured), then Yahoo fast info.
        if asset_type == "stock" and self._is_indian_stock(symbol):
            if self._has_real_itick_key():
                try:
                    quote_df = self._fetch_itick_data(symbol, interval="1m", start_time=datetime.now() - timedelta(days=1), end_time=datetime.now())
                    if not quote_df.empty:
                        itick_price = float(quote_df["close"].iloc[-1])
                        if itick_price > 0:
                            return itick_price
                except Exception:
                    pass

            try:
                normalized_symbol = self._normalize_indian_symbol(symbol)
                ticker = yf.Ticker(normalized_symbol)
                info = ticker.fast_info
                yf_price = float(info.get('last_price', info.get('previous_close', 0)))
                if yf_price > 0:
                    return yf_price
            except:
                # Fallback to historical data
                pass
        
        df = self.fetch_historical_data(
            symbol=symbol,
            interval="1m",
            limit=1,
            asset_type=asset_type
        )
        
        if df.empty:
            raise DatabaseError(f"No data found for {symbol}")
        
        return float(df['close'].iloc[-1])


# Global instance
market_data_service = MarketDataService()
