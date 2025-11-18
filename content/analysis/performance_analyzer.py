"""
Performance Analyzer

Analyzes tweet performance and learns what works.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from collections import Counter
import re
from loguru import logger

from backend.models.database import get_db_session, Tweet, DailyAnalytics


@dataclass
class PerformanceInsight:
    """Container for performance insights."""
    insight_type: str
    title: str
    description: str
    confidence: float
    recommendation: str
    data: Dict[str, Any]


class PerformanceAnalyzer:
    """
    Analyzes tweet performance to identify success patterns.

    Learns:
    - Best performing topics and categories
    - Optimal tweet characteristics (length, structure, hashtags)
    - Best posting times
    - What content resonates with audience
    """

    def __init__(self):
        """Initialize performance analyzer."""
        self.session = get_db_session()
        logger.info("PerformanceAnalyzer initialized")

    def analyze_top_performers(
        self,
        limit: int = 20,
        min_engagement: int = 50
    ) -> List[PerformanceInsight]:
        """
        Analyze top performing tweets to find patterns.

        Args:
            limit: Number of top tweets to analyze
            min_engagement: Minimum engagement threshold

        Returns:
            List of insights
        """
        logger.info(f"Analyzing top {limit} performers...")

        # Get top tweets
        top_tweets = self.session.query(Tweet).filter(
            Tweet.engagement_rate >= min_engagement / 100.0
        ).order_by(
            Tweet.engagement_rate.desc()
        ).limit(limit).all()

        if len(top_tweets) < 5:
            logger.warning("Not enough data for analysis")
            return []

        insights = []

        # Analyze optimal length
        length_insight = self._analyze_length_pattern(top_tweets)
        if length_insight:
            insights.append(length_insight)

        # Analyze hashtag effectiveness
        hashtag_insight = self._analyze_hashtags(top_tweets)
        if hashtag_insight:
            insights.append(hashtag_insight)

        # Analyze content structure
        structure_insight = self._analyze_structure(top_tweets)
        if structure_insight:
            insights.append(structure_insight)

        # Analyze topics
        topic_insight = self._analyze_topics(top_tweets)
        if topic_insight:
            insights.append(topic_insight)

        # Analyze timing
        timing_insight = self._analyze_timing(top_tweets)
        if timing_insight:
            insights.append(timing_insight)

        logger.info(f"Generated {len(insights)} insights")
        return insights

    def _analyze_length_pattern(self, tweets: List[Tweet]) -> Optional[PerformanceInsight]:
        """Analyze optimal tweet length."""
        lengths = [tweet.word_count or len(tweet.content.split()) for tweet in tweets]

        if not lengths:
            return None

        avg_length = np.mean(lengths)
        std_length = np.std(lengths)

        # Compare to all tweets
        all_tweets = self.session.query(Tweet).all()
        all_lengths = [t.word_count or len(t.content.split()) for t in all_tweets]
        overall_avg = np.mean(all_lengths) if all_lengths else 0

        if avg_length > overall_avg * 1.1:
            recommendation = f"Your best tweets are longer than average. Aim for {int(avg_length)} words."
        elif avg_length < overall_avg * 0.9:
            recommendation = f"Your best tweets are shorter than average. Aim for {int(avg_length)} words."
        else:
            recommendation = f"Your sweet spot is around {int(avg_length)} words."

        return PerformanceInsight(
            insight_type="length",
            title="Optimal Tweet Length",
            description=f"Top performing tweets average {int(avg_length)} words (±{int(std_length)})",
            confidence=0.8,
            recommendation=recommendation,
            data={
                "optimal_length": int(avg_length),
                "std_dev": int(std_length),
                "range": [int(avg_length - std_length), int(avg_length + std_length)]
            }
        )

    def _analyze_hashtags(self, tweets: List[Tweet]) -> Optional[PerformanceInsight]:
        """Analyze hashtag effectiveness."""
        all_hashtags = []
        for tweet in tweets:
            if tweet.hashtags:
                all_hashtags.extend(tweet.hashtags)

        if not all_hashtags:
            return PerformanceInsight(
                insight_type="hashtags",
                title="Hashtag Usage",
                description="Top tweets don't use hashtags",
                confidence=0.7,
                recommendation="Consider posting without hashtags for better engagement",
                data={"usage": "none"}
            )

        hashtag_counts = Counter(all_hashtags)
        top_hashtags = hashtag_counts.most_common(5)

        return PerformanceInsight(
            insight_type="hashtags",
            title="Best Performing Hashtags",
            description=f"Most effective hashtags: {', '.join([f'#{h}' for h, _ in top_hashtags[:3]])}",
            confidence=0.75,
            recommendation=f"Use these hashtags more: {', '.join([f'#{h}' for h, _ in top_hashtags[:3]])}",
            data={
                "top_hashtags": [{"hashtag": h, "count": c} for h, c in top_hashtags]
            }
        )

    def _analyze_structure(self, tweets: List[Tweet]) -> Optional[PerformanceInsight]:
        """Analyze content structure patterns."""
        has_question = sum(1 for t in tweets if t.has_question) / len(tweets)
        has_link = sum(1 for t in tweets if t.has_link) / len(tweets)
        has_media = sum(1 for t in tweets if t.has_media) / len(tweets)

        # Find dominant pattern
        patterns = {
            "questions": has_question,
            "links": has_link,
            "media": has_media
        }

        dominant = max(patterns.items(), key=lambda x: x[1])

        recommendations = {
            "questions": "Questions drive engagement. Ask your audience more!",
            "links": "Sharing links works well. Continue curating great content.",
            "media": "Visual content performs best. Add more images/videos."
        }

        return PerformanceInsight(
            insight_type="structure",
            title="Content Structure",
            description=f"{int(dominant[1] * 100)}% of top tweets include {dominant[0]}",
            confidence=0.85,
            recommendation=recommendations.get(dominant[0], ""),
            data={
                "questions": int(has_question * 100),
                "links": int(has_link * 100),
                "media": int(has_media * 100)
            }
        )

    def _analyze_topics(self, tweets: List[Tweet]) -> Optional[PerformanceInsight]:
        """Analyze best performing topics."""
        topic_counts = Counter([t.category for t in tweets if t.category])

        if not topic_counts:
            return None

        top_topics = topic_counts.most_common(3)

        return PerformanceInsight(
            insight_type="topics",
            title="Best Performing Topics",
            description=f"Top topic: {top_topics[0][0]} ({top_topics[0][1]} tweets)",
            confidence=0.9,
            recommendation=f"Focus more on: {', '.join([t for t, _ in top_topics])}",
            data={
                "top_topics": [{"topic": t, "count": c} for t, c in top_topics]
            }
        )

    def _analyze_timing(self, tweets: List[Tweet]) -> Optional[PerformanceInsight]:
        """Analyze best posting times."""
        if not tweets:
            return None

        # Get hour distribution
        hours = [t.posted_at.hour for t in tweets if t.posted_at]

        if not hours:
            return None

        hour_counts = Counter(hours)
        best_hours = hour_counts.most_common(3)

        def format_hour(h):
            return f"{h:02d}:00" if h < 12 else f"{h-12:02d}:00 PM" if h > 12 else "12:00 PM"

        return PerformanceInsight(
            insight_type="timing",
            title="Optimal Posting Times",
            description=f"Best hour: {format_hour(best_hours[0][0])} ({best_hours[0][1]} top tweets)",
            confidence=0.8,
            recommendation=f"Post more around: {', '.join([format_hour(h) for h, _ in best_hours])}",
            data={
                "best_hours": [{"hour": h, "count": c, "formatted": format_hour(h)}
                               for h, c in best_hours]
            }
        )

    def predict_engagement(self, tweet_text: str, metadata: Dict[str, Any] = None) -> float:
        """
        Predict engagement for a tweet before posting.

        Args:
            tweet_text: Tweet content
            metadata: Additional metadata (hashtags, has_media, etc.)

        Returns:
            Predicted engagement score (0-100)
        """
        score = 50.0  # Base score

        # Length analysis
        word_count = len(tweet_text.split())
        if 15 <= word_count <= 25:
            score += 10
        elif word_count < 10:
            score -= 5

        # Has question
        if '?' in tweet_text:
            score += 8

        # Has numbers/stats
        if any(char.isdigit() for char in tweet_text):
            score += 5

        # Has call to action
        cta_words = ['check', 'read', 'learn', 'discover', 'try', 'join']
        if any(word in tweet_text.lower() for word in cta_words):
            score += 5

        # Metadata
        if metadata:
            if metadata.get('has_media'):
                score += 15
            if metadata.get('has_link'):
                score += 5
            if metadata.get('hashtags'):
                # Good: 1-2 hashtags
                num_hashtags = len(metadata['hashtags'])
                if num_hashtags == 1 or num_hashtags == 2:
                    score += 5
                elif num_hashtags > 3:
                    score -= 5

        # Compare to historical top performers
        top_tweets = self.session.query(Tweet).order_by(
            Tweet.engagement_rate.desc()
        ).limit(10).all()

        if top_tweets:
            # Simple similarity check
            tweet_lower = tweet_text.lower()
            max_similarity = 0

            for top_tweet in top_tweets:
                # Count common words
                top_words = set(top_tweet.content.lower().split())
                tweet_words = set(tweet_lower.split())
                common = len(top_words & tweet_words)
                similarity = common / max(len(top_words), len(tweet_words))
                max_similarity = max(max_similarity, similarity)

            # Boost score based on similarity to top performers
            score += max_similarity * 20

        # Cap at 100
        return min(100, max(0, score))

    def get_content_recommendations(self) -> List[str]:
        """
        Generate actionable content recommendations.

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Analyze recent performance
        recent_tweets = self.session.query(Tweet).filter(
            Tweet.posted_at >= datetime.now() - timedelta(days=30)
        ).all()

        if len(recent_tweets) < 5:
            return ["Post more content to generate recommendations"]

        # Check posting frequency
        days_active = (max(t.posted_at for t in recent_tweets) -
                      min(t.posted_at for t in recent_tweets)).days or 1
        posts_per_day = len(recent_tweets) / days_active

        if posts_per_day < 1:
            recommendations.append(f"📈 Increase posting frequency. Currently {posts_per_day:.1f} posts/day. Aim for 2-3.")

        # Check engagement trend
        sorted_tweets = sorted(recent_tweets, key=lambda t: t.posted_at)
        first_half = sorted_tweets[:len(sorted_tweets)//2]
        second_half = sorted_tweets[len(sorted_tweets)//2:]

        avg_first = np.mean([t.engagement_rate for t in first_half if t.engagement_rate])
        avg_second = np.mean([t.engagement_rate for t in second_half if t.engagement_rate])

        if avg_second > avg_first * 1.2:
            recommendations.append("🔥 Your engagement is improving! Keep doing what you're doing.")
        elif avg_second < avg_first * 0.8:
            recommendations.append("📉 Engagement is declining. Try mixing up your content topics.")

        # Topic diversity
        topics = [t.category for t in recent_tweets if t.category]
        unique_topics = len(set(topics))

        if unique_topics < 3:
            recommendations.append("🎯 Expand topic diversity. Currently only covering 2-3 topics.")

        # Media usage
        media_tweets = sum(1 for t in recent_tweets if t.has_media)
        media_rate = media_tweets / len(recent_tweets)

        if media_rate < 0.3:
            recommendations.append("📸 Add more visual content. Only {:.0%} of tweets have media.".format(media_rate))

        # Best performers
        insights = self.analyze_top_performers(limit=10)
        for insight in insights[:2]:  # Top 2 insights
            recommendations.append(f"💡 {insight.recommendation}")

        return recommendations[:5]  # Return top 5

    def generate_performance_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.

        Args:
            days: Number of days to include in report

        Returns:
            Report dictionary
        """
        since = datetime.now() - timedelta(days=days)

        tweets = self.session.query(Tweet).filter(
            Tweet.posted_at >= since
        ).all()

        if not tweets:
            return {"error": "No tweets in this period"}

        total_engagement = sum(t.likes + t.retweets + t.replies for t in tweets)
        total_impressions = sum(t.impressions for t in tweets if t.impressions)
        avg_engagement_rate = np.mean([t.engagement_rate for t in tweets if t.engagement_rate])

        # Best and worst
        best = max(tweets, key=lambda t: t.engagement_rate or 0)
        worst = min(tweets, key=lambda t: t.engagement_rate or 0)

        # Topic breakdown
        topics = Counter([t.category for t in tweets if t.category])

        report = {
            "period": f"Last {days} days",
            "start_date": since.isoformat(),
            "end_date": datetime.now().isoformat(),
            "summary": {
                "total_tweets": len(tweets),
                "total_engagement": total_engagement,
                "total_impressions": total_impressions,
                "avg_engagement_rate": float(avg_engagement_rate),
                "posts_per_day": len(tweets) / days
            },
            "best_tweet": {
                "content": best.content,
                "engagement_rate": float(best.engagement_rate or 0),
                "likes": best.likes,
                "retweets": best.retweets
            },
            "worst_tweet": {
                "content": worst.content,
                "engagement_rate": float(worst.engagement_rate or 0)
            },
            "topics": dict(topics.most_common()),
            "insights": [
                {
                    "type": i.insight_type,
                    "title": i.title,
                    "description": i.description,
                    "recommendation": i.recommendation
                }
                for i in self.analyze_top_performers()
            ],
            "recommendations": self.get_content_recommendations()
        }

        return report

    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == "__main__":
    # Test analyzer
    analyzer = PerformanceAnalyzer()

    # Get insights
    insights = analyzer.analyze_top_performers()
    for insight in insights:
        print(f"\n{insight.title}")
        print(f"  {insight.description}")
        print(f"  Recommendation: {insight.recommendation}")

    # Test prediction
    score = analyzer.predict_engagement(
        "AI is transforming how we work. What's your take?",
        metadata={"has_media": False, "hashtags": ["AI", "Tech"]}
    )
    print(f"\nPredicted engagement score: {score:.1f}")

    # Get recommendations
    recommendations = analyzer.get_content_recommendations()
    print("\nRecommendations:")
    for rec in recommendations:
        print(f"  - {rec}")

    analyzer.close()
