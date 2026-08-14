"""Market Service - Handles market-wide operations.

Single Responsibility: Market-wide data, news, and movers.
This service focuses on operations related to the entire market, not individual stocks.
"""

import logging
from typing import Dict, Any, List, Optional

from massive_client_enhanced import MassiveClient

logger = logging.getLogger(__name__)


class MarketService:
    """Service for market-wide data operations."""
    
    def __init__(self):
        """Initialize with an enhanced Massive API client."""
        self.client = MassiveClient()
    
    def get_market_gainers(self, limit: int = 20) -> Dict[str, Any]:
        """Get top gaining stocks in the market.
        
        Args:
            limit: Number of gainers to return (default: 20)
            
        Returns:
            Dict containing list of top gainers with price and change data
        """
        try:
            logger.info(f"Fetching top {limit} market gainers")
            data = self.client.get_market_gainers(limit=limit)
            return self._format_movers_response(data, "gainers")
        except Exception as e:
            logger.error(f"Error fetching market gainers: {e}")
            raise
    
    def get_market_losers(self, limit: int = 20) -> Dict[str, Any]:
        """Get top losing stocks in the market.
        
        Args:
            limit: Number of losers to return (default: 20)
            
        Returns:
            Dict containing list of top losers with price and change data
        """
        try:
            logger.info(f"Fetching top {limit} market losers")
            data = self.client.get_market_losers(limit=limit)
            return self._format_movers_response(data, "losers")
        except Exception as e:
            logger.error(f"Error fetching market losers: {e}")
            raise
    
    def get_market_news(self, symbol: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Get latest market or stock-specific news.
        
        Args:
            symbol: Optional stock symbol to filter news. If None, returns general market news.
            limit: Number of articles to return (default: 10)
            
        Returns:
            Dict containing list of news articles with title, description, url, etc.
        """
        try:
            if symbol:
                logger.info(f"Fetching news for {symbol} (limit: {limit})")
            else:
                logger.info(f"Fetching general market news (limit: {limit})")
            
            data = self.client.get_stock_news(symbol=symbol, limit=limit)
            return self._format_news_response(data)
        except Exception as e:
            logger.error(f"Error fetching market news: {e}")
            raise
    
    def get_market_overview(self) -> Dict[str, Any]:
        """Get a combined market overview with gainers, losers, and news.
        
        Returns:
            Dict containing market summary data
        """
        try:
            logger.info("Fetching market overview")
            
            # Fetch data in parallel (or sequentially with caching)
            gainers = self.get_market_gainers(limit=5)
            losers = self.get_market_losers(limit=5)
            news = self.get_market_news(limit=5)
            
            return {
                "gainers": gainers.get("movers", [])[:5],
                "losers": losers.get("movers", [])[:5],
                "news": news.get("articles", [])[:5],
                "timestamp": self._get_current_timestamp()
            }
        except Exception as e:
            logger.error(f"Error fetching market overview: {e}")
            raise
    
    # ========== PRIVATE FORMATTING METHODS ==========
    
    def _format_movers_response(self, data: Dict[str, Any], mover_type: str) -> Dict[str, Any]:
        """Format market movers (gainers/losers) into a clean structure."""
        tickers = data.get("tickers", [])
        
        if not tickers:
            return {"movers": [], "count": 0, "type": mover_type}
        
        movers = []
        for ticker in tickers:
            # Extract data safely
            symbol = ticker.get("ticker")
            day_data = ticker.get("day", {})
            prev_day_data = ticker.get("prevDay", {})
            
            current_price = day_data.get("c") or prev_day_data.get("c")
            prev_close = prev_day_data.get("c")
            
            # Calculate change and change percent
            change = None
            change_percent = None
            if current_price and prev_close:
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100
            
            movers.append({
                "symbol": symbol,
                "current_price": current_price,
                "change": change,
                "change_percent": change_percent,
                "volume": day_data.get("v"),
                "day_high": day_data.get("h"),
                "day_low": day_data.get("l")
            })
        
        return {
            "movers": movers,
            "count": len(movers),
            "type": mover_type
        }
    
    def _format_news_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format news data into a clean structure."""
        results = data.get("results", [])
        
        if not results:
            return {"articles": [], "count": 0}
        
        articles = []
        for article in results:
            articles.append({
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("article_url"),
                "image_url": article.get("image_url"),
                "author": article.get("author"),
                "published_utc": article.get("published_utc"),
                "publisher": article.get("publisher", {}).get("name"),
                "tickers": article.get("tickers", [])
            })
        
        return {
            "articles": articles,
            "count": len(articles)
        }
    
    @staticmethod
    def _get_current_timestamp() -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
