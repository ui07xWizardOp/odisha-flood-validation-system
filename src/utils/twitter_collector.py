import os
import tweepy
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load env variables
load_dotenv()

class TwitterCollector:
    """
    Collects tweets using Twitter API v2.
    """
    def __init__(self):
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        if not self.bearer_token:
            print("Warning: TWITTER_BEARER_TOKEN not found in environment.")
            self.client = None
        else:
            self.client = tweepy.Client(bearer_token=self.bearer_token)

    def fetch_historical_tweets(self, query: str, start_time: str, end_time: str, max_results: int = 100) -> pd.DataFrame:
        """
        Fetches historical tweets (requires Academic Access or high-tier access).
        For Standard/Essential access, this endpoint might not be available or limited to recent 7 days.
        
        Args:
            query (str): Search query (e.g. "flood place:Odisha has:geo").
            start_time (str): ISO 8601 timestamp (YYYY-MM-DDTHH:mm:ssZ).
            end_time (str): ISO 8601 timestamp.
            max_results (int): Max results per page (10-100).
            
        Returns:
            pd.DataFrame: Collected tweets.
        """
        if not self.client:
            raise ValueError("Twitter Client not initialized.")

        tweets_data = []
        
        # Note: 'search_all_tweets' is for full archive, 'search_recent_tweets' for 7 days.
        # Trying to be generic. 
        try:
            # Using Paginator for handling pagination
            # Note: This might fail if using Free/Basic tier on search_all_tweets
            paginator = tweepy.Paginator(
                self.client.search_all_tweets,
                query=query,
                tweet_fields=['created_at', 'geo', 'author_id', 'text'],
                start_time=start_time,
                end_time=end_time,
                max_results=max_results,
                limit=10  # Safety limit on requests
            )

            for response in paginator:
                if response.data:
                    for tweet in response.data:
                        data = {
                            'tweet_id': tweet.id,
                            'text': tweet.text,
                            'created_at': tweet.created_at,
                            'author_id': tweet.author_id,
                            'geo': tweet.geo
                        }
                        tweets_data.append(data)
                        
        except tweepy.errors.Forbidden as e:
            print(f"Access Forbidden (likely tier limitation): {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching tweets: {e}")
            return pd.DataFrame()

        return pd.DataFrame(tweets_data)

if __name__ == "__main__":
    # Example usage
    collector = TwitterCollector()
    # df = collector.fetch_historical_tweets("flood", "2019-05-01T00:00:00Z", "2019-05-05T00:00:00Z")
    # if not df.empty:
    #     df.to_csv("data/raw/social_media/tweets.csv")
