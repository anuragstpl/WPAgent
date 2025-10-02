"""
News Fetcher Module - Fetches latest news using Tavily API
"""
import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetches news articles using Tavily Search API"""

    def __init__(self):
        self.api_key = os.getenv('TAVILY_API_KEY')
        if not self.api_key or self.api_key == 'your_tavily_api_key_here':
            logger.warning("Tavily API key not set. Please add TAVILY_API_KEY to .env file")
        self.base_url = "https://api.tavily.com/search"

    def fetch_news(
        self,
        query: str,
        category: Optional[str] = None,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_images: bool = True,
        include_answer: bool = True,
        days: int = 3
    ) -> List[Dict]:
        """
        Fetch news articles from Tavily API

        Args:
            query: Search query for news
            category: News category (technology, business, sports, etc.)
            max_results: Maximum number of results to return
            search_depth: 'basic' or 'advanced'
            include_images: Whether to include images in results
            include_answer: Whether to include AI-generated answer
            days: Number of days to look back for news

        Returns:
            List of news articles with title, content, url, etc.
        """
        if not self.api_key or self.api_key == 'your_tavily_api_key_here':
            logger.error("Tavily API key is not configured")
            return []

        # Construct the search query
        search_query = query
        if category:
            search_query = f"{category} {query}"

        # Prepare request payload
        payload = {
            "api_key": self.api_key,
            "query": search_query,
            "search_depth": search_depth,
            "include_images": include_images,
            "include_answer": include_answer,
            "max_results": max_results,
            "days": days
        }

        try:
            logger.info(f"Fetching news for query: {search_query}")
            response = requests.post(self.base_url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Extract results
            results = []
            if 'results' in data:
                for item in data['results']:
                    article = {
                        'title': item.get('title', 'Untitled'),
                        'url': item.get('url', ''),
                        'content': item.get('content', ''),
                        'score': item.get('score', 0),
                        'published_date': item.get('published_date', ''),
                        'raw_content': item.get('raw_content', None)
                    }
                    results.append(article)

            # Add AI-generated answer if available
            if include_answer and 'answer' in data:
                logger.info(f"AI Answer: {data['answer'][:100]}...")

            # Add images if available
            if include_images and 'images' in data:
                for idx, result in enumerate(results):
                    if idx < len(data['images']):
                        result['tavily_image'] = data['images'][idx]

            logger.info(f"Successfully fetched {len(results)} news articles")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news from Tavily: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return []

    def fetch_news_by_category(
        self,
        category: str,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Fetch news for a specific category

        Args:
            category: News category (technology, business, sports, health, etc.)
            max_results: Maximum number of results

        Returns:
            List of news articles
        """
        queries = {
            'technology': 'latest technology news and innovations',
            'business': 'latest business and finance news',
            'sports': 'latest sports news and updates',
            'health': 'latest health and medical news',
            'science': 'latest science and research news',
            'entertainment': 'latest entertainment and celebrity news',
            'politics': 'latest political news and updates',
            'world': 'latest world news and international updates'
        }

        query = queries.get(category.lower(), f'latest {category} news')
        return self.fetch_news(query, category=category, max_results=max_results)

    def fetch_trending_news(self, max_results: int = 10) -> List[Dict]:
        """
        Fetch trending news across all categories

        Args:
            max_results: Maximum number of results

        Returns:
            List of trending news articles
        """
        return self.fetch_news(
            query="latest breaking news and trending topics",
            max_results=max_results,
            search_depth="advanced"
        )


# Example usage
if __name__ == "__main__":
    fetcher = NewsFetcher()

    # Test fetching technology news
    print("\n=== Testing Technology News ===")
    tech_news = fetcher.fetch_news_by_category('technology', max_results=3)
    for idx, article in enumerate(tech_news, 1):
        print(f"\n{idx}. {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   Content: {article['content'][:150]}...")

    # Test fetching trending news
    print("\n\n=== Testing Trending News ===")
    trending = fetcher.fetch_trending_news(max_results=3)
    for idx, article in enumerate(trending, 1):
        print(f"\n{idx}. {article['title']}")
        print(f"   URL: {article['url']}")
