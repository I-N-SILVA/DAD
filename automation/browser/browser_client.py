"""
Browser Automation Client

Handles automated browser tasks using Playwright.
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
except ImportError:
    logger.warning("playwright not installed. Run: pip install playwright && playwright install")
    async_playwright = None


@dataclass
class ScrapedContent:
    """Container for scraped web content."""
    url: str
    title: str
    content: str
    metadata: Dict[str, Any]
    timestamp: str
    screenshot_path: Optional[str] = None


class BrowserClient:
    """
    Automated browser client for web scraping and interaction.

    Features:
    - Page navigation and interaction
    - Content extraction
    - Screenshot capture
    - Link following
    - Form filling
    - JavaScript execution
    - Multiple browser contexts
    """

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        timeout: int = 30000,
        user_agent: Optional[str] = None,
        viewport: Optional[Dict[str, int]] = None
    ):
        """
        Initialize browser client.

        Args:
            headless: Run browser in headless mode
            browser_type: 'chromium', 'firefox', or 'webkit'
            timeout: Default timeout in milliseconds
            user_agent: Custom user agent string
            viewport: Viewport size dict with 'width' and 'height'
        """
        if not async_playwright:
            raise ImportError("playwright required. Install: pip install playwright")

        self.headless = headless
        self.browser_type = browser_type
        self.timeout = timeout
        self.user_agent = user_agent
        self.viewport = viewport or {"width": 1920, "height": 1080}

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

        logger.info(f"BrowserClient initialized ({browser_type}, headless={headless})")

    async def start(self):
        """Start the browser."""
        try:
            self.playwright = await async_playwright().start()

            # Launch browser based on type
            if self.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
            elif self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"Invalid browser type: {self.browser_type}")

            # Create context
            context_options = {
                "viewport": self.viewport,
            }
            if self.user_agent:
                context_options["user_agent"] = self.user_agent

            self.context = await self.browser.new_context(**context_options)

            logger.info("Browser started successfully")

        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise

    async def stop(self):
        """Stop the browser."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            logger.info("Browser stopped")

        except Exception as e:
            logger.error(f"Error stopping browser: {e}")

    async def scrape_url(
        self,
        url: str,
        wait_for: Optional[str] = None,
        extract_selectors: Optional[Dict[str, str]] = None,
        take_screenshot: bool = False,
        screenshot_path: Optional[str] = None
    ) -> ScrapedContent:
        """
        Scrape content from a URL.

        Args:
            url: URL to scrape
            wait_for: CSS selector to wait for before extracting
            extract_selectors: Dict of field_name: selector to extract specific elements
            take_screenshot: Whether to capture screenshot
            screenshot_path: Path to save screenshot

        Returns:
            ScrapedContent object
        """
        if not self.context:
            await self.start()

        page = await self.context.new_page()

        try:
            logger.info(f"Scraping URL: {url}")

            # Navigate to page
            await page.goto(url, timeout=self.timeout)

            # Wait for specific element if specified
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=self.timeout)

            # Get page title
            title = await page.title()

            # Extract main content
            content = await page.content()

            # Extract specific elements if selectors provided
            extracted_data = {}
            if extract_selectors:
                for field, selector in extract_selectors.items():
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            extracted_data[field] = await element.inner_text()
                    except Exception as e:
                        logger.warning(f"Failed to extract {field}: {e}")
                        extracted_data[field] = None

            # Take screenshot if requested
            screenshot_file = None
            if take_screenshot:
                if not screenshot_path:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_file = f"screenshots/{timestamp}_{url.split('//')[-1].replace('/', '_')}.png"
                else:
                    screenshot_file = screenshot_path

                Path(screenshot_file).parent.mkdir(parents=True, exist_ok=True)
                await page.screenshot(path=screenshot_file, full_page=True)
                logger.info(f"Screenshot saved: {screenshot_file}")

            # Build metadata
            metadata = {
                'domain': page.url.split('/')[2],
                'extracted_fields': extracted_data,
                'status': 'success'
            }

            scraped_content = ScrapedContent(
                url=url,
                title=title,
                content=content,
                metadata=metadata,
                timestamp=datetime.now().isoformat(),
                screenshot_path=screenshot_file
            )

            logger.info(f"Successfully scraped {url}")
            return scraped_content

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            raise

        finally:
            await page.close()

    async def scrape_multiple(
        self,
        urls: List[str],
        **kwargs
    ) -> List[ScrapedContent]:
        """
        Scrape multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape
            **kwargs: Additional arguments for scrape_url

        Returns:
            List of ScrapedContent objects
        """
        logger.info(f"Scraping {len(urls)} URLs concurrently...")

        tasks = [self.scrape_url(url, **kwargs) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to scrape {urls[i]}: {result}")
            else:
                successful_results.append(result)

        logger.info(f"Successfully scraped {len(successful_results)}/{len(urls)} URLs")
        return successful_results

    async def extract_article(
        self,
        url: str
    ) -> Dict[str, Any]:
        """
        Extract article content with smart parsing.

        Args:
            url: Article URL

        Returns:
            Dict with title, content, author, date, etc.
        """
        if not self.context:
            await self.start()

        page = await self.context.new_page()

        try:
            await page.goto(url, timeout=self.timeout)

            # Common article selectors
            article_data = {
                'url': url,
                'title': await page.title(),
                'timestamp': datetime.now().isoformat()
            }

            # Try to extract article content using common patterns
            content_selectors = [
                'article',
                '[role="article"]',
                '.article-content',
                '.post-content',
                '.entry-content',
                'main'
            ]

            for selector in content_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        article_data['content'] = await element.inner_text()
                        break
                except Exception:
                    continue

            # Extract metadata
            try:
                # Author
                author_selectors = ['.author', '[rel="author"]', '.byline']
                for selector in author_selectors:
                    element = await page.query_selector(selector)
                    if element:
                        article_data['author'] = await element.inner_text()
                        break

                # Published date
                date_selectors = ['time', '.published', '.post-date']
                for selector in date_selectors:
                    element = await page.query_selector(selector)
                    if element:
                        article_data['published_date'] = await element.get_attribute('datetime') or await element.inner_text()
                        break

            except Exception as e:
                logger.warning(f"Error extracting metadata: {e}")

            return article_data

        finally:
            await page.close()

    async def monitor_page(
        self,
        url: str,
        selector: str,
        check_interval: int = 60,
        max_checks: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Monitor a page for changes.

        Args:
            url: URL to monitor
            selector: Selector to watch for changes
            check_interval: Seconds between checks
            max_checks: Maximum number of checks

        Returns:
            List of detected changes
        """
        if not self.context:
            await self.start()

        page = await self.context.new_page()
        changes = []
        previous_content = None

        try:
            for i in range(max_checks):
                await page.goto(url)
                await page.wait_for_selector(selector)

                element = await page.query_selector(selector)
                current_content = await element.inner_html()

                if previous_content and current_content != previous_content:
                    changes.append({
                        'timestamp': datetime.now().isoformat(),
                        'check_number': i + 1,
                        'change_detected': True
                    })
                    logger.info(f"Change detected on {url}")

                previous_content = current_content

                if i < max_checks - 1:
                    await asyncio.sleep(check_interval)

        finally:
            await page.close()

        return changes

    async def fill_form(
        self,
        url: str,
        form_data: Dict[str, str],
        submit_selector: str
    ) -> bool:
        """
        Fill and submit a form.

        Args:
            url: Page URL
            form_data: Dict of selector: value pairs
            submit_selector: Submit button selector

        Returns:
            Success status
        """
        if not self.context:
            await self.start()

        page = await self.context.new_page()

        try:
            await page.goto(url)

            # Fill form fields
            for selector, value in form_data.items():
                await page.fill(selector, value)

            # Submit form
            await page.click(submit_selector)

            # Wait for navigation
            await page.wait_for_load_state('networkidle')

            logger.info(f"Form submitted successfully on {url}")
            return True

        except Exception as e:
            logger.error(f"Error filling form: {e}")
            return False

        finally:
            await page.close()

    async def execute_script(
        self,
        url: str,
        script: str
    ) -> Any:
        """
        Execute JavaScript on a page.

        Args:
            url: Page URL
            script: JavaScript code to execute

        Returns:
            Script result
        """
        if not self.context:
            await self.start()

        page = await self.context.new_page()

        try:
            await page.goto(url)
            result = await page.evaluate(script)
            return result

        finally:
            await page.close()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


if __name__ == "__main__":
    # Test browser client
    async def test():
        async with BrowserClient(headless=True) as browser:
            # Test scraping
            result = await browser.scrape_url(
                "https://news.ycombinator.com",
                wait_for=".titleline",
                take_screenshot=True
            )

            print(f"Scraped: {result.title}")
            print(f"URL: {result.url}")
            print(f"Screenshot: {result.screenshot_path}")

            # Test article extraction
            article = await browser.extract_article(
                "https://example.com/article"
            )
            print(f"\nArticle: {article.get('title')}")

    # Run test
    # asyncio.run(test())
    print("Browser client ready. Uncomment asyncio.run(test()) to test.")
