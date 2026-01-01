"""
Social Media Service for Flood Monitoring.
Uses:
1. NewsAPI (Free Tier) - To validate "Social Buzz" / News confirmation.
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
    NEWS_API_URL = "https://newsapi.org/v2/everything"
    
    def __init__(self):
        # Load from .env
        self.news_api_key = os.getenv("NEWS_API_KEY", "")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    def get_social_context(self, location="Odisha"):
        """
        Fetch news/social buzz regarding floods in the area.
        Acts as 'Layer 4' validation (External Confirmation).
        """
        if self.news_api_key == "demo-key-placeholder":
            return self._get_mock_news(location)
            
        try:
            params = {
                "q": f"{location} AND (flood OR rain OR disaster)",
                "sortBy": "publishedAt",
                "apiKey": self.news_api_key,
                "language": "en"
            }
            response = requests.get(self.NEWS_API_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            articles = data.get('articles', [])
            return {
                "buzz_score": min(len(articles) * 0.1, 1.0),  # 10 articles = max score
                "recent_headlines": [a['title'] for a in articles[:3]],
                "source": "NewsAPI"
            }
        except Exception as e:
            logger.error(f"NewsAPI failed: {e}")
            return self._get_mock_news(location)

    def _get_mock_news(self, location):
        """Fallback mock data for demo/testing."""
        return {
            "buzz_score": 0.0,
            "recent_headlines": [],
            "source": "None"
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
