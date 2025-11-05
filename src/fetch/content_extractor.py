"""Web content extraction and processing."""

import logging
from typing import Optional, Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import html2text

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extracts and processes web page content."""

    def __init__(self, timeout: int = 10):
        """
        Initialize content extractor.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_url(self, url: str) -> Optional[Dict]:
        """
        Fetch and extract content from a URL.

        Args:
            url: URL to fetch.

        Returns:
            Dictionary containing extracted content or None if failed.
        """
        try:
            logger.info(f"Fetching URL: {url}")
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.content, 'lxml')

            # Extract metadata
            title = self._extract_title(soup)
            description = self._extract_description(soup)

            # Extract main content
            content = self._extract_main_content(soup)

            # Convert HTML to markdown
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            markdown_content = h.handle(content)

            result = {
                'url': url,
                'final_url': response.url,
                'title': title,
                'description': description,
                'content': markdown_content,
                'content_length': len(markdown_content),
                'status_code': response.status_code,
            }

            logger.info(f"Successfully extracted content from {url} ({len(markdown_content)} chars)")
            return result

        except requests.Timeout:
            logger.error(f"Timeout fetching {url}")
            return None
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing {url}: {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        # Try meta og:title first
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content']

        # Try regular title tag
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        # Try h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()

        return "No title found"

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description."""
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']

        # Try og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content']

        return ""

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content from page.

        This is a simplified extraction. For production, consider using
        libraries like readability-lxml or newspaper3k.
        """
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Try to find main content area
        main_content = None

        # Look for common content containers
        for selector in ['article', 'main', '[role="main"]', '.post-content', '.article-content', '#content']:
            if isinstance(selector, str) and selector.startswith('.'):
                main_content = soup.find(class_=selector[1:])
            elif isinstance(selector, str) and selector.startswith('#'):
                main_content = soup.find(id=selector[1:])
            else:
                main_content = soup.find(selector)

            if main_content:
                break

        # Fallback to body
        if not main_content:
            main_content = soup.find('body')

        if main_content:
            return str(main_content)

        return str(soup)

    def batch_fetch(self, urls: list) -> Dict[str, Optional[Dict]]:
        """
        Fetch multiple URLs.

        Args:
            urls: List of URLs to fetch.

        Returns:
            Dictionary mapping URLs to their extracted content.
        """
        results = {}
        for url in urls:
            results[url] = self.fetch_url(url)
        return results

    def is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid.

        Args:
            url: URL to validate.

        Returns:
            True if valid, False otherwise.
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
