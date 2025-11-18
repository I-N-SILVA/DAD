"""
Morning Briefing Workflow

Scrapes news, analyzes trends, and generates tweet ideas for the morning.
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

from integrations.scraping.news_scraper import NewsScraper, NewsArticle
from integrations.twitter.client import TwitterClient
from integrations.claude.client import ClaudeClient
from content.generation.tweet_generator import TweetGenerator, TweetIdea
from rag.indexing.indexer import DocumentIndexer, Document
from rag.retrieval.retriever import ContentRetriever
from backend.core.config import get_config


class MorningBriefingWorkflow:
    """
    Morning content briefing workflow.

    Steps:
    1. Scrape top tech news from configured sources
    2. Get trending topics on X/Twitter
    3. Index new content in knowledge base
    4. Generate tweet ideas based on news and trends
    5. Return briefing summary
    """

    def __init__(
        self,
        news_scraper: NewsScraper,
        twitter_client: TwitterClient,
        tweet_generator: TweetGenerator,
        document_indexer: DocumentIndexer,
        content_retriever: ContentRetriever
    ):
        """
        Initialize morning briefing workflow.

        Args:
            news_scraper: News scraper instance
            twitter_client: Twitter API client
            tweet_generator: Tweet generator
            document_indexer: Document indexer
            content_retriever: Content retriever
        """
        self.news_scraper = news_scraper
        self.twitter_client = twitter_client
        self.tweet_generator = tweet_generator
        self.document_indexer = document_indexer
        self.content_retriever = content_retriever

        self.config = get_config()

        logger.info("MorningBriefingWorkflow initialized")

    async def run(self) -> Dict[str, Any]:
        """
        Execute the morning briefing workflow.

        Returns:
            Dict with briefing data including news, trends, and tweet ideas
        """
        logger.info("Starting morning briefing workflow...")
        start_time = datetime.now()

        briefing = {
            'timestamp': start_time.isoformat(),
            'news_articles': [],
            'trending_topics': [],
            'tweet_ideas': [],
            'errors': []
        }

        try:
            # Step 1: Scrape news from multiple sources
            logger.info("Step 1: Scraping news sources...")
            news_sources = self.config.get('browser.scraping_targets.news_sites', [])

            if news_sources:
                # Get configured sources
                source_names = [site.get('url', '').split('//')[1].split('.')[0]
                               for site in news_sources]
            else:
                # Default sources
                source_names = ['hackernews', 'techcrunch']

            news_by_source = await self.news_scraper.scrape_all_sources(
                sources=source_names,
                limit_per_source=self.config.get('workflows.morning_briefing.news_sources', 5)
            )

            # Flatten articles
            all_articles = []
            for source, articles in news_by_source.items():
                all_articles.extend(articles)
                briefing['news_articles'].extend([
                    {
                        'title': article.title,
                        'url': article.url,
                        'source': article.source,
                        'summary': article.summary
                    }
                    for article in articles
                ])

            logger.info(f"Scraped {len(all_articles)} articles from {len(news_by_source)} sources")

            # Step 2: Get trending topics
            logger.info("Step 2: Fetching trending topics...")
            try:
                trending = self.twitter_client.get_trending_topics()
                briefing['trending_topics'] = trending[:self.config.get('workflows.morning_briefing.trending_topics', 10)]
                logger.info(f"Retrieved {len(briefing['trending_topics'])} trending topics")
            except Exception as e:
                logger.error(f"Error getting trending topics: {e}")
                briefing['errors'].append(f"Trending topics: {str(e)}")

            # Step 3: Index articles in knowledge base
            logger.info("Step 3: Indexing articles in knowledge base...")
            try:
                documents = []
                for article in all_articles:
                    content = f"{article.title}\n\n{article.summary or ''}"
                    documents.append(Document(
                        content=content,
                        metadata={
                            'type': 'news_article',
                            'source': article.source,
                            'url': article.url,
                            'timestamp': article.timestamp,
                            'category': 'tech_news'
                        }
                    ))

                if documents:
                    doc_ids = self.document_indexer.index_documents(documents)
                    logger.info(f"Indexed {len(doc_ids)} articles in knowledge base")
            except Exception as e:
                logger.error(f"Error indexing articles: {e}")
                briefing['errors'].append(f"Indexing: {str(e)}")

            # Step 4: Generate tweet ideas
            logger.info("Step 4: Generating tweet ideas...")
            try:
                # Combine news titles and trending topics for context
                context_topics = []
                context_topics.extend([article.title for article in all_articles[:5]])
                if briefing['trending_topics']:
                    context_topics.extend([t['name'] for t in briefing['trending_topics'][:5]])

                # Generate ideas for top topics
                num_ideas = self.config.get('workflows.morning_briefing.tweet_ideas', 5)

                # Create a combined topic string
                topics_str = "tech news and trending topics: " + ", ".join(context_topics[:5])

                tweet_ideas = await self.tweet_generator.generate_tweet_ideas_async(
                    topic=topics_str,
                    num_ideas=num_ideas
                )

                briefing['tweet_ideas'] = [
                    {
                        'content': idea.content,
                        'rationale': idea.rationale,
                        'confidence': idea.confidence,
                        'hashtags': idea.hashtags,
                        'category': idea.category
                    }
                    for idea in tweet_ideas
                ]

                logger.info(f"Generated {len(tweet_ideas)} tweet ideas")

            except Exception as e:
                logger.error(f"Error generating tweet ideas: {e}")
                briefing['errors'].append(f"Tweet generation: {str(e)}")

            # Calculate execution time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            briefing['duration_seconds'] = duration

            logger.info(f"Morning briefing workflow completed in {duration:.2f}s")

            return briefing

        except Exception as e:
            logger.error(f"Error in morning briefing workflow: {e}")
            briefing['errors'].append(f"Workflow error: {str(e)}")
            return briefing

    def format_briefing(self, briefing: Dict[str, Any]) -> str:
        """
        Format briefing data as readable text.

        Args:
            briefing: Briefing data dict

        Returns:
            Formatted briefing text
        """
        output = []
        output.append("=" * 80)
        output.append("MORNING CONTENT BRIEFING")
        output.append(f"Generated: {briefing['timestamp']}")
        output.append("=" * 80)

        # News articles
        output.append("\n📰 TOP NEWS ARTICLES:")
        for i, article in enumerate(briefing['news_articles'], 1):
            output.append(f"\n{i}. {article['title']}")
            output.append(f"   Source: {article['source']}")
            output.append(f"   URL: {article['url']}")
            if article.get('summary'):
                output.append(f"   Summary: {article['summary'][:100]}...")

        # Trending topics
        output.append("\n\n🔥 TRENDING TOPICS:")
        for i, trend in enumerate(briefing['trending_topics'], 1):
            volume = trend.get('tweet_volume')
            volume_str = f"({volume:,} tweets)" if volume else ""
            output.append(f"{i}. {trend['name']} {volume_str}")

        # Tweet ideas
        output.append("\n\n💡 TWEET IDEAS:")
        for i, idea in enumerate(briefing['tweet_ideas'], 1):
            output.append(f"\n{i}. {idea['content']}")
            output.append(f"   Category: {idea['category']} | Confidence: {idea['confidence']:.2f}")
            output.append(f"   Hashtags: {', '.join(idea['hashtags'])}")
            output.append(f"   Rationale: {idea['rationale']}")

        # Errors
        if briefing['errors']:
            output.append("\n\n⚠️  ERRORS:")
            for error in briefing['errors']:
                output.append(f"- {error}")

        # Footer
        output.append(f"\n{'=' * 80}")
        output.append(f"Completed in {briefing.get('duration_seconds', 0):.2f} seconds")
        output.append("=" * 80)

        return "\n".join(output)


async def run_morning_briefing():
    """Standalone function to run morning briefing."""
    from rag.embeddings.generator import EmbeddingGenerator
    from rag.vectorstore.chroma_store import ChromaStore
    from automation.browser.browser_client import BrowserClient

    # Load config
    config = get_config()

    # Initialize components
    logger.info("Initializing components for morning briefing...")

    # RAG components
    embedding_generator = EmbeddingGenerator(
        model_name=config.rag.embedding_model
    )

    vector_store = ChromaStore(
        persist_directory=config.rag.vectorstore_path,
        collection_name="content"
    )

    content_retriever = ContentRetriever(
        vector_store=vector_store,
        embedding_generator=embedding_generator,
        similarity_threshold=config.rag.similarity_threshold
    )

    document_indexer = DocumentIndexer(
        vector_store=vector_store,
        embedding_generator=embedding_generator,
        chunk_size=config.rag.chunk_size,
        chunk_overlap=config.rag.chunk_overlap
    )

    # Scraping components
    browser_client = BrowserClient(
        headless=config.get('browser.headless', True),
        browser_type=config.get('browser.browser_type', 'chromium')
    )

    news_scraper = NewsScraper(browser_client=browser_client)

    # Twitter client
    api_keys = config.api_keys
    if api_keys.twitter_api_key:
        twitter_client = TwitterClient(
            api_key=api_keys.twitter_api_key,
            api_secret=api_keys.twitter_api_secret,
            access_token=api_keys.twitter_access_token,
            access_secret=api_keys.twitter_access_secret,
            bearer_token=api_keys.twitter_bearer_token
        )
    else:
        logger.warning("Twitter API credentials not configured, skipping trending topics")
        twitter_client = None

    # Claude and tweet generator
    claude_client = ClaudeClient(
        api_key=api_keys.anthropic_api_key,
        model=config.claude.model,
        max_tokens=config.claude.max_tokens,
        temperature=config.claude.temperature
    )

    tweet_generator = TweetGenerator(
        claude_client=claude_client,
        content_retriever=content_retriever,
        config=config.content.tweet_characteristics
    )

    # Create and run workflow
    workflow = MorningBriefingWorkflow(
        news_scraper=news_scraper,
        twitter_client=twitter_client,
        tweet_generator=tweet_generator,
        document_indexer=document_indexer,
        content_retriever=content_retriever
    )

    briefing = await workflow.run()

    # Print formatted briefing
    formatted = workflow.format_briefing(briefing)
    print(formatted)

    return briefing


if __name__ == "__main__":
    # Run morning briefing
    asyncio.run(run_morning_briefing())
