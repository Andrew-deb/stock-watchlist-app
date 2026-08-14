"""
Enhanced Client for the Massive (Polygon.io) API with richer endpoints.

New features:
- Historical price data (charts)
- Company details and fundamentals
- Real-time snapshots
- Market news
- Market movers (gainers/losers)
- Technical indicators
- Rate limiting and caching
"""

import base64
import os
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

import requests
from databricks.sdk import WorkspaceClient

_w = WorkspaceClient()

_SCOPE = os.environ.get("MASSIVE_SECRET_SCOPE", "massive")
_KEY = os.environ.get("MASSIVE_SECRET_KEY", "api-key")
_BASE_URL = os.environ.get("MASSIVE_API_BASE_URL", "https://api.polygon.io")

_DEFAULT_TIMEOUT = 30


def _get_api_key() -> str:
    """Fetch and decode the Massive API key from the Databricks secret scope."""
    secret = _w.secrets.get_secret(scope=_SCOPE, key=_KEY)
    return base64.b64decode(secret.value).decode("utf-8")


def rate_limit(calls_per_minute=5):
    """Decorator to rate-limit API calls."""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator


class MassiveClient:
    """Enhanced wrapper around the Polygon.io API with rich stock market data."""

    def __init__(self, base_url: str | None = None, timeout: int = _DEFAULT_TIMEOUT):
        self.base_url = (base_url or _BASE_URL).rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {_get_api_key()}",
                "Content-Type": "application/json",
            }
        )
        # Simple in-memory cache for frequent data
        self._cache = {}

    def _get_from_cache(self, key: str, ttl_seconds: int = 300) -> Any | None:
        """Get data from cache if not expired."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=ttl_seconds):
                return data
        return None

    def _set_cache(self, key: str, data: Any) -> None:
        """Store data in cache with timestamp."""
        self._cache[key] = (data, datetime.now())

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make a GET request with error handling."""
        resp = self._session.get(f"{self.base_url}{path}", params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make a POST request with error handling."""
        resp = self._session.post(f"{self.base_url}{path}", json=json, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ========== PHASE 1: CORE DATA ENRICHMENT ==========

    def get_latest_price(self, symbol: str) -> dict:
        """
        Fetch the latest traded price for a single symbol (previous day's close).
        This is the original method - kept for backward compatibility.
        """
        data = self.get(f"/v2/aggs/ticker/{symbol}/prev")
        return data

    def get_historical_data(self, symbol: str, timespan: str = "day", days_back: int = 30) -> dict:
        """
        Fetch historical aggregate bars for a stock.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            timespan: 'day', 'week', 'month', 'quarter', 'year'
            days_back: Number of days to look back (default: 30)
            
        Returns:
            Dict with 'results' array containing OHLCV data:
            [{'t': timestamp_ms, 'o': open, 'h': high, 'l': low, 'c': close, 'v': volume}, ...]
        """
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        cache_key = f"hist_{symbol}_{timespan}_{days_back}"
        cached = self._get_from_cache(cache_key, ttl_seconds=3600)  # 1 hour cache
        if cached:
            return cached
        
        data = self.get(f"/v2/aggs/ticker/{symbol}/range/1/{timespan}/{from_date}/{to_date}")
        self._set_cache(cache_key, data)
        return data

    def get_company_details(self, symbol: str) -> dict:
        """
        Fetch comprehensive company information.
        
        Returns:
            Dict with company details: name, description, logo, market_cap, sector, 
            industry, homepage_url, total_employees, etc.
        """
        cache_key = f"company_{symbol}"
        cached = self._get_from_cache(cache_key, ttl_seconds=86400)  # 24 hour cache
        if cached:
            return cached
        
        data = self.get(f"/v3/reference/tickers/{symbol}")
        self._set_cache(cache_key, data)
        return data

    def get_snapshot(self, symbol: str) -> dict:
        """
        Get current snapshot with today's trading data (real-time or 15-min delayed).
        
        Returns:
            Dict with current price, day's high/low, volume, bid/ask, etc.
        """
        data = self.get(f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}")
        return data

    # ========== PHASE 2: MARKET INTELLIGENCE ==========

    def get_stock_news(self, symbol: str = None, limit: int = 10) -> dict:
        """
        Fetch recent news articles.
        
        Args:
            symbol: Optional ticker symbol to filter news. If None, returns general market news.
            limit: Number of articles to return (default: 10, max: 50)
            
        Returns:
            Dict with 'results' array of news articles with title, description, url, image, etc.
        """
        params = {
            "limit": min(limit, 50),
            "order": "desc"
        }
        if symbol:
            params["ticker"] = symbol
        
        data = self.get("/v2/reference/news", params=params)
        return data

    def get_market_gainers(self, limit: int = 20) -> dict:
        """
        Get top gaining stocks today.
        
        Returns:
            Dict with 'tickers' array of top gainers with price, change %, etc.
        """
        cache_key = f"gainers_{limit}"
        cached = self._get_from_cache(cache_key, ttl_seconds=300)  # 5 min cache
        if cached:
            return cached
        
        data = self.get("/v2/snapshot/locale/us/markets/stocks/gainers")
        self._set_cache(cache_key, data)
        return data

    def get_market_losers(self, limit: int = 20) -> dict:
        """
        Get top losing stocks today.
        
        Returns:
            Dict with 'tickers' array of top losers with price, change %, etc.
        """
        cache_key = f"losers_{limit}"
        cached = self._get_from_cache(cache_key, ttl_seconds=300)  # 5 min cache
        if cached:
            return cached
        
        data = self.get("/v2/snapshot/locale/us/markets/stocks/losers")
        self._set_cache(cache_key, data)
        return data

    # ========== PHASE 3: TECHNICAL INDICATORS ==========

    def get_sma(self, symbol: str, window: int = 50, timespan: str = "day", series_type: str = "close") -> dict:
        """
        Get Simple Moving Average (SMA) for a stock.
        
        Args:
            symbol: Stock ticker
            window: Number of periods for SMA (default: 50)
            timespan: 'day', 'week', 'month'
            series_type: 'close', 'open', 'high', 'low'
            
        Returns:
            Dict with SMA values over time
        """
        params = {
            "timespan": timespan,
            "adjusted": "true",
            "window": window,
            "series_type": series_type,
            "order": "desc"
        }
        data = self.get(f"/v1/indicators/sma/{symbol}", params=params)
        return data

    def get_ema(self, symbol: str, window: int = 20, timespan: str = "day", series_type: str = "close") -> dict:
        """
        Get Exponential Moving Average (EMA) for a stock.
        
        Args:
            symbol: Stock ticker
            window: Number of periods for EMA (default: 20)
            timespan: 'day', 'week', 'month'
            series_type: 'close', 'open', 'high', 'low'
            
        Returns:
            Dict with EMA values over time
        """
        params = {
            "timespan": timespan,
            "adjusted": "true",
            "window": window,
            "series_type": series_type,
            "order": "desc"
        }
        data = self.get(f"/v1/indicators/ema/{symbol}", params=params)
        return data

    def get_rsi(self, symbol: str, window: int = 14, timespan: str = "day", series_type: str = "close") -> dict:
        """
        Get Relative Strength Index (RSI) for a stock.
        
        Args:
            symbol: Stock ticker
            window: Number of periods for RSI (default: 14)
            timespan: 'day', 'week', 'month'
            series_type: 'close', 'open', 'high', 'low'
            
        Returns:
            Dict with RSI values (0-100, <30 = oversold, >70 = overbought)
        """
        params = {
            "timespan": timespan,
            "adjusted": "true",
            "window": window,
            "series_type": series_type,
            "order": "desc"
        }
        data = self.get(f"/v1/indicators/rsi/{symbol}", params=params)
        return data

    def get_macd(self, symbol: str, timespan: str = "day", 
                 short_window: int = 12, long_window: int = 26, signal_window: int = 9) -> dict:
        """
        Get MACD (Moving Average Convergence Divergence) for a stock.
        
        Args:
            symbol: Stock ticker
            timespan: 'day', 'week', 'month'
            short_window: Short EMA period (default: 12)
            long_window: Long EMA period (default: 26)
            signal_window: Signal line period (default: 9)
            
        Returns:
            Dict with MACD values, signal line, and histogram
        """
        params = {
            "timespan": timespan,
            "adjusted": "true",
            "short_window": short_window,
            "long_window": long_window,
            "signal_window": signal_window,
            "series_type": "close",
            "order": "desc"
        }
        data = self.get(f"/v1/indicators/macd/{symbol}", params=params)
        return data

    # ========== BATCH & UTILITY METHODS ==========

    def get_multiple_snapshots(self, symbols: list[str]) -> dict:
        """
        Fetch snapshots for multiple symbols in one request (if API supports).
        Note: Polygon.io free tier may not support this - falls back to individual calls.
        
        Args:
            symbols: List of ticker symbols
            
        Returns:
            Dict with snapshots for all requested symbols
        """
        try:
            # Try batch endpoint first
            params = {"tickers": ",".join(symbols)}
            data = self.get("/v2/snapshot/locale/us/markets/stocks/tickers", params=params)
            return data
        except requests.HTTPError:
            # Fall back to individual requests if batch not supported
            results = {}
            for symbol in symbols:
                try:
                    results[symbol] = self.get_snapshot(symbol)
                except Exception as e:
                    results[symbol] = {"error": str(e)}
            return {"tickers": results}

    def paginated_get(self, path: str, params: dict[str, Any] | None = None, page_size: int = 200):
        """
        Generator that yields items across all pages of a paginated dataset.
        Assumes a cursor-based API shape: {"results": [...], "next_url": "..." | null}
        """
        cursor = None
        params = dict(params or {})
        params["limit"] = page_size

        while True:
            if cursor:
                params["cursor"] = cursor
            data = self.get(path, params=params)
            items = data.get("results", [])
            for item in items:
                yield item

            # Check for next page
            next_url = data.get("next_url")
            if not next_url:
                break
            
            # Extract cursor from next_url if present
            if "cursor=" in next_url:
                cursor = next_url.split("cursor=")[1].split("&")[0]
            else:
                break
