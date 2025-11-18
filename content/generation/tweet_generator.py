"""
Tweet Generator

Generates tweets using RAG-augmented Claude API calls.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from integrations.claude.client import ClaudeClient, GenerationResult
from rag.retrieval.retriever import ContentRetriever


@dataclass
class TweetIdea:
    """Container for a generated tweet idea."""
    content: str
    rationale: str
    confidence: float
    hashtags: List[str]
    category: str
    optimal_time: Optional[str] = None
    metadata: Dict[str, Any] = None


class TweetGenerator:
    """
    Generates tweet ideas using RAG and Claude API.

    Features:
    - RAG-augmented generation
    - Style matching from past tweets
    - Multiple variations per topic
    - Hashtag and mention suggestions
    - Optimal timing recommendations
    """

    def __init__(
        self,
        claude_client: ClaudeClient,
        content_retriever: ContentRetriever,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize tweet generator.

        Args:
            claude_client: Claude API client
            content_retriever: RAG content retriever
            config: Configuration dictionary
        """
        self.claude_client = claude_client
        self.content_retriever = content_retriever
        self.config = config or {}

        # Default configuration
        self.max_length = self.config.get('max_length', 280)
        self.preferred_length = self.config.get('preferred_length', (150, 200))
        self.use_hashtags = self.config.get('use_hashtags', True)
        self.max_hashtags = self.config.get('max_hashtags', 2)
        self.tone = self.config.get('tone', 'professional yet conversational')

        logger.info("TweetGenerator initialized")

    def generate_tweet_ideas(
        self,
        topic: str,
        num_ideas: int = 5,
        context_query: Optional[str] = None
    ) -> List[TweetIdea]:
        """
        Generate multiple tweet ideas on a topic.

        Args:
            topic: Topic to generate tweets about
            num_ideas: Number of tweet ideas to generate
            context_query: Optional custom query for context retrieval

        Returns:
            List of TweetIdea objects
        """
        logger.info(f"Generating {num_ideas} tweet ideas for topic: {topic}")

        # Retrieve relevant context from knowledge base
        query = context_query or f"tweets and content about {topic}"
        context = self.content_retriever.retrieve_for_context(
            query=query,
            max_tokens=2000,
            top_k=10
        )

        # Build system prompt
        system_prompt = self._build_system_prompt()

        # Build user prompt
        user_prompt = f"""Generate {num_ideas} different tweet ideas about: {topic}

Requirements:
- Each tweet must be under {self.max_length} characters
- Preferred length: {self.preferred_length[0]}-{self.preferred_length[1]} characters
- Tone: {self.tone}
- Include relevant hashtags (max {self.max_hashtags})
- Make each tweet unique and engaging
- Match the style of the context examples

Format your response as a JSON array with this structure:
[
  {{
    "content": "The tweet text here",
    "rationale": "Why this tweet works",
    "confidence": 0.85,
    "hashtags": ["AI", "Tech"],
    "category": "educational/entertaining/thought-provoking"
  }}
]

IMPORTANT: Respond ONLY with valid JSON, no additional text."""

        try:
            # Generate with context
            result = self.claude_client.generate_with_context(
                prompt=user_prompt,
                context=context,
                system=system_prompt,
                max_tokens=2000,
                temperature=0.8
            )

            # Parse response
            tweet_ideas = self._parse_tweet_response(result.content)

            logger.info(f"Successfully generated {len(tweet_ideas)} tweet ideas")
            return tweet_ideas

        except Exception as e:
            logger.error(f"Error generating tweet ideas: {e}")
            raise

    async def generate_tweet_ideas_async(
        self,
        topic: str,
        num_ideas: int = 5,
        context_query: Optional[str] = None
    ) -> List[TweetIdea]:
        """Async version of generate_tweet_ideas()."""
        logger.info(f"Generating {num_ideas} tweet ideas for topic: {topic}")

        # Retrieve relevant context
        query = context_query or f"tweets and content about {topic}"
        context = self.content_retriever.retrieve_for_context(
            query=query,
            max_tokens=2000,
            top_k=10
        )

        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = f"""Generate {num_ideas} different tweet ideas about: {topic}

Requirements:
- Each tweet must be under {self.max_length} characters
- Preferred length: {self.preferred_length[0]}-{self.preferred_length[1]} characters
- Tone: {self.tone}
- Include relevant hashtags (max {self.max_hashtags})
- Make each tweet unique and engaging
- Match the style of the context examples

Format your response as a JSON array with this structure:
[
  {{
    "content": "The tweet text here",
    "rationale": "Why this tweet works",
    "confidence": 0.85,
    "hashtags": ["AI", "Tech"],
    "category": "educational/entertaining/thought-provoking"
  }}
]

IMPORTANT: Respond ONLY with valid JSON, no additional text."""

        try:
            # Generate with context
            result = await self.claude_client.generate_with_context_async(
                prompt=user_prompt,
                context=context,
                system=system_prompt,
                max_tokens=2000,
                temperature=0.8
            )

            # Parse response
            tweet_ideas = self._parse_tweet_response(result.content)

            logger.info(f"Successfully generated {len(tweet_ideas)} tweet ideas")
            return tweet_ideas

        except Exception as e:
            logger.error(f"Error generating tweet ideas: {e}")
            raise

    def generate_variations(
        self,
        original_tweet: str,
        num_variations: int = 3
    ) -> List[str]:
        """
        Generate variations of a tweet.

        Args:
            original_tweet: Original tweet text
            num_variations: Number of variations to generate

        Returns:
            List of tweet variations
        """
        system_prompt = self._build_system_prompt()

        user_prompt = f"""Generate {num_variations} variations of this tweet:

"{original_tweet}"

Requirements:
- Keep the core message the same
- Vary the wording and structure
- Each must be under {self.max_length} characters
- Maintain the same tone

Return as a JSON array of strings:
["variation 1", "variation 2", "variation 3"]"""

        try:
            result = self.claude_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.9
            )

            # Parse JSON response
            import json
            variations = json.loads(result.content.strip())

            return variations

        except Exception as e:
            logger.error(f"Error generating variations: {e}")
            raise

    def improve_tweet(
        self,
        tweet: str,
        feedback: str
    ) -> str:
        """
        Improve a tweet based on feedback.

        Args:
            tweet: Original tweet
            feedback: Improvement feedback

        Returns:
            Improved tweet
        """
        system_prompt = self._build_system_prompt()

        user_prompt = f"""Improve this tweet based on the feedback:

Original tweet: "{tweet}"

Feedback: {feedback}

Return ONLY the improved tweet text, nothing else. Keep it under {self.max_length} characters."""

        try:
            result = self.claude_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.7
            )

            improved_tweet = result.content.strip().strip('"')
            return improved_tweet

        except Exception as e:
            logger.error(f"Error improving tweet: {e}")
            raise

    def generate_from_article(
        self,
        article_text: str,
        article_url: Optional[str] = None,
        num_tweets: int = 3
    ) -> List[TweetIdea]:
        """
        Generate tweet ideas from an article.

        Args:
            article_text: Article content
            article_url: Optional article URL
            num_tweets: Number of tweets to generate

        Returns:
            List of TweetIdea objects
        """
        system_prompt = self._build_system_prompt()

        user_prompt = f"""Read this article and generate {num_tweets} engaging tweets about it:

{article_text[:2000]}  # Limit article length

Requirements:
- Extract the most interesting insights
- Each tweet should highlight a different angle
- Under {self.max_length} characters each
- Engaging and thought-provoking
{f'- Include link: {article_url}' if article_url else ''}

Format as JSON array:
[
  {{
    "content": "tweet text",
    "rationale": "why this angle is interesting",
    "confidence": 0.85,
    "hashtags": ["relevant", "hashtags"],
    "category": "type"
  }}
]"""

        try:
            result = self.claude_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                max_tokens=1500,
                temperature=0.8
            )

            tweet_ideas = self._parse_tweet_response(result.content)

            # Add article URL to metadata
            for idea in tweet_ideas:
                if idea.metadata is None:
                    idea.metadata = {}
                idea.metadata['source_url'] = article_url

            return tweet_ideas

        except Exception as e:
            logger.error(f"Error generating tweets from article: {e}")
            raise

    def generate_thread(
        self,
        topic: str,
        num_tweets: int = 5
    ) -> List[str]:
        """
        Generate a Twitter thread.

        Args:
            topic: Thread topic
            num_tweets: Number of tweets in thread

        Returns:
            List of tweets forming a thread
        """
        # Retrieve context
        context = self.content_retriever.retrieve_for_context(
            query=f"detailed content about {topic}",
            max_tokens=3000,
            top_k=15
        )

        system_prompt = self._build_system_prompt()

        user_prompt = f"""Create a {num_tweets}-tweet thread about: {topic}

Requirements:
- First tweet should hook the reader
- Each tweet builds on the previous one
- Last tweet should have a strong conclusion
- Each tweet under {self.max_length} characters
- Cohesive narrative throughout
- Use "1/" "2/" etc. numbering

Return as JSON array of strings:
["1/ First tweet...", "2/ Second tweet...", ...]"""

        try:
            result = self.claude_client.generate_with_context(
                prompt=user_prompt,
                context=context,
                system=system_prompt,
                max_tokens=2000,
                temperature=0.7
            )

            # Parse JSON
            import json
            thread = json.loads(result.content.strip())

            return thread

        except Exception as e:
            logger.error(f"Error generating thread: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """Build system prompt for Claude."""
        return f"""You are an expert social media content creator specializing in X (Twitter).

Your writing style:
- Tone: {self.tone}
- Clear, concise, and engaging
- Authentic and valuable
- No clickbait or excessive hype
- Focus on insights and actionable content

Guidelines:
- Maximum {self.max_length} characters per tweet
- Use line breaks for readability
- Include relevant hashtags when appropriate
- Be specific and concrete
- Add value to the reader

You have access to the user's past successful tweets and content as context. Match their unique voice and style."""

    def _parse_tweet_response(self, response: str) -> List[TweetIdea]:
        """Parse Claude's JSON response into TweetIdea objects."""
        import json

        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON array directly
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response

            # Parse JSON
            ideas_data = json.loads(json_str)

            # Convert to TweetIdea objects
            tweet_ideas = []
            for idea in ideas_data:
                tweet_ideas.append(TweetIdea(
                    content=idea.get('content', ''),
                    rationale=idea.get('rationale', ''),
                    confidence=idea.get('confidence', 0.7),
                    hashtags=idea.get('hashtags', []),
                    category=idea.get('category', 'general'),
                    metadata=idea.get('metadata', {})
                ))

            return tweet_ideas

        except Exception as e:
            logger.error(f"Error parsing tweet response: {e}")
            logger.debug(f"Response was: {response}")
            raise ValueError(f"Failed to parse tweet response: {e}")

    def __repr__(self) -> str:
        return f"TweetGenerator(max_length={self.max_length}, tone={self.tone})"


if __name__ == "__main__":
    # Test the tweet generator
    import os
    from rag.vectorstore.chroma_store import ChromaStore
    from rag.embeddings.generator import EmbeddingGenerator
    from rag.retrieval.retriever import ContentRetriever

    # Initialize components
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        exit(1)

    claude_client = ClaudeClient(api_key=api_key)

    generator_emb = EmbeddingGenerator()
    store = ChromaStore(
        persist_directory="./test_chroma",
        collection_name="test_tweets"
    )

    # Add some example tweets to the knowledge base
    example_tweets = [
        "AI is revolutionizing how we create content. The future is here.",
        "Machine learning enables personalized experiences at scale.",
        "Building with Python: fast, flexible, and powerful."
    ]
    store.add_documents(
        example_tweets,
        metadatas=[{"type": "tweet", "category": "AI"} for _ in example_tweets]
    )

    retriever = ContentRetriever(
        vector_store=store,
        embedding_generator=generator_emb
    )

    # Initialize tweet generator
    tweet_gen = TweetGenerator(
        claude_client=claude_client,
        content_retriever=retriever,
        config={
            'max_length': 280,
            'tone': 'professional yet conversational'
        }
    )

    # Generate tweet ideas
    print("Generating tweet ideas about AI...")
    ideas = tweet_gen.generate_tweet_ideas(
        topic="AI and productivity",
        num_ideas=3
    )

    for i, idea in enumerate(ideas, 1):
        print(f"\n{i}. {idea.content}")
        print(f"   Category: {idea.category}")
        print(f"   Confidence: {idea.confidence}")
        print(f"   Hashtags: {', '.join(idea.hashtags)}")

    # Cleanup
    store.delete_collection()
