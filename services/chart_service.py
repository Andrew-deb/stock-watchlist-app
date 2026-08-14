"""Chart Service - Handles chart data preparation and formatting.

Single Responsibility: Chart data retrieval and formatting for UI consumption.
This service focuses on preparing historical and indicator data for chart visualizations.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from massive_client import MassiveClient

logger = logging.getLogger(__name__)


class ChartService:
    """Service for chart data operations and formatting."""
    
    def __init__(self):
        """Initialize with an enhanced Massive API client."""
        self.client = MassiveClient()
    
    def get_historical_chart_data(self, symbol: str, timespan: str = "day", days_back: int = 30) -> Dict[str, Any]:
        """Get historical price data formatted for chart display.
        
        Args:
            symbol: Stock ticker symbol
            timespan: Time period ('day', 'week', 'month')
            days_back: Number of days to look back (default: 30)
            
        Returns:
            Dict containing formatted chart data with labels and values
        """
        try:
            logger.info(f"Fetching historical chart data for {symbol} ({timespan}, {days_back} days)")
            data = self.client.get_historical_data(symbol, timespan=timespan, days_back=days_back)
            return self._format_historical_for_chart(data, symbol)
        except Exception as e:
            logger.error(f"Error fetching historical chart data for {symbol}: {e}")
            raise
    
    def get_technical_indicators(self, symbol: str, indicator_type: str = "sma", 
                                window: int = 50, timespan: str = "day") -> Dict[str, Any]:
        """Get technical indicator data formatted for chart overlay.
        
        Args:
            symbol: Stock ticker symbol
            indicator_type: Type of indicator ('sma', 'ema', 'rsi', 'macd')
            window: Window size for the indicator
            timespan: Time period ('day', 'week', 'month')
            
        Returns:
            Dict containing formatted indicator data
        """
        try:
            logger.info(f"Fetching {indicator_type.upper()} for {symbol} (window: {window})")
            
            if indicator_type.lower() == "sma":
                data = self.client.get_sma(symbol, window=window, timespan=timespan)
            elif indicator_type.lower() == "ema":
                data = self.client.get_ema(symbol, window=window, timespan=timespan)
            elif indicator_type.lower() == "rsi":
                data = self.client.get_rsi(symbol, window=window, timespan=timespan)
            elif indicator_type.lower() == "macd":
                data = self.client.get_macd(symbol, timespan=timespan)
            else:
                raise ValueError(f"Unsupported indicator type: {indicator_type}")
            
            return self._format_indicator_for_chart(data, indicator_type)
        except Exception as e:
            logger.error(f"Error fetching {indicator_type} for {symbol}: {e}")
            raise
    
    def get_multi_timeframe_data(self, symbol: str) -> Dict[str, Any]:
        """Get historical data across multiple timeframes for comparison.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dict containing chart data for 7 days, 30 days, 90 days, and 1 year
        """
        try:
            logger.info(f"Fetching multi-timeframe data for {symbol}")
            
            return {
                "symbol": symbol,
                "timeframes": {
                    "7d": self.get_historical_chart_data(symbol, "day", 7),
                    "30d": self.get_historical_chart_data(symbol, "day", 30),
                    "90d": self.get_historical_chart_data(symbol, "day", 90),
                    "1y": self.get_historical_chart_data(symbol, "day", 365)
                }
            }
        except Exception as e:
            logger.error(f"Error fetching multi-timeframe data for {symbol}: {e}")
            raise
    
    # ========== PRIVATE FORMATTING METHODS ==========
    
    def _format_historical_for_chart(self, data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Format historical price data into Chart.js compatible structure.
        
        Returns:
            Dict with 'labels' (dates) and 'datasets' (price series)
        """
        results = data.get("results", [])
        
        if not results:
            return {
                "symbol": symbol,
                "labels": [],
                "datasets": [],
                "error": "No historical data available"
            }
        
        # Extract and format data points
        labels = []
        prices = []
        volumes = []
        
        for bar in results:
            # Convert timestamp from milliseconds to date string
            timestamp = bar.get("t")
            if timestamp:
                date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
                labels.append(date)
            
            # Extract OHLCV data
            prices.append({
                "date": labels[-1] if labels else None,
                "open": bar.get("o"),
                "high": bar.get("h"),
                "low": bar.get("l"),
                "close": bar.get("c"),
                "volume": bar.get("v")
            })
            volumes.append(bar.get("v"))
        
        # Create Chart.js compatible datasets
        return {
            "symbol": symbol,
            "labels": labels,
            "datasets": [
                {
                    "label": f"{symbol} Price",
                    "data": [p["close"] for p in prices],
                    "borderColor": "#667eea",
                    "backgroundColor": "rgba(102, 126, 234, 0.1)",
                    "fill": True,
                    "tension": 0.4
                }
            ],
            "prices": prices,  # Full OHLCV data for advanced charts
            "volumes": volumes,
            "count": len(results)
        }
    
    def _format_indicator_for_chart(self, data: Dict[str, Any], indicator_type: str) -> Dict[str, Any]:
        """Format technical indicator data for chart overlay.
        
        Returns:
            Dict with indicator values and timestamps
        """
        results = data.get("results", {}).get("values", [])
        
        if not results:
            return {
                "indicator": indicator_type,
                "data": [],
                "error": "No indicator data available"
            }
        
        labels = []
        values = []
        
        for point in results:
            timestamp = point.get("timestamp")
            if timestamp:
                date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
                labels.append(date)
            
            values.append(point.get("value"))
        
        return {
            "indicator": indicator_type,
            "labels": labels,
            "values": values,
            "count": len(results)
        }
    
    @staticmethod
    def calculate_price_statistics(prices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic statistics from price data.
        
        Args:
            prices: List of price dictionaries with 'close', 'high', 'low' keys
            
        Returns:
            Dict containing min, max, average, and volatility
        """
        if not prices:
            return {}
        
        closes = [p.get("close") for p in prices if p.get("close") is not None]
        highs = [p.get("high") for p in prices if p.get("high") is not None]
        lows = [p.get("low") for p in prices if p.get("low") is not None]
        
        if not closes:
            return {}
        
        return {
            "min": min(lows) if lows else None,
            "max": max(highs) if highs else None,
            "average": sum(closes) / len(closes),
            "first": closes[0],
            "last": closes[-1],
            "change": closes[-1] - closes[0] if len(closes) > 1 else 0,
            "change_percent": ((closes[-1] - closes[0]) / closes[0] * 100) if len(closes) > 1 and closes[0] != 0 else 0
        }
