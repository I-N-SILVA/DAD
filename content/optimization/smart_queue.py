"""
Smart Posting Queue

ML-powered tweet scheduling and optimization.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from collections import Counter
from loguru import logger

from backend.models.database import get_db_session, Tweet, TweetDraft
from content.analysis.tweet_scorer import TweetScorer


@dataclass
class ScheduledTweet:
    """Container for a scheduled tweet."""
    content: str
    scheduled_time: datetime
    predicted_score: float
    predicted_engagement: float
    category: str
    priority: int


class SmartPostingQueue:
    """
    Intelligent tweet queue with ML-powered scheduling.

    Features:
    - Predicts optimal posting times
    - Spaces content appropriately
    - Avoids topic clustering
    - Maximizes engagement potential
    """

    def __init__(self):
        """Initialize smart queue."""
        self.session = get_db_session()
        self.scorer = TweetScorer()
        logger.info("SmartPostingQueue initialized")

    def predict_best_time(
        self,
        tweet_content: str,
        category: Optional[str] = None,
        days_ahead: int = 7
    ) -> List[Tuple[datetime, float]]:
        """
        Predict best posting times for a tweet.

        Args:
            tweet_content: Tweet text
            category: Tweet category/topic
            days_ahead: Days to look ahead

        Returns:
            List of (datetime, predicted_engagement_score) tuples
        """
        logger.info(f"Predicting best times for tweet (category: {category})")

        # Get historical performance by time
        historical_tweets = self.session.query(Tweet).filter(
            Tweet.engagement_rate > 0
        ).all()

        if not historical_tweets:
            # No data, return default times
            return self._get_default_times(days_ahead)

        # Analyze performance by hour and day of week
        hour_performance = {}
        day_performance = {}

        for tweet in historical_tweets:
            if not tweet.posted_at or not tweet.engagement_rate:
                continue

            hour = tweet.posted_at.hour
            day = tweet.posted_at.weekday()

            if hour not in hour_performance:
                hour_performance[hour] = []
            hour_performance[hour].append(tweet.engagement_rate)

            if day not in day_performance:
                day_performance[day] = []
            day_performance[day].append(tweet.engagement_rate)

        # Calculate average performance
        hour_avg = {h: np.mean(rates) for h, rates in hour_performance.items()}
        day_avg = {d: np.mean(rates) for d, rates in day_performance.items()}

        # If category specified, weight by category performance
        if category:
            category_tweets = [t for t in historical_tweets if t.category == category]
            if category_tweets:
                cat_hour_perf = {}
                for tweet in category_tweets:
                    if tweet.posted_at:
                        h = tweet.posted_at.hour
                        if h not in cat_hour_perf:
                            cat_hour_perf[h] = []
                        cat_hour_perf[h].append(tweet.engagement_rate)

                # Blend category and overall performance
                for h in cat_hour_perf:
                    if h in hour_avg:
                        hour_avg[h] = 0.7 * np.mean(cat_hour_perf[h]) + 0.3 * hour_avg[h]

        # Generate potential posting times
        now = datetime.now()
        candidates = []

        for day_offset in range(days_ahead):
            target_date = now + timedelta(days=day_offset)

            # Check each good hour
            best_hours = sorted(hour_avg.items(), key=lambda x: x[1], reverse=True)[:5]

            for hour, avg_performance in best_hours:
                scheduled_time = target_date.replace(
                    hour=hour,
                    minute=np.random.choice([0, 15, 30, 45]),  # Vary minutes
                    second=0,
                    microsecond=0
                )

                # Skip past times
                if scheduled_time <= now:
                    continue

                # Check if slot is already taken
                if not self._is_slot_available(scheduled_time):
                    continue

                # Calculate predicted engagement
                day_of_week = scheduled_time.weekday()
                day_factor = day_avg.get(day_of_week, 0.5)

                # Score the tweet
                score = self.scorer.score_tweet(tweet_content)

                # Combine factors
                predicted_engagement = (
                    avg_performance * 0.4 +
                    day_factor * 0.2 +
                    (score["total"] / 100) * 0.4
                )

                candidates.append((scheduled_time, predicted_engagement))

        # Sort by predicted engagement
        candidates.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"Generated {len(candidates)} candidate times")
        return candidates[:10]  # Top 10 times

    def _get_default_times(self, days_ahead: int) -> List[Tuple[datetime, float]]:
        """Get default posting times when no historical data."""
        # Industry standard best times: 9 AM, 12 PM, 5 PM
        best_hours = [9, 12, 17]

        now = datetime.now()
        candidates = []

        for day_offset in range(days_ahead):
            target_date = now + timedelta(days=day_offset)

            # Skip weekends (lower engagement typically)
            if target_date.weekday() >= 5:
                continue

            for hour in best_hours:
                scheduled_time = target_date.replace(
                    hour=hour,
                    minute=0,
                    second=0,
                    microsecond=0
                )

                if scheduled_time > now:
                    candidates.append((scheduled_time, 0.5))  # Default score

        return candidates

    def _is_slot_available(self, scheduled_time: datetime, buffer_minutes: int = 60) -> bool:
        """Check if a time slot is available (no tweets within buffer)."""
        start = scheduled_time - timedelta(minutes=buffer_minutes)
        end = scheduled_time + timedelta(minutes=buffer_minutes)

        existing = self.session.query(TweetDraft).filter(
            TweetDraft.scheduled_for >= start,
            TweetDraft.scheduled_for <= end,
            TweetDraft.posted == False
        ).count()

        return existing == 0

    def auto_schedule_queue(
        self,
        tweets: List[str],
        categories: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        spacing_hours: int = 4
    ) -> List[ScheduledTweet]:
        """
        Automatically schedule a list of tweets optimally.

        Args:
            tweets: List of tweet texts
            categories: Optional categories for each tweet
            start_date: Start scheduling from this date
            spacing_hours: Minimum hours between tweets

        Returns:
            List of scheduled tweets
        """
        logger.info(f"Auto-scheduling {len(tweets)} tweets...")

        if categories and len(categories) != len(tweets):
            categories = [None] * len(tweets)
        elif not categories:
            categories = [None] * len(tweets)

        scheduled = []

        # Score all tweets first
        scored_tweets = []
        for i, (tweet, category) in enumerate(zip(tweets, categories)):
            score_data = self.scorer.score_tweet(tweet)
            scored_tweets.append({
                "index": i,
                "content": tweet,
                "category": category,
                "score": score_data["total"]
            })

        # Sort by score (post best content first)
        scored_tweets.sort(key=lambda x: x["score"], reverse=True)

        last_scheduled = start_date or datetime.now()

        for tweet_data in scored_tweets:
            # Find best time after last scheduled + spacing
            search_start = last_scheduled + timedelta(hours=spacing_hours)

            best_times = self.predict_best_time(
                tweet_data["content"],
                category=tweet_data["category"],
                days_ahead=14
            )

            # Filter times after search_start
            valid_times = [(t, score) for t, score in best_times if t >= search_start]

            if not valid_times:
                # Fallback: just space by spacing_hours
                scheduled_time = search_start
                predicted_engagement = 50.0
            else:
                scheduled_time, predicted_engagement = valid_times[0]

            scheduled_tweet = ScheduledTweet(
                content=tweet_data["content"],
                scheduled_time=scheduled_time,
                predicted_score=tweet_data["score"],
                predicted_engagement=predicted_engagement,
                category=tweet_data["category"] or "general",
                priority=100 - tweet_data["index"]  # Higher score = higher priority
            )

            scheduled.append(scheduled_tweet)
            last_scheduled = scheduled_time

            # Save to database
            draft = TweetDraft(
                content=tweet_data["content"],
                scheduled_for=scheduled_time,
                category=tweet_data["category"],
                predicted_score=tweet_data["score"],
                priority=scheduled_tweet.priority
            )
            self.session.add(draft)

        self.session.commit()
        logger.info(f"Scheduled {len(scheduled)} tweets")

        return scheduled

    def optimize_queue(self) -> Dict[str, Any]:
        """
        Optimize existing queue for better performance.

        Returns:
            Optimization report
        """
        logger.info("Optimizing tweet queue...")

        # Get all unposted drafts
        drafts = self.session.query(TweetDraft).filter(
            TweetDraft.posted == False,
            TweetDraft.scheduled_for > datetime.now()
        ).order_by(TweetDraft.scheduled_for).all()

        if not drafts:
            return {"message": "No tweets in queue to optimize"}

        optimizations = []

        # Check for topic clustering
        categories = [d.category for d in drafts if d.category]
        if len(categories) >= 3:
            for i in range(len(categories) - 2):
                if categories[i] == categories[i+1] == categories[i+2]:
                    optimizations.append({
                        "type": "topic_clustering",
                        "issue": f"Three consecutive {categories[i]} tweets",
                        "recommendation": "Mix up topics for better variety"
                    })
                    break

        # Check for poor timing
        for draft in drafts:
            best_times = self.predict_best_time(draft.content, draft.category)
            if best_times:
                best_time, best_score = best_times[0]
                current_score = draft.predicted_score or 50

                # If there's a much better time available
                if best_score > current_score * 1.2:
                    time_diff = (best_time - draft.scheduled_for).total_seconds() / 3600

                    if abs(time_diff) > 1:  # More than 1 hour difference
                        optimizations.append({
                            "type": "timing",
                            "tweet_id": draft.id,
                            "current_time": draft.scheduled_for.isoformat(),
                            "suggested_time": best_time.isoformat(),
                            "improvement": f"{((best_score / current_score - 1) * 100):.1f}% better"
                        })

        # Check spacing
        for i in range(len(drafts) - 1):
            time_diff = (drafts[i+1].scheduled_for - drafts[i].scheduled_for).total_seconds() / 3600

            if time_diff < 2:
                optimizations.append({
                    "type": "spacing",
                    "issue": f"Only {time_diff:.1f} hours between tweets",
                    "recommendation": "Space tweets at least 3-4 hours apart"
                })

        report = {
            "total_tweets": len(drafts),
            "optimizations_found": len(optimizations),
            "optimizations": optimizations,
            "overall_health": "good" if len(optimizations) < 2 else "needs_attention"
        }

        return report

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        total = self.session.query(TweetDraft).filter(
            TweetDraft.posted == False
        ).count()

        scheduled = self.session.query(TweetDraft).filter(
            TweetDraft.posted == False,
            TweetDraft.scheduled_for > datetime.now()
        ).order_by(TweetDraft.scheduled_for).all()

        pending_approval = self.session.query(TweetDraft).filter(
            TweetDraft.posted == False,
            TweetDraft.approved == False
        ).count()

        next_tweet = scheduled[0] if scheduled else None

        return {
            "total_in_queue": total,
            "scheduled_count": len(scheduled),
            "pending_approval": pending_approval,
            "next_tweet": {
                "content": next_tweet.content[:100] + "..." if len(next_tweet.content) > 100 else next_tweet.content,
                "scheduled_for": next_tweet.scheduled_for.isoformat(),
                "category": next_tweet.category
            } if next_tweet else None
        }

    def close(self):
        """Close database session."""
        self.scorer.close()
        self.session.close()


if __name__ == "__main__":
    # Test smart queue
    queue = SmartPostingQueue()

    # Test predicting best time
    tweet = "Just learned something amazing about AI and productivity!"
    best_times = queue.predict_best_time(tweet, category="AI", days_ahead=3)

    print("Best posting times:")
    for time, score in best_times[:5]:
        print(f"  {time.strftime('%Y-%m-%d %H:%M')} - Predicted engagement: {score:.3f}")

    # Test auto-schedule
    tweets_to_schedule = [
        "AI is transforming content creation",
        "New productivity hack I discovered",
        "The future of remote work looks interesting"
    ]

    scheduled = queue.auto_schedule_queue(
        tweets_to_schedule,
        categories=["AI", "Productivity", "Work"],
        spacing_hours=4
    )

    print(f"\nScheduled {len(scheduled)} tweets:")
    for st in scheduled:
        print(f"  {st.scheduled_time.strftime('%Y-%m-%d %H:%M')} - Score: {st.predicted_score:.1f}")

    # Get queue status
    status = queue.get_queue_status()
    print(f"\nQueue Status:")
    print(f"  Total in queue: {status['total_in_queue']}")
    print(f"  Scheduled: {status['scheduled_count']}")

    queue.close()
