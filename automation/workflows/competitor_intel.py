"""
Competitor Intelligence Workflow

Monitors and analyzes competitor accounts for strategic insights.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter
import asyncio
from loguru import logger

from integrations.twitter.client import TwitterClient
from integrations.claude.client import ClaudeClient
from backend.models.database import get_db_session, Competitor, CompetitorSnapshot, ContentGap
from rag.indexing.indexer import DocumentIndexer


class CompetitorIntelligence:
    """
    Deep competitor analysis and content gap identification.

    Features:
    - Track multiple competitors
    - Analyze posting patterns
    - Identify content gaps
    - Generate differentiated content ideas
    """

    def __init__(
        self,
        twitter_client: TwitterClient,
        claude_client: ClaudeClient,
        document_indexer: Optional[DocumentIndexer] = None
    ):
        """
        Initialize competitor intelligence.

        Args:
            twitter_client: Twitter API client
            claude_client: Claude API client
            document_indexer: Optional document indexer for storing insights
        """
        self.twitter_client = twitter_client
        self.claude_client = claude_client
        self.document_indexer = document_indexer
        self.session = get_db_session()

        logger.info("CompetitorIntelligence initialized")

    async def analyze_competitor_strategy(
        self,
        username: str,
        depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        Comprehensive competitor analysis.

        Args:
            username: Competitor's username (without @)
            depth: Analysis depth (quick, standard, deep)

        Returns:
            Analysis report
        """
        logger.info(f"Analyzing competitor @{username} (depth: {depth})")

        report = {
            "username": username,
            "analyzed_at": datetime.now().isoformat(),
            "metrics": {},
            "patterns": {},
            "insights": [],
            "recommendations": []
        }

        try:
            # Get competitor from database or create
            competitor = self.session.query(Competitor).filter(
                Competitor.username == username
            ).first()

            if not competitor:
                competitor = Competitor(username=username)
                self.session.add(competitor)
                self.session.commit()

            # Get recent tweets
            num_tweets = {"quick": 20, "standard": 50, "deep": 100}[depth]
            recent_tweets = self.twitter_client.get_user_tweets(
                username=username,
                limit=num_tweets
            )

            if not recent_tweets:
                report["error"] = "Could not fetch tweets"
                return report

            # Basic metrics
            total_engagement = sum(
                t.metrics.get('like_count', 0) +
                t.metrics.get('retweet_count', 0) +
                t.metrics.get('reply_count', 0)
                for t in recent_tweets
            )
            avg_engagement = total_engagement / len(recent_tweets)

            report["metrics"] = {
                "total_tweets_analyzed": len(recent_tweets),
                "avg_engagement": avg_engagement,
                "total_engagement": total_engagement,
                "engagement_rate": avg_engagement / 1000  # Rough estimate
            }

            # Posting patterns
            patterns = self._analyze_posting_patterns(recent_tweets)
            report["patterns"] = patterns

            # Topic analysis
            topics = await self._analyze_topics(recent_tweets)
            report["topics"] = topics

            # Content analysis
            if depth in ["standard", "deep"]:
                content_insights = await self._analyze_content_style(recent_tweets)
                report["content_style"] = content_insights

            # Generate insights
            insights = self._generate_insights(report)
            report["insights"] = insights

            # Save snapshot
            snapshot = CompetitorSnapshot(
                competitor_id=competitor.id,
                timestamp=datetime.now(),
                tweet_count=len(recent_tweets),
                recent_engagement_rate=report["metrics"]["engagement_rate"],
                topics_covered=topics[:5],
                content_types=patterns.get("content_types", {})
            )
            self.session.add(snapshot)

            # Update competitor record
            competitor.avg_engagement_rate = report["metrics"]["engagement_rate"]
            competitor.posts_per_day = patterns.get("posts_per_day", 0)
            competitor.primary_topics = topics[:5]
            competitor.posting_times = patterns.get("best_hours", [])

            self.session.commit()

            logger.info(f"Completed analysis of @{username}")

        except Exception as e:
            logger.error(f"Error analyzing competitor: {e}")
            report["error"] = str(e)

        return report

    def _analyze_posting_patterns(self, tweets: List[Any]) -> Dict[str, Any]:
        """Analyze when and how competitor posts."""
        if not tweets:
            return {}

        # Time analysis
        hours = [datetime.fromisoformat(t.created_at).hour
                for t in tweets if t.created_at]
        hour_counts = Counter(hours)
        best_hours = [h for h, _ in hour_counts.most_common(3)]

        # Day of week
        days = [datetime.fromisoformat(t.created_at).weekday()
               for t in tweets if t.created_at]
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_counts = Counter(days)

        # Content types
        has_media = sum(1 for t in tweets if 'media' in str(t.metadata))
        has_links = sum(1 for t in tweets if 'http' in t.text)
        has_threads = sum(1 for t in tweets if t.text.startswith('1/'))

        # Calculate posting frequency
        if len(tweets) > 1:
            first = datetime.fromisoformat(tweets[-1].created_at)
            last = datetime.fromisoformat(tweets[0].created_at)
            days_span = (last - first).days or 1
            posts_per_day = len(tweets) / days_span
        else:
            posts_per_day = 0

        return {
            "posts_per_day": round(posts_per_day, 2),
            "best_hours": best_hours,
            "day_distribution": {day_names[d]: c for d, c in day_counts.most_common()},
            "content_types": {
                "with_media": has_media,
                "with_links": has_links,
                "threads": has_threads,
                "text_only": len(tweets) - has_media - has_links
            }
        }

    async def _analyze_topics(self, tweets: List[Any]) -> List[str]:
        """Extract main topics using Claude."""
        # Combine tweet texts
        combined_text = "\n".join([t.text for t in tweets[:30]])  # Limit for token efficiency

        prompt = f"""Analyze these tweets and identify the top 10 topics/themes:

{combined_text}

Return ONLY a JSON array of topic strings:
["topic1", "topic2", "topic3", ...]"""

        try:
            result = await self.claude_client.generate_async(
                prompt=prompt,
                system="You are an expert content analyst. Respond only with valid JSON.",
                max_tokens=500,
                temperature=0.3
            )

            # Parse JSON
            import json
            topics = json.loads(result.content.strip())
            return topics

        except Exception as e:
            logger.error(f"Error analyzing topics: {e}")
            # Fallback: simple keyword extraction
            from collections import Counter
            import re

            words = []
            for tweet in tweets:
                # Extract hashtags and common words
                hashtags = re.findall(r'#(\w+)', tweet.text)
                words.extend([h.lower() for h in hashtags])

            common = Counter(words).most_common(10)
            return [word for word, _ in common]

    async def _analyze_content_style(self, tweets: List[Any]) -> Dict[str, Any]:
        """Analyze writing style and content characteristics."""
        sample_tweets = [t.text for t in tweets[:10]]

        prompt = f"""Analyze the writing style of these tweets:

{chr(10).join(sample_tweets)}

Provide analysis in JSON:
{{
  "tone": "...",
  "style": "...",
  "common_patterns": ["...", "..."],
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."]
}}"""

        try:
            result = await self.claude_client.generate_async(
                prompt=prompt,
                system="You are a content style analyst. Respond with valid JSON only.",
                max_tokens=500
            )

            import json
            analysis = json.loads(result.content.strip())
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing style: {e}")
            return {
                "tone": "unknown",
                "style": "unknown",
                "note": "Analysis failed"
            }

    def _generate_insights(self, report: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from analysis."""
        insights = []

        metrics = report.get("metrics", {})
        patterns = report.get("patterns", {})

        # Posting frequency insights
        posts_per_day = patterns.get("posts_per_day", 0)
        if posts_per_day > 3:
            insights.append(f"🔥 Very active: {posts_per_day:.1f} posts/day. Consider matching their frequency.")
        elif posts_per_day < 1:
            insights.append(f"📊 Low frequency: {posts_per_day:.1f} posts/day. Opportunity to post more consistently.")

        # Content type insights
        content_types = patterns.get("content_types", {})
        if content_types.get("with_media", 0) > content_types.get("text_only", 0):
            insights.append("📸 Heavy use of media. Visual content is their strength.")

        if content_types.get("threads", 0) > 5:
            insights.append("🧵 Frequently uses threads. Consider thread-based content.")

        # Engagement insights
        avg_engagement = metrics.get("avg_engagement", 0)
        if avg_engagement > 100:
            insights.append(f"💪 Strong engagement ({avg_engagement:.0f} avg). Study their top performers.")

        return insights

    async def gap_analysis(
        self,
        competitors: List[str],
        your_topics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Identify content gaps - topics competitors aren't covering.

        Args:
            competitors: List of competitor usernames
            your_topics: Your existing topics (optional)

        Returns:
            List of content gap opportunities
        """
        logger.info(f"Analyzing content gaps across {len(competitors)} competitors...")

        # Analyze all competitors
        all_topics = []
        for username in competitors:
            analysis = await self.analyze_competitor_strategy(username, depth="quick")
            topics = analysis.get("topics", [])
            all_topics.extend(topics)

        # Find common topics
        topic_counts = Counter(all_topics)

        # Identify gaps (topics not heavily covered)
        gaps = []

        # Get industry-standard topics (could be from a predefined list or API)
        industry_topics = [
            "AI", "machine learning", "productivity", "remote work",
            "automation", "startups", "coding", "data science",
            "career advice", "tech news", "tools", "tutorials"
        ]

        for topic in industry_topics:
            coverage = sum(1 for t in all_topics if topic.lower() in t.lower())

            if coverage < len(competitors) * 0.3:  # Less than 30% coverage
                # This is a gap!
                opportunity_score = (1 - (coverage / len(competitors))) * 100

                gap = {
                    "topic": topic,
                    "competitor_coverage": coverage,
                    "total_competitors": len(competitors),
                    "opportunity_score": opportunity_score,
                    "why_gap": f"Only {coverage}/{len(competitors)} competitors actively discussing this",
                    "suggested_angle": f"Position yourself as the go-to for {topic}"
                }

                gaps.append(gap)

                # Save to database
                content_gap = ContentGap(
                    topic=topic,
                    discovered_at=datetime.now(),
                    opportunity_score=opportunity_score,
                    competitor_coverage=coverage,
                    why_gap=gap["why_gap"],
                    suggested_angle=gap["suggested_angle"]
                )
                self.session.add(content_gap)

        self.session.commit()

        # Sort by opportunity score
        gaps.sort(key=lambda x: x["opportunity_score"], reverse=True)

        logger.info(f"Identified {len(gaps)} content gaps")
        return gaps

    async def content_differentiation(
        self,
        their_tweet: str,
        your_style: str = "professional yet conversational"
    ) -> str:
        """
        Take competitor's topic and create differentiated content.

        Args:
            their_tweet: Competitor's tweet
            your_style: Your desired tone/style

        Returns:
            Differentiated tweet
        """
        prompt = f"""A competitor posted this tweet:
"{their_tweet}"

Create a differentiated tweet on the same topic but with:
- A unique angle or perspective
- {your_style} tone
- Adds more value or insight
- Stands out from the original

Return ONLY the tweet text (max 280 characters)."""

        result = await self.claude_client.generate_async(
            prompt=prompt,
            system="You are an expert content strategist.",
            max_tokens=300,
            temperature=0.8
        )

        return result.content.strip().strip('"')

    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == "__main__":
    import os
    from backend.core.config import get_config

    config = get_config()

    # Initialize components
    twitter_client = TwitterClient(
        api_key=os.getenv("TWITTER_API_KEY"),
        api_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_secret=os.getenv("TWITTER_ACCESS_SECRET")
    )

    claude_client = ClaudeClient(api_key=config.api_keys.anthropic_api_key)

    intel = CompetitorIntelligence(
        twitter_client=twitter_client,
        claude_client=claude_client
    )

    async def test():
        # Analyze a competitor
        report = await intel.analyze_competitor_strategy("competitor_username")

        print("Competitor Analysis:")
        print(f"  Posts/day: {report['patterns']['posts_per_day']}")
        print(f"  Avg engagement: {report['metrics']['avg_engagement']:.0f}")
        print(f"\nTop topics: {', '.join(report['topics'][:5])}")
        print(f"\nInsights:")
        for insight in report['insights']:
            print(f"  - {insight}")

        # Gap analysis
        gaps = await intel.gap_analysis(["comp1", "comp2", "comp3"])
        print(f"\nContent Gaps:")
        for gap in gaps[:5]:
            print(f"  - {gap['topic']} (score: {gap['opportunity_score']:.1f})")

    # asyncio.run(test())
    print("Competitor intelligence ready!")
