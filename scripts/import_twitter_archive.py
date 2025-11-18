"""
Import Twitter Archive

Imports tweets from a Twitter archive ZIP file into the knowledge base.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import zipfile
from loguru import logger
from typing import List, Dict, Any

from rag.vectorstore.chroma_store import ChromaStore
from rag.indexing.indexer import DocumentIndexer
from rag.embeddings.generator import EmbeddingGenerator
from backend.core.config import get_config


def extract_tweets_from_archive(archive_path: str) -> List[Dict[str, Any]]:
    """
    Extract tweets from Twitter archive.

    Args:
        archive_path: Path to Twitter archive ZIP file

    Returns:
        List of tweet dictionaries
    """
    logger.info(f"Extracting tweets from archive: {archive_path}")

    tweets = []

    try:
        with zipfile.ZipFile(archive_path, 'r') as zip_file:
            # Twitter archives typically have tweets in data/tweets.js or tweet.js
            tweet_files = [f for f in zip_file.namelist()
                          if 'tweet' in f.lower() and f.endswith('.js')]

            if not tweet_files:
                logger.error("No tweet files found in archive")
                return []

            logger.info(f"Found tweet files: {tweet_files}")

            for tweet_file in tweet_files:
                content = zip_file.read(tweet_file).decode('utf-8')

                # Twitter archive JS files start with "window.YTD.tweets.part0 = "
                if content.startswith('window.'):
                    # Extract JSON array
                    json_start = content.index('[')
                    json_content = content[json_start:]
                    data = json.loads(json_content)
                else:
                    data = json.loads(content)

                # Extract tweet data
                for item in data:
                    if 'tweet' in item:
                        tweet = item['tweet']
                    else:
                        tweet = item

                    tweets.append({
                        'id': tweet.get('id_str', tweet.get('id')),
                        'text': tweet.get('full_text', tweet.get('text', '')),
                        'created_at': tweet.get('created_at'),
                        'likes': tweet.get('favorite_count', 0),
                        'retweets': tweet.get('retweet_count', 0),
                        'replies': tweet.get('reply_count', 0)
                    })

        logger.info(f"Extracted {len(tweets)} tweets from archive")
        return tweets

    except Exception as e:
        logger.error(f"Error extracting tweets: {e}")
        return []


def import_tweets(tweets: List[Dict[str, Any]], indexer: DocumentIndexer) -> int:
    """
    Import tweets into knowledge base.

    Args:
        tweets: List of tweet dictionaries
        indexer: Document indexer

    Returns:
        Number of tweets imported
    """
    logger.info(f"Importing {len(tweets)} tweets into knowledge base...")

    try:
        indexed_ids = indexer.index_tweets(tweets, include_metadata=True)
        logger.info(f"Successfully imported {len(indexed_ids)} tweets")
        return len(indexed_ids)

    except Exception as e:
        logger.error(f"Error importing tweets: {e}")
        return 0


def main():
    """Main import function."""
    import argparse

    parser = argparse.ArgumentParser(description="Import Twitter archive into knowledge base")
    parser.add_argument(
        '--archive-path',
        required=True,
        help='Path to Twitter archive ZIP file'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of tweets to import (optional)'
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("TWITTER ARCHIVE IMPORT")
    logger.info("=" * 80)

    # Check archive exists
    archive_path = Path(args.archive_path)
    if not archive_path.exists():
        logger.error(f"Archive not found: {archive_path}")
        return 1

    # Initialize components
    logger.info("Initializing components...")

    try:
        config = get_config()

        embedding_generator = EmbeddingGenerator(
            model_name=config.rag.embedding_model
        )

        vector_store = ChromaStore(
            persist_directory=config.rag.vectorstore_path,
            collection_name="content"
        )

        indexer = DocumentIndexer(
            vector_store=vector_store,
            embedding_generator=embedding_generator,
            chunk_size=config.rag.chunk_size,
            chunk_overlap=config.rag.chunk_overlap
        )

        # Extract tweets
        tweets = extract_tweets_from_archive(str(archive_path))

        if not tweets:
            logger.error("No tweets found in archive")
            return 1

        # Limit if specified
        if args.limit:
            tweets = tweets[:args.limit]
            logger.info(f"Limited to {len(tweets)} tweets")

        # Import tweets
        imported_count = import_tweets(tweets, indexer)

        logger.info("=" * 80)
        logger.info(f"✅ Import complete: {imported_count} tweets imported")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"Error during import: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
