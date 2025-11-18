"""
Tweet Scorer

Scores tweets before posting to predict performance.
"""

from typing import Dict, Any, List
import re
from datetime import datetime
from loguru import logger

from backend.models.database import get_db_session, Tweet


class TweetScorer:
    """
    Scores tweets based on multiple factors to predict engagement.
    """

    def __init__(self):
        """Initialize tweet scorer."""
        self.session = get_db_session()
        logger.info("TweetScorer initialized")

    def score_tweet(
        self,
        tweet_text: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive tweet scoring.

        Args:
            tweet_text: Tweet content
            metadata: Optional metadata (category, has_media, etc.)

        Returns:
            Dict with score and breakdown
        """
        if metadata is None:
            metadata = {}

        scores = {
            "total": 0,
            "breakdown": {},
            "grade": "",
            "recommendations": []
        }

        # Length score (0-15 points)
        length_score, length_rec = self._score_length(tweet_text)
        scores["breakdown"]["length"] = length_score
        scores["total"] += length_score
        if length_rec:
            scores["recommendations"].append(length_rec)

        # Structure score (0-20 points)
        structure_score, structure_rec = self._score_structure(tweet_text)
        scores["breakdown"]["structure"] = structure_score
        scores["total"] += structure_score
        scores["recommendations"].extend(structure_rec)

        # Hashtag score (0-10 points)
        hashtag_score, hashtag_rec = self._score_hashtags(tweet_text, metadata)
        scores["breakdown"]["hashtags"] = hashtag_score
        scores["total"] += hashtag_score
        if hashtag_rec:
            scores["recommendations"].append(hashtag_rec)

        # Media score (0-15 points)
        media_score, media_rec = self._score_media(metadata)
        scores["breakdown"]["media"] = media_score
        scores["total"] += media_score
        if media_rec:
            scores["recommendations"].append(media_rec)

        # Engagement triggers (0-20 points)
        engagement_score, engagement_rec = self._score_engagement_triggers(tweet_text)
        scores["breakdown"]["engagement"] = engagement_score
        scores["total"] += engagement_score
        scores["recommendations"].extend(engagement_rec)

        # Historical similarity (0-20 points)
        similarity_score = self._score_historical_similarity(tweet_text)
        scores["breakdown"]["similarity"] = similarity_score
        scores["total"] += similarity_score

        # Assign grade
        total = scores["total"]
        if total >= 80:
            scores["grade"] = "A"
        elif total >= 70:
            scores["grade"] = "B"
        elif total >= 60:
            scores["grade"] = "C"
        elif total >= 50:
            scores["grade"] = "D"
        else:
            scores["grade"] = "F"

        logger.debug(f"Tweet scored: {total}/100 (Grade {scores['grade']})")

        return scores

    def _score_length(self, text: str) -> tuple:
        """Score based on tweet length."""
        char_count = len(text)
        word_count = len(text.split())

        # Optimal: 150-200 characters, 15-25 words
        score = 0
        recommendation = None

        if 150 <= char_count <= 200:
            score = 15
        elif 100 <= char_count <= 250:
            score = 10
        elif char_count < 100:
            score = 5
            recommendation = "Tweet is too short. Add more context."
        else:
            score = 8

        if word_count < 10:
            recommendation = "Tweet is too brief. Aim for 15-25 words."
        elif word_count > 35:
            recommendation = "Tweet might be too long. Consider breaking into thread."

        return score, recommendation

    def _score_structure(self, text: str) -> tuple:
        """Score content structure."""
        score = 0
        recommendations = []

        # Has question
        if '?' in text:
            score += 7
        else:
            recommendations.append("Consider adding a question to boost engagement")

        # Has numbers/stats
        if any(char.isdigit() for char in text):
            score += 5

        # Has emoji (but not too many)
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map
            u"\U0001F1E0-\U0001F1FF"  # flags
            "]+", flags=re.UNICODE)
        emojis = emoji_pattern.findall(text)

        if 1 <= len(emojis) <= 3:
            score += 3
        elif len(emojis) > 5:
            score -= 2
            recommendations.append("Too many emojis. Keep it to 1-3.")

        # Line breaks (improves readability)
        if '\n' in text:
            score += 3

        # Starts strong
        first_word = text.split()[0] if text.split() else ""
        power_words = ['New', 'Breaking', 'Exclusive', 'Just', 'Today', 'Now', 'Important']
        if first_word in power_words:
            score += 2

        return score, recommendations

    def _score_hashtags(self, text: str, metadata: Dict) -> tuple:
        """Score hashtag usage."""
        hashtags = re.findall(r'#\w+', text)

        if metadata.get('hashtags'):
            hashtags = metadata['hashtags']

        num_hashtags = len(hashtags)

        if num_hashtags == 0:
            return 8, None  # No hashtags is okay
        elif num_hashtags == 1 or num_hashtags == 2:
            return 10, None  # Optimal
        elif num_hashtags == 3:
            return 7, "2 hashtags is optimal"
        else:
            return 3, "Too many hashtags. Stick to 1-2."

    def _score_media(self, metadata: Dict) -> tuple:
        """Score media inclusion."""
        has_media = metadata.get('has_media', False)

        if has_media:
            return 15, None
        else:
            return 0, "Consider adding an image or video for 3x more engagement"

    def _score_engagement_triggers(self, text: str) -> tuple:
        """Score engagement-driving elements."""
        score = 0
        recommendations = []

        text_lower = text.lower()

        # Call to action
        cta_words = ['check out', 'read', 'learn', 'discover', 'try', 'join',
                     'follow', 'share', 'comment', 'thoughts', 'agree', 'take']
        has_cta = any(word in text_lower for word in cta_words)

        if has_cta:
            score += 7
        else:
            recommendations.append("Add a call-to-action (e.g., 'What do you think?')")

        # Asks for opinion
        opinion_words = ['think', 'thoughts', 'opinion', 'take', 'agree', 'disagree']
        if any(word in text_lower for word in opinion_words):
            score += 5

        # Has controversy/debate potential
        debate_words = ['controversial', 'unpopular', 'hot take', 'debate']
        if any(word in text_lower for word in debate_words):
            score += 3

        # Value proposition (teaches/shares)
        value_words = ['how to', 'tips', 'learn', 'improve', 'better', 'best']
        if any(word in text_lower for word in value_words):
            score += 5

        return score, recommendations

    def _score_historical_similarity(self, text: str) -> float:
        """Score based on similarity to top performers."""
        # Get top 10 performing tweets
        top_tweets = self.session.query(Tweet).filter(
            Tweet.engagement_rate > 0.05  # 5% engagement rate
        ).order_by(
            Tweet.engagement_rate.desc()
        ).limit(10).all()

        if not top_tweets:
            return 10  # Default score

        # Simple similarity: count common words
        text_words = set(text.lower().split())
        max_similarity = 0

        for top_tweet in top_tweets:
            top_words = set(top_tweet.content.lower().split())
            common = len(text_words & top_words)
            total = len(text_words | top_words)
            similarity = common / total if total > 0 else 0
            max_similarity = max(max_similarity, similarity)

        # Convert similarity to score (0-20)
        return max_similarity * 20

    def compare_tweets(self, tweet1: str, tweet2: str) -> Dict[str, Any]:
        """
        Compare two tweets and recommend the better one.

        Args:
            tweet1: First tweet
            tweet2: Second tweet

        Returns:
            Comparison results
        """
        score1 = self.score_tweet(tweet1)
        score2 = self.score_tweet(tweet2)

        winner = 1 if score1["total"] > score2["total"] else 2
        margin = abs(score1["total"] - score2["total"])

        return {
            "winner": winner,
            "margin": margin,
            "confidence": "high" if margin > 15 else "medium" if margin > 5 else "low",
            "tweet1_score": score1,
            "tweet2_score": score2,
            "recommendation": f"Tweet {winner} is likely to perform better" if margin > 5
                            else "Both tweets are comparable"
        }

    def batch_score(self, tweets: List[str]) -> List[Dict[str, Any]]:
        """
        Score multiple tweets at once.

        Args:
            tweets: List of tweet texts

        Returns:
            List of score dicts, sorted by score
        """
        scored = []

        for i, tweet in enumerate(tweets):
            score = self.score_tweet(tweet)
            score["index"] = i
            score["content"] = tweet
            scored.append(score)

        # Sort by total score
        scored.sort(key=lambda x: x["total"], reverse=True)

        return scored

    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == "__main__":
    # Test scorer
    scorer = TweetScorer()

    # Test tweet
    tweet = "🚀 Just discovered an amazing way to boost productivity with AI. What's your favorite AI tool? #AI #Productivity"

    score = scorer.score_tweet(
        tweet,
        metadata={"has_media": True, "category": "AI"}
    )

    print(f"Tweet: {tweet}\n")
    print(f"Total Score: {score['total']}/100 (Grade {score['grade']})")
    print(f"\nBreakdown:")
    for component, points in score['breakdown'].items():
        print(f"  {component}: {points}")

    print(f"\nRecommendations:")
    for rec in score['recommendations']:
        print(f"  - {rec}")

    # Compare tweets
    tweet1 = "AI is amazing"
    tweet2 = "Just tried the new AI tool. Game changer! What's everyone using for automation? 🤖"

    comparison = scorer.compare_tweets(tweet1, tweet2)
    print(f"\n\nComparison:")
    print(f"Winner: Tweet {comparison['winner']}")
    print(f"Confidence: {comparison['confidence']}")
    print(f"Tweet 1: {comparison['tweet1_score']['total']}/100")
    print(f"Tweet 2: {comparison['tweet2_score']['total']}/100")

    scorer.close()
