"""
Image Fetcher Module - Fetches relevant images using Pexels API
"""
import os
import requests
from typing import Optional, Dict, List
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageFetcher:
    """Fetches relevant images using Pexels API"""

    def __init__(self):
        self.api_key = os.getenv('PEXELS_API_KEY')
        if not self.api_key or self.api_key == 'your_pexels_api_key_here':
            logger.warning("Pexels API key not set. Please add PEXELS_API_KEY to .env file")
        self.base_url = "https://api.pexels.com/v1"
        self.headers = {
            'Authorization': self.api_key
        }

    def search_image(
        self,
        query: str,
        orientation: str = "landscape",
        size: str = "medium",
        per_page: int = 1,
        page: int = 1
    ) -> Optional[Dict]:
        """
        Search for an image on Pexels

        Args:
            query: Search query (e.g., "technology", "business news")
            orientation: Image orientation - 'landscape', 'portrait', or 'square'
            size: Image size - 'large', 'medium', or 'small'
            per_page: Number of results per page (max 80)
            page: Page number

        Returns:
            Dictionary containing image information or None
        """
        if not self.api_key or self.api_key == 'your_pexels_api_key_here':
            logger.error("Pexels API key is not configured")
            return None

        url = f"{self.base_url}/search"
        params = {
            'query': query,
            'orientation': orientation,
            'size': size,
            'per_page': per_page,
            'page': page
        }

        try:
            logger.info(f"Searching Pexels for: {query}")
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data.get('photos') and len(data['photos']) > 0:
                photo = data['photos'][0]
                image_data = {
                    'id': photo.get('id'),
                    'photographer': photo.get('photographer'),
                    'photographer_url': photo.get('photographer_url'),
                    'src': {
                        'original': photo['src'].get('original'),
                        'large2x': photo['src'].get('large2x'),
                        'large': photo['src'].get('large'),
                        'medium': photo['src'].get('medium'),
                        'small': photo['src'].get('small'),
                        'portrait': photo['src'].get('portrait'),
                        'landscape': photo['src'].get('landscape'),
                        'tiny': photo['src'].get('tiny')
                    },
                    'width': photo.get('width'),
                    'height': photo.get('height'),
                    'url': photo.get('url'),
                    'alt': photo.get('alt', query)
                }

                logger.info(f"Found image by {image_data['photographer']}")
                return image_data
            else:
                logger.warning(f"No images found for query: {query}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching image from Pexels: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None

    def get_image_for_news(
        self,
        title: str,
        category: Optional[str] = None,
        content: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get a relevant image for a news article

        Args:
            title: News article title
            category: News category
            content: News content (optional, for better matching)

        Returns:
            Dictionary containing image information or None
        """
        # Try to get image based on category first
        if category:
            image = self.search_image(category, orientation="landscape")
            if image:
                return image

        # Extract keywords from title
        # Remove common words and get important keywords
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = title.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 3]

        # Try searching with first few keywords
        if keywords:
            search_query = ' '.join(keywords[:3])
            image = self.search_image(search_query, orientation="landscape")
            if image:
                return image

        # Fallback to category or generic news image
        fallback_queries = [category, 'news', 'breaking news', 'newspaper']
        for query in fallback_queries:
            if query:
                image = self.search_image(query, orientation="landscape")
                if image:
                    return image

        return None

    def get_curated_photos(self, per_page: int = 10, page: int = 1) -> List[Dict]:
        """
        Get curated photos from Pexels

        Args:
            per_page: Number of results per page (max 80)
            page: Page number

        Returns:
            List of curated photos
        """
        if not self.api_key or self.api_key == 'your_pexels_api_key_here':
            logger.error("Pexels API key is not configured")
            return []

        url = f"{self.base_url}/curated"
        params = {
            'per_page': per_page,
            'page': page
        }

        try:
            logger.info("Fetching curated photos from Pexels")
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            photos = []
            if data.get('photos'):
                for photo in data['photos']:
                    image_data = {
                        'id': photo.get('id'),
                        'photographer': photo.get('photographer'),
                        'src': photo['src'].get('large'),
                        'alt': photo.get('alt', 'Curated photo')
                    }
                    photos.append(image_data)

            logger.info(f"Found {len(photos)} curated photos")
            return photos

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching curated photos: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return []

    def download_image(self, image_url: str, save_path: str) -> bool:
        """
        Download an image from URL to local path

        Args:
            image_url: URL of the image to download
            save_path: Local path to save the image

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Downloading image from {image_url}")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Image saved to {save_path}")
            return True

        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    fetcher = ImageFetcher()

    # Test searching for technology image
    print("\n=== Testing Technology Image Search ===")
    tech_image = fetcher.search_image('technology innovation')
    if tech_image:
        print(f"Image ID: {tech_image['id']}")
        print(f"Photographer: {tech_image['photographer']}")
        print(f"Large Image URL: {tech_image['src']['large']}")
        print(f"Medium Image URL: {tech_image['src']['medium']}")

    # Test getting image for news article
    print("\n\n=== Testing News Image Fetch ===")
    news_image = fetcher.get_image_for_news(
        title="Breaking: New AI Technology Revolutionizes Healthcare",
        category="technology"
    )
    if news_image:
        print(f"Found image by: {news_image['photographer']}")
        print(f"Image URL: {news_image['src']['large']}")
