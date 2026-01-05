"""
Social Media Service for Flood Monitoring.
Uses:
1. NewsData.io (Free Tier) - To validate "Social Buzz" / News confirmation.
2. Telegram Bot Logic (Stub) - To accept crowdsourced reports via chat.
"""

import requests
import os
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SocialMediaService:
    # NewsData.io API (free tier: 200 requests/day)
    NEWS_API_URL = "https://newsdata.io/api/1/news"
    
    def __init__(self):
        # Load from .env or use provided key
        self.news_api_key = os.getenv("NEWS_API_KEY", "pub_bad062c65c504ec7bd821aaca2685cc3")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    def get_social_context(self, location="Odisha"):
        """
        Fetch news/social buzz regarding floods in the area.
        Acts as 'Layer 4' validation (External Confirmation).
        """
        if not self.news_api_key or self.news_api_key == "demo-key-placeholder":
            return self._get_mock_news(location)
            
        try:
            params = {
                "q": f"{location} flood",
                "country": "in",
                "language": "en",
                "apikey": self.news_api_key
            }
            response = requests.get(self.NEWS_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'success':
                logger.warning(f"NewsData.io returned status: {data.get('status')}")
                return self._get_mock_news(location)
            
            articles = data.get('results', [])
            
            return {
                "buzz_score": min(len(articles) * 0.1, 1.0),  # 10 articles = max score
                "recent_headlines": [a.get('title', '')[:100] for a in articles[:3]],
                "article_count": len(articles),
                "source": "NewsData.io"
            }
        except requests.exceptions.Timeout:
            logger.warning("NewsData.io request timed out")
            return self._get_mock_news(location)
        except requests.exceptions.RequestException as e:
            logger.error(f"NewsData.io request failed: {e}")
            return self._get_mock_news(location)
        except Exception as e:
            logger.error(f"NewsData.io processing error: {e}")
            return self._get_mock_news(location)

    def _get_mock_news(self, location):
        """Fallback mock data for demo/testing."""
        return {
            "buzz_score": 0.5,  # Neutral default
            "recent_headlines": ["Mock: Monitoring weather conditions"],
            "article_count": 0,
            "source": "Mock"
        }

    def process_telegram_webhook(self, update: dict):
        """
        Process incoming Telegram message as a Flood Report.
        Format expected: "Location: x,y | Depth: 1m | Desc: ..."
        """
        try:
            message = update.get('message', {})
            text = message.get('text', '')
            chat_id = message.get('chat', {}).get('id')
            
            # Simple parsing logic (Demo)
            if 'flood' in text.lower():
                return {
                    "source": "telegram",
                    "user_id": f"tg_{chat_id}",
                    "description": text,
                    "likely_report": True
                }
            return None
        except Exception as e:
            logger.error(f"Telegram processing error: {e}")
            return None

# Singleton
social_service = SocialMediaService()
