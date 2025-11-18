"""
Database Models

SQLAlchemy models for tracking tweets, analytics, and performance.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from pathlib import Path
from loguru import logger

Base = declarative_base()


class Tweet(Base):
    """Stores posted tweets and their performance metrics."""
    __tablename__ = 'tweets'

    id = Column(Integer, primary_key=True)
    tweet_id = Column(String, unique=True, index=True)
    content = Column(Text, nullable=False)
    posted_at = Column(DateTime, default=datetime.now, index=True)

    # Engagement metrics
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)

    # Content metadata
    category = Column(String, index=True)
    sentiment = Column(Float)
    hashtags = Column(JSON)
    word_count = Column(Integer)
    has_media = Column(Boolean, default=False)
    has_link = Column(Boolean, default=False)
    has_question = Column(Boolean, default=False)

    # Performance tracking
    score = Column(Float)  # Pre-post prediction score
    predicted_engagement = Column(Float)
    actual_vs_predicted = Column(Float)

    # Relationships
    ab_test_id = Column(Integer, ForeignKey('ab_tests.id'), nullable=True)
    ab_test = relationship("ABTest", back_populates="tweets")

    def __repr__(self):
        return f"<Tweet {self.tweet_id}: {self.content[:50]}>"


class TweetDraft(Base):
    """Stores draft tweets in the queue."""
    __tablename__ = 'tweet_drafts'

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    scheduled_for = Column(DateTime, index=True)
    posted = Column(Boolean, default=False)
    posted_tweet_id = Column(String, nullable=True)

    # Generation metadata
    topic = Column(String)
    category = Column(String)
    confidence = Column(Float)
    predicted_score = Column(Float)

    # Queue management
    priority = Column(Integer, default=0)
    approved = Column(Boolean, default=False)
    approved_by = Column(String, nullable=True)

    def __repr__(self):
        return f"<TweetDraft {self.id}: {self.content[:50]}>"


class DailyAnalytics(Base):
    """Daily aggregated analytics."""
    __tablename__ = 'daily_analytics'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, unique=True, index=True)

    # Follower metrics
    follower_count = Column(Integer)
    follower_growth = Column(Integer)

    # Content metrics
    tweets_posted = Column(Integer, default=0)
    total_impressions = Column(Integer, default=0)
    total_engagement = Column(Integer, default=0)
    avg_engagement_rate = Column(Float, default=0.0)

    # Performance
    best_performing_tweet_id = Column(String)
    best_performing_engagement = Column(Integer)
    worst_performing_tweet_id = Column(String)

    # Topic distribution
    topic_distribution = Column(JSON)

    def __repr__(self):
        return f"<DailyAnalytics {self.date.date()}>"


class Competitor(Base):
    """Tracks competitor accounts."""
    __tablename__ = 'competitors'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    display_name = Column(String)
    added_at = Column(DateTime, default=datetime.now)

    # Current stats
    follower_count = Column(Integer)
    following_count = Column(Integer)
    tweet_count = Column(Integer)

    # Tracking settings
    active = Column(Boolean, default=True)
    check_frequency = Column(String, default='daily')

    # Analysis
    avg_engagement_rate = Column(Float)
    posts_per_day = Column(Float)
    primary_topics = Column(JSON)
    posting_times = Column(JSON)

    # Relationships
    snapshots = relationship("CompetitorSnapshot", back_populates="competitor")

    def __repr__(self):
        return f"<Competitor @{self.username}>"


class CompetitorSnapshot(Base):
    """Periodic snapshots of competitor metrics."""
    __tablename__ = 'competitor_snapshots'

    id = Column(Integer, primary_key=True)
    competitor_id = Column(Integer, ForeignKey('competitors.id'))
    timestamp = Column(DateTime, default=datetime.now, index=True)

    follower_count = Column(Integer)
    tweet_count = Column(Integer)
    recent_engagement_rate = Column(Float)

    # Recent content analysis
    topics_covered = Column(JSON)
    content_types = Column(JSON)

    # Relationships
    competitor = relationship("Competitor", back_populates="snapshots")

    def __repr__(self):
        return f"<CompetitorSnapshot {self.competitor_id} at {self.timestamp}>"


class ABTest(Base):
    """A/B tests for content optimization."""
    __tablename__ = 'ab_tests'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    hypothesis = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    # Test configuration
    variant_a_description = Column(Text)
    variant_b_description = Column(Text)
    duration_days = Column(Integer, default=7)

    # Results
    status = Column(String, default='draft')  # draft, running, completed
    variant_a_count = Column(Integer, default=0)
    variant_b_count = Column(Integer, default=0)
    variant_a_avg_engagement = Column(Float)
    variant_b_avg_engagement = Column(Float)
    winner = Column(String, nullable=True)  # A, B, or inconclusive
    confidence_level = Column(Float)

    # Insights
    insights = Column(JSON)

    # Relationships
    tweets = relationship("Tweet", back_populates="ab_test")

    def __repr__(self):
        return f"<ABTest {self.name} ({self.status})>"


class ContentGap(Base):
    """Identified content gaps from competitor analysis."""
    __tablename__ = 'content_gaps'

    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)
    discovered_at = Column(DateTime, default=datetime.now)

    # Opportunity metrics
    opportunity_score = Column(Float)
    search_volume = Column(Integer, nullable=True)
    competitor_coverage = Column(Integer)

    # Gap analysis
    why_gap = Column(Text)
    suggested_angle = Column(Text)

    # Status
    addressed = Column(Boolean, default=False)
    tweet_id = Column(String, nullable=True)

    def __repr__(self):
        return f"<ContentGap {self.topic} (score: {self.opportunity_score})>"


class TrendAlert(Base):
    """Real-time trend alerts."""
    __tablename__ = 'trend_alerts'

    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False, index=True)
    detected_at = Column(DateTime, default=datetime.now, index=True)

    # Trend metadata
    source = Column(String)  # twitter, reddit, hackernews, etc.
    trend_score = Column(Float)
    velocity = Column(Float)  # How fast it's trending
    predicted_duration_hours = Column(Integer)

    # Response
    content_generated = Column(Boolean, default=False)
    tweet_id = Column(String, nullable=True)
    response_time_minutes = Column(Integer)

    # Performance
    engagement = Column(Integer)
    was_successful = Column(Boolean, nullable=True)

    def __repr__(self):
        return f"<TrendAlert {self.topic} at {self.detected_at}>"


class EngagementInteraction(Base):
    """Track engagement interactions (replies, likes, etc)."""
    __tablename__ = 'engagement_interactions'

    id = Column(Integer, primary_key=True)
    interaction_type = Column(String)  # reply, like, retweet, follow
    target_tweet_id = Column(String, nullable=True)
    target_username = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)

    # AI-generated reply
    our_tweet_id = Column(String, nullable=True)
    our_content = Column(Text, nullable=True)

    # Context
    was_automated = Column(Boolean, default=False)
    required_approval = Column(Boolean, default=False)

    # Outcome
    resulted_in_follow = Column(Boolean, default=False)
    resulted_in_engagement = Column(Boolean, default=False)

    def __repr__(self):
        return f"<EngagementInteraction {self.interaction_type} at {self.timestamp}>"


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, db_path: str = "data/databases/xcontentrag.db"):
        """Initialize database manager."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create engine
        self.engine = create_engine(f'sqlite:///{self.db_path}')

        # Create tables
        Base.metadata.create_all(self.engine)

        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)

        logger.info(f"Database initialized at {self.db_path}")

    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()

    def close(self):
        """Close database connection."""
        self.engine.dispose()


# Global database instance
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        from backend.core.config import get_config
        config = get_config()
        db_path = config.get('database.sqlite_path', 'data/databases/xcontentrag.db')
        _db_manager = DatabaseManager(db_path)
    return _db_manager


def get_db_session():
    """Get a database session."""
    db_manager = get_db_manager()
    return db_manager.get_session()


if __name__ == "__main__":
    # Test database setup
    db = DatabaseManager("data/databases/test.db")

    session = db.get_session()

    # Create test tweet
    tweet = Tweet(
        tweet_id="123456",
        content="Test tweet about AI",
        likes=100,
        retweets=20,
        category="AI",
        hashtags=["AI", "Tech"]
    )

    session.add(tweet)
    session.commit()

    # Query
    tweets = session.query(Tweet).all()
    print(f"Found {len(tweets)} tweets")

    session.close()
    db.close()
