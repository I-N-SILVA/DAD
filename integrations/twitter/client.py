"""
X/Twitter API Client

Handles interaction with X/Twitter API for posting, monitoring, and analytics.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger

try:
    import tweepy
except ImportError:
    logger.warning("tweepy not installed. Run: pip install tweepy")
    tweepy = None


@dataclass
class Tweet:
    """Container for tweet data."""
    id: str
    text: str
    created_at: str
    author_id: str
    metrics: Dict[str, int]
    metadata: Dict[str, Any] = None


@dataclass
class TweetMetrics:
    """Engagement metrics for a tweet."""
    likes: int
    retweets: int
    replies: int
    impressions: int
    engagement_rate: float


class TwitterClient:
    """
    Client for X/Twitter API.

    Features:
    - Post tweets and threads
    - Schedule tweets
    - Monitor mentions and keywords
    - Track engagement metrics
    - Search and retrieve tweets
    - Get trending topics
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str,
        bearer_token: Optional[str] = None
    ):
        """
        Initialize Twitter client.

        Args:
            api_key: Twitter API key
            api_secret: Twitter API secret
            access_token: Access token
            access_secret: Access token secret
            bearer_token: Bearer token (for API v2)
        """
        if not tweepy:
            raise ImportError("tweepy required. Install with: pip install tweepy")

        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_secret = access_secret
        self.bearer_token = bearer_token

        # Initialize Tweepy clients
        # API v1.1 client
        auth = tweepy.OAuth1UserHandler(
            api_key, api_secret,
            access_token, access_secret
        )
        self.api_v1 = tweepy.API(auth)

        # API v2 client
        if bearer_token:
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_secret
            )
        else:
            self.client = None

        logger.info("TwitterClient initialized")

    def post_tweet(
        self,
        text: str,
        reply_to: Optional[str] = None
    ) -> Tweet:
        """
        Post a tweet.

        Args:
            text: Tweet text (max 280 chars)
            reply_to: Tweet ID to reply to (optional)

        Returns:
            Tweet object with posted tweet data
        """
        if len(text) > 280:
            raise ValueError(f"Tweet too long: {len(text)} characters (max 280)")

        logger.info(f"Posting tweet: {text[:50]}...")

        try:
            if self.client:
                # Use API v2
                response = self.client.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=reply_to
                )

                tweet_data = response.data
                return Tweet(
                    id=str(tweet_data['id']),
                    text=text,
                    created_at=datetime.now().isoformat(),
                    author_id=str(tweet_data.get('author_id', '')),
                    metrics={}
                )
            else:
                # Use API v1.1
                if reply_to:
                    status = self.api_v1.update_status(
                        status=text,
                        in_reply_to_status_id=reply_to
                    )
                else:
                    status = self.api_v1.update_status(status=text)

                return Tweet(
                    id=str(status.id),
                    text=status.text,
                    created_at=status.created_at.isoformat(),
                    author_id=str(status.user.id),
                    metrics={
                        'likes': status.favorite_count,
                        'retweets': status.retweet_count
                    }
                )

        except Exception as e:
            logger.error(f"Error posting tweet: {e}")
            raise

    def post_thread(
        self,
        tweets: List[str]
    ) -> List[Tweet]:
        """
        Post a thread of tweets.

        Args:
            tweets: List of tweet texts

        Returns:
            List of posted Tweet objects
        """
        logger.info(f"Posting thread with {len(tweets)} tweets...")

        posted_tweets = []
        reply_to = None

        for i, text in enumerate(tweets):
            try:
                tweet = self.post_tweet(text, reply_to=reply_to)
                posted_tweets.append(tweet)
                reply_to = tweet.id

                logger.info(f"Posted tweet {i + 1}/{len(tweets)}")

            except Exception as e:
                logger.error(f"Error posting tweet {i + 1}: {e}")
                break

        return posted_tweets

    def get_tweet(
        self,
        tweet_id: str,
        include_metrics: bool = True
    ) -> Tweet:
        """
        Get a tweet by ID.

        Args:
            tweet_id: Tweet ID
            include_metrics: Include engagement metrics

        Returns:
            Tweet object
        """
        try:
            if self.client:
                response = self.client.get_tweet(
                    tweet_id,
                    tweet_fields=['created_at', 'author_id', 'public_metrics']
                )

                tweet_data = response.data
                metrics = tweet_data.public_metrics if hasattr(tweet_data, 'public_metrics') else {}

                return Tweet(
                    id=str(tweet_data.id),
                    text=tweet_data.text,
                    created_at=tweet_data.created_at.isoformat(),
                    author_id=str(tweet_data.author_id),
                    metrics=metrics
                )
            else:
                status = self.api_v1.get_status(tweet_id)
                return Tweet(
                    id=str(status.id),
                    text=status.text,
                    created_at=status.created_at.isoformat(),
                    author_id=str(status.user.id),
                    metrics={
                        'likes': status.favorite_count,
                        'retweets': status.retweet_count
                    }
                )

        except Exception as e:
            logger.error(f"Error getting tweet {tweet_id}: {e}")
            raise

    def get_user_tweets(
        self,
        username: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 10,
        include_replies: bool = False
    ) -> List[Tweet]:
        """
        Get tweets from a user.

        Args:
            username: Username (without @)
            user_id: User ID (alternative to username)
            limit: Number of tweets to retrieve
            include_replies: Include replies

        Returns:
            List of Tweet objects
        """
        try:
            if self.client:
                if username:
                    user = self.client.get_user(username=username)
                    user_id = user.data.id
                elif not user_id:
                    # Get authenticated user's tweets
                    user = self.client.get_me()
                    user_id = user.data.id

                response = self.client.get_users_tweets(
                    user_id,
                    max_results=min(limit, 100),
                    exclude='retweets' if not include_replies else None,
                    tweet_fields=['created_at', 'public_metrics']
                )

                tweets = []
                for tweet_data in response.data or []:
                    tweets.append(Tweet(
                        id=str(tweet_data.id),
                        text=tweet_data.text,
                        created_at=tweet_data.created_at.isoformat(),
                        author_id=str(user_id),
                        metrics=tweet_data.public_metrics
                    ))

                return tweets
            else:
                if username:
                    user = self.api_v1.get_user(screen_name=username)
                    user_id = user.id

                statuses = self.api_v1.user_timeline(
                    user_id=user_id,
                    count=limit,
                    exclude_replies=not include_replies
                )

                return [Tweet(
                    id=str(s.id),
                    text=s.text,
                    created_at=s.created_at.isoformat(),
                    author_id=str(s.user.id),
                    metrics={
                        'likes': s.favorite_count,
                        'retweets': s.retweet_count
                    }
                ) for s in statuses]

        except Exception as e:
            logger.error(f"Error getting user tweets: {e}")
            return []

    def search_tweets(
        self,
        query: str,
        limit: int = 10,
        recent: bool = True
    ) -> List[Tweet]:
        """
        Search for tweets.

        Args:
            query: Search query
            limit: Number of results
            recent: Get recent tweets (vs. popular)

        Returns:
            List of Tweet objects
        """
        try:
            if self.client:
                response = self.client.search_recent_tweets(
                    query=query,
                    max_results=min(limit, 100),
                    tweet_fields=['created_at', 'author_id', 'public_metrics']
                )

                tweets = []
                for tweet_data in response.data or []:
                    tweets.append(Tweet(
                        id=str(tweet_data.id),
                        text=tweet_data.text,
                        created_at=tweet_data.created_at.isoformat(),
                        author_id=str(tweet_data.author_id),
                        metrics=tweet_data.public_metrics
                    ))

                return tweets
            else:
                statuses = self.api_v1.search_tweets(q=query, count=limit)

                return [Tweet(
                    id=str(s.id),
                    text=s.text,
                    created_at=s.created_at.isoformat(),
                    author_id=str(s.user.id),
                    metrics={
                        'likes': s.favorite_count,
                        'retweets': s.retweet_count
                    }
                ) for s in statuses]

        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            return []

    def get_trending_topics(
        self,
        location_id: int = 1  # 1 = Worldwide
    ) -> List[Dict[str, Any]]:
        """
        Get trending topics.

        Args:
            location_id: Location WOEID (1 = Worldwide, 23424977 = USA)

        Returns:
            List of trending topics
        """
        try:
            trends = self.api_v1.get_place_trends(location_id)

            trending = []
            for trend in trends[0]['trends']:
                trending.append({
                    'name': trend['name'],
                    'url': trend['url'],
                    'tweet_volume': trend.get('tweet_volume')
                })

            logger.info(f"Retrieved {len(trending)} trending topics")
            return trending

        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return []

    def get_metrics(
        self,
        tweet_id: str
    ) -> TweetMetrics:
        """
        Get detailed metrics for a tweet.

        Args:
            tweet_id: Tweet ID

        Returns:
            TweetMetrics object
        """
        tweet = self.get_tweet(tweet_id, include_metrics=True)

        metrics = tweet.metrics
        likes = metrics.get('like_count', metrics.get('likes', 0))
        retweets = metrics.get('retweet_count', metrics.get('retweets', 0))
        replies = metrics.get('reply_count', metrics.get('replies', 0))
        impressions = metrics.get('impression_count', metrics.get('impressions', 0))

        total_engagement = likes + retweets + replies
        engagement_rate = (total_engagement / impressions * 100) if impressions > 0 else 0

        return TweetMetrics(
            likes=likes,
            retweets=retweets,
            replies=replies,
            impressions=impressions,
            engagement_rate=engagement_rate
        )

    def delete_tweet(self, tweet_id: str) -> bool:
        """Delete a tweet."""
        try:
            if self.client:
                self.client.delete_tweet(tweet_id)
            else:
                self.api_v1.destroy_status(tweet_id)

            logger.info(f"Deleted tweet {tweet_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting tweet: {e}")
            return False

    def __repr__(self) -> str:
        return "TwitterClient(authenticated)"


if __name__ == "__main__":
    import os

    # Test Twitter client
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        print("Please set Twitter API credentials in environment variables")
        exit(1)

    client = TwitterClient(
        api_key=api_key,
        api_secret=api_secret,
        access_token=access_token,
        access_secret=access_secret
    )

    # Test search
    print("Searching for AI tweets...")
    tweets = client.search_tweets("artificial intelligence", limit=5)
    for tweet in tweets:
        print(f"- {tweet.text[:100]}")

    # Test trending topics
    print("\nTrending topics:")
    trends = client.get_trending_topics()
    for trend in trends[:10]:
        print(f"- {trend['name']}")
