"""
Engagement Bot

Automates engagement activities (replies, likes, relationship building).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from loguru import logger

from integrations.twitter.client import TwitterClient
from integrations.claude.client import ClaudeClient
from rag.retrieval.retriever import ContentRetriever
from backend.models.database import get_db_session, EngagementInteraction


class SafetyFilter:
    """Filter sensitive topics that require human review."""

    SENSITIVE_TOPICS = [
        "politics", "political", "election", "controversy",
        "religion", "religious", "war", "conflict",
        "death", "tragedy", "disaster"
    ]

    @staticmethod
    def requires_human_review(content: str) -> bool:
        """Check if content needs manual review."""
        content_lower = content.lower()
        return any(topic in content_lower for topic in SafetyFilter.SENSITIVE_TOPICS)

    @staticmethod
    def is_spam(content: str) -> bool:
        """Detect potential spam."""
        spam_indicators = [
            "buy now", "click here", "limited time",
            "guarantee", "winner", "prize"
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in spam_indicators)


class EngagementBot:
    """
    Smart engagement automation with AI-powered responses.

    Features:
    - Auto-reply to mentions
    - Engage with relevant conversations
    - Relationship building with key accounts
    - Safety filters for sensitive content
    """

    def __init__(
        self,
        twitter_client: TwitterClient,
        claude_client: ClaudeClient,
        content_retriever: Optional[ContentRetriever] = None,
        auto_post: bool = False
    ):
        """
        Initialize engagement bot.

        Args:
            twitter_client: Twitter API client
            claude_client: Claude API client
            content_retriever: RAG retriever for context
            auto_post: Whether to auto-post or require approval
        """
        self.twitter_client = twitter_client
        self.claude_client = claude_client
        self.content_retriever = content_retriever
        self.auto_post = auto_post
        self.session = get_db_session()

        logger.info(f"EngagementBot initialized (auto_post={auto_post})")

    async def auto_reply_to_mentions(
        self,
        since_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Auto-reply to recent mentions.

        Args:
            since_minutes: Check mentions from last N minutes

        Returns:
            List of replies generated
        """
        logger.info(f"Checking mentions from last {since_minutes} minutes...")

        replies_generated = []

        try:
            # Get recent mentions (would use Twitter API search)
            # For now, simulating with search
            mentions = self.twitter_client.search_tweets(
                query="@your_username",
                limit=10,
                recent=True
            )

            for mention in mentions:
                # Check if we already replied
                existing = self.session.query(EngagementInteraction).filter(
                    EngagementInteraction.target_tweet_id == mention.id
                ).first()

                if existing:
                    continue  # Skip if already replied

                # Safety check
                if SafetyFilter.requires_human_review(mention.text):
                    logger.warning(f"Mention requires human review: {mention.text[:50]}")
                    self._save_interaction(
                        interaction_type="mention_flagged",
                        target_tweet_id=mention.id,
                        target_username=mention.author_id,
                        was_automated=False,
                        required_approval=True
                    )
                    continue

                if SafetyFilter.is_spam(mention.text):
                    logger.info("Detected spam mention, skipping")
                    continue

                # Generate reply
                reply_text = await self._generate_reply(mention.text)

                if reply_text:
                    result = {
                        "mention_id": mention.id,
                        "mention_text": mention.text,
                        "reply_text": reply_text,
                        "posted": False
                    }

                    # Post if auto_post enabled
                    if self.auto_post:
                        try:
                            posted_tweet = self.twitter_client.post_tweet(
                                text=reply_text,
                                reply_to=mention.id
                            )
                            result["posted"] = True
                            result["reply_id"] = posted_tweet.id

                            logger.info(f"Posted auto-reply to {mention.id}")

                        except Exception as e:
                            logger.error(f"Error posting reply: {e}")

                    # Save interaction
                    self._save_interaction(
                        interaction_type="reply",
                        target_tweet_id=mention.id,
                        target_username=mention.author_id,
                        our_content=reply_text,
                        was_automated=True,
                        required_approval=not self.auto_post
                    )

                    replies_generated.append(result)

        except Exception as e:
            logger.error(f"Error processing mentions: {e}")

        logger.info(f"Generated {len(replies_generated)} replies")
        return replies_generated

    async def _generate_reply(
        self,
        mention_text: str,
        max_length: int = 280
    ) -> str:
        """
        Generate AI reply to a mention.

        Args:
            mention_text: The mention/tweet to reply to
            max_length: Max reply length

        Returns:
            Reply text
        """
        # Get relevant context from knowledge base
        context = ""
        if self.content_retriever:
            context = self.content_retriever.retrieve_for_context(
                query=mention_text,
                max_tokens=500,
                top_k=3
            )

        prompt = f"""Generate a helpful, friendly reply to this mention:

"{mention_text}"

{"Context from knowledge base:" + context if context else ""}

Requirements:
- Be helpful and authentic
- Under {max_length} characters
- Professional yet conversational tone
- Add value to the conversation
- Don't be overly promotional

Return ONLY the reply text."""

        try:
            result = await self.claude_client.generate_async(
                prompt=prompt,
                system="You are a helpful social media assistant. Be authentic and valuable.",
                max_tokens=200,
                temperature=0.7
            )

            reply = result.content.strip().strip('"')

            # Ensure within length limit
            if len(reply) > max_length:
                reply = reply[:max_length-3] + "..."

            return reply

        except Exception as e:
            logger.error(f"Error generating reply: {e}")
            return ""

    async def engage_with_relevant_conversations(
        self,
        keywords: List[str],
        max_engagements: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find and engage with relevant conversations.

        Args:
            keywords: Topics to monitor
            max_engagements: Max number of tweets to engage with

        Returns:
            List of engagements
        """
        logger.info(f"Finding conversations about: {', '.join(keywords)}")

        engagements = []

        for keyword in keywords:
            try:
                # Search for relevant tweets
                tweets = self.twitter_client.search_tweets(
                    query=keyword,
                    limit=max_engagements * 2  # Get extra to filter
                )

                for tweet in tweets[:max_engagements]:
                    # Check if worth engaging
                    if not self._should_engage(tweet):
                        continue

                    # Generate reply
                    reply_text = await self._generate_reply(tweet.text)

                    if reply_text:
                        engagement = {
                            "tweet_id": tweet.id,
                            "author": tweet.author_id,
                            "tweet_text": tweet.text,
                            "reply_text": reply_text,
                            "keyword": keyword,
                            "posted": False
                        }

                        # Post if auto_post
                        if self.auto_post:
                            try:
                                posted = self.twitter_client.post_tweet(
                                    text=reply_text,
                                    reply_to=tweet.id
                                )
                                engagement["posted"] = True
                                engagement["reply_id"] = posted.id

                            except Exception as e:
                                logger.error(f"Error posting engagement: {e}")

                        # Save interaction
                        self._save_interaction(
                            interaction_type="engagement",
                            target_tweet_id=tweet.id,
                            target_username=tweet.author_id,
                            our_content=reply_text,
                            was_automated=True
                        )

                        engagements.append(engagement)

            except Exception as e:
                logger.error(f"Error engaging with {keyword}: {e}")

        logger.info(f"Engaged with {len(engagements)} conversations")
        return engagements

    def _should_engage(self, tweet: Any) -> bool:
        """Determine if tweet is worth engaging with."""
        # Skip if:
        # - Too old
        created_at = datetime.fromisoformat(tweet.created_at)
        if datetime.now() - created_at > timedelta(hours=24):
            return False

        # - Too short
        if len(tweet.text.split()) < 5:
            return False

        # - Spam
        if SafetyFilter.is_spam(tweet.text):
            return False

        # - Sensitive
        if SafetyFilter.requires_human_review(tweet.text):
            return False

        # Good indicators:
        # - Has question
        if '?' in tweet.text:
            return True

        # - Moderate engagement (not viral, not dead)
        total_engagement = (
            tweet.metrics.get('like_count', 0) +
            tweet.metrics.get('retweet_count', 0) +
            tweet.metrics.get('reply_count', 0)
        )

        return 5 < total_engagement < 1000

    async def relationship_management(
        self,
        key_accounts: List[str],
        engagement_frequency: str = "daily"
    ) -> Dict[str, Any]:
        """
        Build relationships with key accounts.

        Args:
            key_accounts: List of important usernames
            engagement_frequency: How often to engage (daily, weekly)

        Returns:
            Engagement summary
        """
        logger.info(f"Managing relationships with {len(key_accounts)} accounts...")

        summary = {
            "accounts_checked": 0,
            "engagements": 0,
            "actions": []
        }

        for username in key_accounts:
            try:
                # Get their recent tweets
                tweets = self.twitter_client.get_user_tweets(
                    username=username,
                    limit=5
                )

                # Check if we've engaged recently
                recent_interactions = self.session.query(EngagementInteraction).filter(
                    EngagementInteraction.target_username == username,
                    EngagementInteraction.timestamp >= datetime.now() - timedelta(days=1)
                ).count()

                if recent_interactions > 0:
                    logger.debug(f"Already engaged with @{username} recently")
                    continue

                # Engage with their top tweet
                if tweets:
                    top_tweet = max(tweets, key=lambda t: t.metrics.get('like_count', 0))

                    # Like the tweet
                    action = {
                        "account": username,
                        "action": "like",
                        "tweet_id": top_tweet.id
                    }

                    # Could also add a thoughtful reply
                    if '?' in top_tweet.text:  # If they asked a question
                        reply = await self._generate_reply(top_tweet.text)
                        action["reply"] = reply

                        if self.auto_post:
                            self.twitter_client.post_tweet(
                                text=reply,
                                reply_to=top_tweet.id
                            )
                            action["reply_posted"] = True

                    summary["actions"].append(action)
                    summary["engagements"] += 1

                    # Save interaction
                    self._save_interaction(
                        interaction_type="relationship",
                        target_username=username,
                        target_tweet_id=top_tweet.id,
                        was_automated=True
                    )

                summary["accounts_checked"] += 1

            except Exception as e:
                logger.error(f"Error managing relationship with @{username}: {e}")

        logger.info(f"Relationship management: {summary['engagements']} engagements")
        return summary

    def _save_interaction(
        self,
        interaction_type: str,
        target_tweet_id: Optional[str] = None,
        target_username: Optional[str] = None,
        our_content: Optional[str] = None,
        was_automated: bool = False,
        required_approval: bool = False
    ):
        """Save engagement interaction to database."""
        interaction = EngagementInteraction(
            interaction_type=interaction_type,
            target_tweet_id=target_tweet_id,
            target_username=target_username,
            our_content=our_content,
            was_automated=was_automated,
            required_approval=required_approval,
            timestamp=datetime.now()
        )

        self.session.add(interaction)
        self.session.commit()

    def get_engagement_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get engagement statistics."""
        since = datetime.now() - timedelta(days=days)

        total = self.session.query(EngagementInteraction).filter(
            EngagementInteraction.timestamp >= since
        ).count()

        by_type = {}
        types = ["reply", "like", "retweet", "engagement", "relationship"]

        for interaction_type in types:
            count = self.session.query(EngagementInteraction).filter(
                EngagementInteraction.interaction_type == interaction_type,
                EngagementInteraction.timestamp >= since
            ).count()
            by_type[interaction_type] = count

        return {
            "period_days": days,
            "total_interactions": total,
            "by_type": by_type,
            "automated_percentage": self._calculate_automation_rate(since)
        }

    def _calculate_automation_rate(self, since: datetime) -> float:
        """Calculate what % of engagements were automated."""
        total = self.session.query(EngagementInteraction).filter(
            EngagementInteraction.timestamp >= since
        ).count()

        if total == 0:
            return 0.0

        automated = self.session.query(EngagementInteraction).filter(
            EngagementInteraction.timestamp >= since,
            EngagementInteraction.was_automated == True
        ).count()

        return (automated / total) * 100

    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == "__main__":
    print("Engagement bot ready!")
    print("Features: auto-replies, conversation engagement, relationship management")
