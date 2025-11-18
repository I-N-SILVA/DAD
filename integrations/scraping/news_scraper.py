"""
News Scraper

Specialized scrapers for common news sources.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from automation.browser.browser_client import BrowserClient


@dataclass
class NewsArticle:
    """Container for a news article."""
    title: str
    url: str
    source: str
    summary: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class NewsScraper:
    """
    Scraper for popular tech news sources.

    Supported sources:
    - Hacker News
    - TechCrunch
    - The Verge
    - Ars Technica
    - Custom sources via configuration
    """

    def __init__(self, browser_client: Optional[BrowserClient] = None):
        """
        Initialize news scraper.

        Args:
            browser_client: Optional browser client (will create if not provided)
        """
        self.browser_client = browser_client
        self.own_browser = browser_client is None

        logger.info("NewsScraper initialized")

    async def scrape_hacker_news(
        self,
        limit: int = 10
    ) -> List[NewsArticle]:
        """
        Scrape top stories from Hacker News.

        Args:
            limit: Number of stories to return

        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Scraping Hacker News (limit={limit})")

        if self.own_browser:
            self.browser_client = BrowserClient(headless=True)
            await self.browser_client.start()

        try:
            scraped = await self.browser_client.scrape_url(
                url="https://news.ycombinator.com",
                wait_for=".titleline"
            )

            # Parse the HTML to extract articles
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(scraped.content, 'html.parser')

            articles = []
            title_lines = soup.select('.titleline')[:limit]

            for title_line in title_lines:
                link = title_line.find('a')
                if link:
                    title = link.get_text(strip=True)
                    url = link.get('href', '')

                    # Handle relative URLs
                    if not url.startswith('http'):
                        url = f"https://news.ycombinator.com/{url}"

                    articles.append(NewsArticle(
                        title=title,
                        url=url,
                        source="Hacker News"
                    ))

            logger.info(f"Scraped {len(articles)} articles from Hacker News")
            return articles

        except Exception as e:
            logger.error(f"Error scraping Hacker News: {e}")
            return []

        finally:
            if self.own_browser and self.browser_client:
                await self.browser_client.stop()

    async def scrape_techcrunch(
        self,
        limit: int = 10
    ) -> List[NewsArticle]:
        """
        Scrape latest articles from TechCrunch.

        Args:
            limit: Number of articles to return

        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Scraping TechCrunch (limit={limit})")

        if self.own_browser:
            self.browser_client = BrowserClient(headless=True)
            await self.browser_client.start()

        try:
            scraped = await self.browser_client.scrape_url(
                url="https://techcrunch.com",
                wait_for=".post-block"
            )

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(scraped.content, 'html.parser')

            articles = []
            post_blocks = soup.select('.post-block')[:limit]

            for block in post_blocks:
                title_elem = block.select_one('.post-block__title__link')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')

                    # Extract summary if available
                    summary_elem = block.select_one('.post-block__content')
                    summary = summary_elem.get_text(strip=True) if summary_elem else None

                    articles.append(NewsArticle(
                        title=title,
                        url=url,
                        source="TechCrunch",
                        summary=summary
                    ))

            logger.info(f"Scraped {len(articles)} articles from TechCrunch")
            return articles

        except Exception as e:
            logger.error(f"Error scraping TechCrunch: {e}")
            return []

        finally:
            if self.own_browser and self.browser_client:
                await self.browser_client.stop()

    async def scrape_custom_source(
        self,
        url: str,
        title_selector: str,
        link_selector: Optional[str] = None,
        summary_selector: Optional[str] = None,
        source_name: str = "Custom",
        limit: int = 10
    ) -> List[NewsArticle]:
        """
        Scrape articles from a custom news source.

        Args:
            url: Source URL
            title_selector: CSS selector for article titles
            link_selector: CSS selector for article links (if different from title)
            summary_selector: CSS selector for article summaries
            source_name: Name of the source
            limit: Number of articles

        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Scraping {source_name} at {url}")

        if self.own_browser:
            self.browser_client = BrowserClient(headless=True)
            await self.browser_client.start()

        try:
            scraped = await self.browser_client.scrape_url(
                url=url,
                wait_for=title_selector
            )

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(scraped.content, 'html.parser')

            articles = []
            title_elements = soup.select(title_selector)[:limit]

            for i, title_elem in enumerate(title_elements):
                title = title_elem.get_text(strip=True)

                # Get link
                if link_selector:
                    link_elem = title_elem.select_one(link_selector)
                    article_url = link_elem.get('href', '') if link_elem else ''
                else:
                    article_url = title_elem.get('href', '') or title_elem.find('a').get('href', '')

                # Handle relative URLs
                if article_url and not article_url.startswith('http'):
                    from urllib.parse import urljoin
                    article_url = urljoin(url, article_url)

                # Get summary if selector provided
                summary = None
                if summary_selector:
                    summary_elem = title_elem.find_parent().select_one(summary_selector)
                    if summary_elem:
                        summary = summary_elem.get_text(strip=True)

                articles.append(NewsArticle(
                    title=title,
                    url=article_url,
                    source=source_name,
                    summary=summary
                ))

            logger.info(f"Scraped {len(articles)} articles from {source_name}")
            return articles

        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")
            return []

        finally:
            if self.own_browser and self.browser_client:
                await self.browser_client.stop()

    async def scrape_all_sources(
        self,
        sources: List[str] = None,
        limit_per_source: int = 5
    ) -> Dict[str, List[NewsArticle]]:
        """
        Scrape multiple sources concurrently.

        Args:
            sources: List of source names (default: ['hackernews', 'techcrunch'])
            limit_per_source: Articles per source

        Returns:
            Dict mapping source name to articles
        """
        if sources is None:
            sources = ['hackernews', 'techcrunch']

        logger.info(f"Scraping {len(sources)} sources...")

        if self.own_browser:
            self.browser_client = BrowserClient(headless=True)
            await self.browser_client.start()

        results = {}

        try:
            for source in sources:
                if source.lower() == 'hackernews':
                    results['Hacker News'] = await self.scrape_hacker_news(limit_per_source)
                elif source.lower() == 'techcrunch':
                    results['TechCrunch'] = await self.scrape_techcrunch(limit_per_source)

            return results

        finally:
            if self.own_browser and self.browser_client:
                await self.browser_client.stop()


if __name__ == "__main__":
    import asyncio

    async def test():
        scraper = NewsScraper()

        # Test Hacker News
        print("Scraping Hacker News...")
        hn_articles = await scraper.scrape_hacker_news(limit=5)
        for article in hn_articles:
            print(f"- {article.title}")
            print(f"  {article.url}\n")

        # Test multiple sources
        print("\nScraping all sources...")
        all_articles = await scraper.scrape_all_sources(limit_per_source=3)
        for source, articles in all_articles.items():
            print(f"\n{source}:")
            for article in articles:
                print(f"  - {article.title}")

    # Run test
    # asyncio.run(test())
    print("News scraper ready. Uncomment asyncio.run(test()) to test.")
