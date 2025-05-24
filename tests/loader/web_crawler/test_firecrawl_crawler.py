import unittest
import os
from unittest.mock import patch, MagicMock

from langchain_core.documents import Document

from deepsearcher.loader.web_crawler import FireCrawlCrawler


class TestFireCrawlCrawler(unittest.TestCase):
    """Tests for the FireCrawlCrawler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Patch the environment variable
        self.env_patcher = patch.dict('os.environ', {'FIRECRAWL_API_KEY': 'fake-api-key'})
        self.env_patcher.start()
        
        # Create a mock for the FirecrawlApp
        self.firecrawl_app_patcher = patch('deepsearcher.loader.web_crawler.firecrawl_crawler.FirecrawlApp')
        self.mock_firecrawl_app = self.firecrawl_app_patcher.start()
        
        # Set up mock instances
        self.mock_app_instance = MagicMock()
        self.mock_firecrawl_app.return_value = self.mock_app_instance
        
        # Create the crawler
        self.crawler = FireCrawlCrawler()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()
        self.firecrawl_app_patcher.stop()
    
    def test_init(self):
        """Test initialization."""
        self.assertIsNone(self.crawler.app)
    
    def test_crawl_url_single_page(self):
        """Test crawling a single URL."""
        url = "https://example.com"
        
        # Set up mock response for scrape_url
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "markdown": "# Example Page\nThis is a test page.",
            "metadata": {"title": "Example Page", "url": url}
        }
        self.mock_app_instance.scrape_url.return_value = mock_response
        
        # Call the method
        documents = self.crawler.crawl_url(url)
        
        # Verify FirecrawlApp was initialized
        self.mock_firecrawl_app.assert_called_once_with(api_key='fake-api-key')
        
        # Verify scrape_url was called correctly
        self.mock_app_instance.scrape_url.assert_called_once_with(url=url, formats=["markdown"])
        
        # Check results
        self.assertEqual(len(documents), 1)
        document = documents[0]
        self.assertEqual(document.page_content, "# Example Page\nThis is a test page.")
        self.assertEqual(document.metadata["reference"], url)
        self.assertEqual(document.metadata["title"], "Example Page")
    
    def test_crawl_url_multiple_pages(self):
        """Test crawling multiple pages recursively."""
        url = "https://example.com"
        max_depth = 3
        limit = 10
        
        # Set up mock response for crawl_url
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "data": [
                {
                    "markdown": "# Page 1\nContent 1",
                    "metadata": {"title": "Page 1", "url": "https://example.com/page1"}
                },
                {
                    "markdown": "# Page 2\nContent 2",
                    "metadata": {"title": "Page 2", "url": "https://example.com/page2"}
                }
            ]
        }
        self.mock_app_instance.crawl_url.return_value = mock_response
        
        # Call the method
        documents = self.crawler.crawl_url(url, max_depth=max_depth, limit=limit)
        
        # Verify FirecrawlApp was initialized
        self.mock_firecrawl_app.assert_called_once_with(api_key='fake-api-key')
        
        # Verify crawl_url was called correctly
        self.mock_app_instance.crawl_url.assert_called_once()
        call_kwargs = self.mock_app_instance.crawl_url.call_args[1]
        self.assertEqual(call_kwargs['url'], url)
        self.assertEqual(call_kwargs['max_depth'], max_depth)
        self.assertEqual(call_kwargs['limit'], limit)
        
        # Check results
        self.assertEqual(len(documents), 2)
        
        # Check first document
        self.assertEqual(documents[0].page_content, "# Page 1\nContent 1")
        self.assertEqual(documents[0].metadata["reference"], "https://example.com/page1")
        self.assertEqual(documents[0].metadata["title"], "Page 1")
        
        # Check second document
        self.assertEqual(documents[1].page_content, "# Page 2\nContent 2")
        self.assertEqual(documents[1].metadata["reference"], "https://example.com/page2")
        self.assertEqual(documents[1].metadata["title"], "Page 2")
    
    def test_crawl_url_with_default_params(self):
        """Test crawling with default parameters."""
        url = "https://example.com"
        
        # Set up mock response for crawl_url
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {"data": []}
        self.mock_app_instance.crawl_url.return_value = mock_response
        
        # Call the method with only max_depth
        self.crawler.crawl_url(url, max_depth=2)
        
        # Verify default values were used
        call_kwargs = self.mock_app_instance.crawl_url.call_args[1]
        self.assertEqual(call_kwargs['limit'], 20)  # Default limit
        self.assertEqual(call_kwargs['max_depth'], 2)  # Provided max_depth
        self.assertEqual(call_kwargs['allow_backward_links'], False)  # Default allow_backward_links


if __name__ == "__main__":
    unittest.main() 