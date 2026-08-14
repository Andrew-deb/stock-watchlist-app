"""Stock Service - Handles individual stock operations.

Single Responsibility: Individual stock data retrieval and processing.
This service focuses on operations related to a single stock symbol.
"""

import logging
from typing import Dict, Any, Optional

from massive_client import MassiveClient

logger = logging.getLogger(__name__)


class StockService:
    """Service for individual stock data operations."""
    
    def __init__(self):
        """Initialize with an enhanced Massive API client."""
        self.client = MassiveClient()
    
    def get_latest_price(self, symbol: str) -> Dict[str, Any]:
        """Get the latest price for a stock symbol.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            Dict containing latest price data
            
        Raises:
            Exception: If API call fails
        """
        try:
            logger.info(f"Fetching latest price for {symbol}")
            data = self.client.get_latest_price(symbol)
            return self._format_price_response(data, symbol)
        except Exception as e:
            logger.error(f"Error fetching latest price for {symbol}: {e}")
            raise
    
    def get_company_details(self, symbol: str) -> Dict[str, Any]:
        """Get detailed company information.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dict containing company details (name, description, logo, etc.)
        """
        try:
            logger.info(f"Fetching company details for {symbol}")
            data = self.client.get_company_details(symbol)
            return self._format_company_response(data)
        except Exception as e:
            logger.error(f"Error fetching company details for {symbol}: {e}")
            raise
    
    def get_snapshot(self, symbol: str) -> Dict[str, Any]:
        """Get real-time snapshot with current trading data.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dict containing current price, day's high/low, volume, etc.
        """
        try:
            logger.info(f"Fetching snapshot for {symbol}")
            data = self.client.get_snapshot(symbol)
            return self._format_snapshot_response(data)
        except Exception as e:
            logger.error(f"Error fetching snapshot for {symbol}: {e}")
            raise
    
    def get_multiple_quotes(self, symbols: list[str]) -> Dict[str, Any]:
        """Get quotes for multiple symbols efficiently.
        
        Args:
            symbols: List of stock ticker symbols
            
        Returns:
            Dict mapping symbols to their quote data
        """
        try:
            logger.info(f"Fetching quotes for {len(symbols)} symbols")
            data = self.client.get_multiple_snapshots(symbols)
            return self._format_multiple_quotes(data)
        except Exception as e:
            logger.error(f"Error fetching multiple quotes: {e}")
            raise
    
    # ========== PRIVATE FORMATTING METHODS ==========
    
    def _format_price_response(self, data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Format price data into a consistent structure."""
        if not data.get("results"):
            return {"symbol": symbol, "price": None, "error": "No data available"}
        
        results = data["results"][0] if isinstance(data["results"], list) else data["results"]
        
        return {
            "symbol": symbol,
            "price": results.get("c"),  # close price
            "open": results.get("o"),
            "high": results.get("h"),
            "low": results.get("l"),
            "volume": results.get("v"),
            "timestamp": results.get("t")
        }
    
    def _format_company_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format company data into a clean structure."""
        if not data.get("results"):
            return {"error": "No company data available"}
        
        results = data["results"]
        
        return {
            "symbol": results.get("ticker"),
            "name": results.get("name"),
            "description": results.get("description"),
            "logo_url": results.get("branding", {}).get("logo_url"),
            "icon_url": results.get("branding", {}).get("icon_url"),
            "market_cap": results.get("market_cap"),
            "sector": results.get("sic_description"),
            "industry": results.get("industry"),
            "homepage_url": results.get("homepage_url"),
            "total_employees": results.get("total_employees"),
            "phone_number": results.get("phone_number"),
            "address": {
                "address1": results.get("address", {}).get("address1"),
                "city": results.get("address", {}).get("city"),
                "state": results.get("address", {}).get("state"),
                "postal_code": results.get("address", {}).get("postal_code")
            }
        }
    
    def _format_snapshot_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format snapshot data into a clean structure."""
        if not data.get("ticker"):
            return {"error": "No snapshot data available"}
        
        ticker_data = data.get("ticker", {})
        day_data = ticker_data.get("day", {})
        prev_day_data = ticker_data.get("prevDay", {})
        
        current_price = day_data.get("c") or prev_day_data.get("c")
        prev_close = prev_day_data.get("c")
        
        # Calculate change and change percent
        change = None
        change_percent = None
        if current_price and prev_close:
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100
        
        return {
            "symbol": data.get("ticker"),
            "current_price": current_price,
            "change": change,
            "change_percent": change_percent,
            "day": {
                "open": day_data.get("o"),
                "high": day_data.get("h"),
                "low": day_data.get("l"),
                "close": day_data.get("c"),
                "volume": day_data.get("v")
            },
            "prev_day": {
                "close": prev_close,
                "volume": prev_day_data.get("v")
            },
            "last_trade": ticker_data.get("lastTrade", {}),
            "last_quote": ticker_data.get("lastQuote", {})
        }
    
    def _format_multiple_quotes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format multiple quotes into a clean structure."""
        tickers = data.get("tickers", [])
        if not tickers:
            return {"quotes": {}, "count": 0}
        
        quotes = {}
        for ticker in tickers:
            symbol = ticker.get("ticker")
            if symbol:
                quotes[symbol] = self._format_snapshot_response({"ticker": ticker})
        
        return {
            "quotes": quotes,
            "count": len(quotes)
        }
