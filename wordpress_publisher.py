"""
WordPress Publisher Module - Publishes content to WordPress
"""
import os
import requests
from typing import Optional, Dict, List
from dotenv import load_dotenv
import logging
import re
import time

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WordPressPublisher:
    """Publishes news articles to WordPress site"""

    def __init__(self):
        self.base_url = os.getenv('WORDPRESS_BASE_URL', 'https://vibebuilder.studio')
        self.bearer_token = os.getenv('BEARER_TOKEN')
        if not self.bearer_token:
            logger.warning("WordPress Bearer Token not set. Please add BEARER_TOKEN to .env file")

    def get_headers(self) -> Dict[str, str]:
        """Get WordPress API headers with authentication"""
        return {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'WordPress-News-Bot/1.0'
        }

    def create_post(
        self,
        title: str,
        content: str,
        status: str = 'publish',
        excerpt: Optional[str] = None,
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
        featured_media: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Create a new WordPress post

        Args:
            title: Post title
            content: Post content (HTML)
            status: Post status - 'draft', 'publish', or 'private'
            excerpt: Post excerpt
            categories: List of category IDs
            tags: List of tag IDs
            featured_media: Featured image media ID

        Returns:
            Dictionary containing post information or None
        """
        if not self.bearer_token:
            logger.error("WordPress Bearer Token is not configured")
            return None

        url = f"{self.base_url}/wp-json/wp/v2/posts"

        data = {
            'title': title,
            'content': content,
            'status': status
        }

        if excerpt:
            data['excerpt'] = excerpt

        if categories:
            data['categories'] = categories

        if tags:
            data['tags'] = tags

        if featured_media:
            data['featured_media'] = featured_media

        try:
            logger.info(f"Creating WordPress post: {title[:50]}...")
            response = requests.post(url, headers=self.get_headers(), json=data, timeout=30)
            response.raise_for_status()

            post_data = response.json()
            post_id = post_data.get('id')
            post_url = post_data.get('link')

            logger.info(f"Post created successfully! ID: {post_id}, URL: {post_url}")

            return {
                'id': post_id,
                'url': post_url,
                'title': title,
                'status': status,
                'date': post_data.get('date')
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed. Please check your bearer token.")
            elif e.response.status_code == 403:
                logger.error("Permission denied. You don't have permission to create posts.")
            else:
                logger.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error creating post: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating post: {str(e)}")
            return None

    def upload_media(
        self,
        image_url: str,
        title: Optional[str] = None,
        alt_text: Optional[str] = None,
        caption: Optional[str] = None
    ) -> Optional[int]:
        """
        Upload media from URL to WordPress

        Args:
            image_url: URL of the image to upload
            title: Media title (used to generate unique filename)
            alt_text: Alt text for the image
            caption: Image caption

        Returns:
            Media ID or None
        """
        if not self.bearer_token:
            logger.error("WordPress Bearer Token is not configured")
            return None

        try:
            # First, download the image
            logger.info(f"Downloading image from {image_url}")
            image_response = requests.get(image_url, timeout=30)
            image_response.raise_for_status()

            # Generate unique filename based on title
            if title:
                # Sanitize title for filename: remove special chars, limit length
                safe_title = re.sub(r'[^\w\s-]', '', title.lower())
                safe_title = re.sub(r'[-\s]+', '-', safe_title)
                safe_title = safe_title[:50]  # Limit length

                # Add timestamp for uniqueness
                timestamp = int(time.time())

                # Get file extension from URL or content type
                url_filename = image_url.split('/')[-1].split('?')[0]
                if '.' in url_filename:
                    ext = url_filename.split('.')[-1].lower()
                    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        filename = f"{safe_title}-{timestamp}.{ext}"
                    else:
                        filename = f"{safe_title}-{timestamp}.jpg"
                else:
                    filename = f"{safe_title}-{timestamp}.jpg"
            else:
                # Fallback to original URL filename with timestamp
                url_filename = image_url.split('/')[-1].split('?')[0]
                if not url_filename or '.' not in url_filename:
                    filename = f"image-{int(time.time())}.jpg"
                else:
                    name_part = url_filename.rsplit('.', 1)[0]
                    ext_part = url_filename.rsplit('.', 1)[1]
                    filename = f"{name_part}-{int(time.time())}.{ext_part}"

            # Determine content type from response or filename
            content_type = image_response.headers.get('Content-Type', 'image/jpeg')

            # If content type is not set, try to determine from filename
            if not content_type or content_type == 'application/octet-stream':
                if filename.lower().endswith('.png'):
                    content_type = 'image/png'
                elif filename.lower().endswith('.gif'):
                    content_type = 'image/gif'
                elif filename.lower().endswith('.webp'):
                    content_type = 'image/webp'
                else:
                    content_type = 'image/jpeg'

            # Prepare headers for media upload
            headers = {
                'Authorization': f'Bearer {self.bearer_token}',
                'Content-Type': content_type,
                'Content-Disposition': f'attachment; filename="{filename}"',
            }

            # Upload to WordPress
            url = f"{self.base_url}/wp-json/wp/v2/media"

            logger.info(f"Uploading image to WordPress: {filename} (Content-Type: {content_type})")
            upload_response = requests.post(
                url,
                headers=headers,
                data=image_response.content,
                timeout=60
            )
            upload_response.raise_for_status()

            media_data = upload_response.json()
            media_id = media_data.get('id')

            # Update media metadata if provided
            if media_id and (title or alt_text or caption):
                self.update_media_metadata(media_id, title, alt_text, caption)

            logger.info(f"Media uploaded successfully! Media ID: {media_id}")
            return media_id

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error uploading media: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error uploading media: {str(e)}")
            return None

    def update_media_metadata(
        self,
        media_id: int,
        title: Optional[str] = None,
        alt_text: Optional[str] = None,
        caption: Optional[str] = None
    ) -> bool:
        """
        Update media metadata

        Args:
            media_id: Media ID
            title: Media title
            alt_text: Alt text
            caption: Caption

        Returns:
            True if successful, False otherwise
        """
        if not self.bearer_token:
            return False

        url = f"{self.base_url}/wp-json/wp/v2/media/{media_id}"
        data = {}

        if title:
            data['title'] = title
        if alt_text:
            data['alt_text'] = alt_text
        if caption:
            data['caption'] = caption

        if not data:
            return True

        try:
            response = requests.post(url, headers=self.get_headers(), json=data, timeout=30)
            response.raise_for_status()
            logger.info(f"Media metadata updated for ID: {media_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating media metadata: {str(e)}")
            return False

    def get_or_create_category(self, category_name: str) -> Optional[int]:
        """
        Get existing category ID or create new category

        Args:
            category_name: Category name

        Returns:
            Category ID or None
        """
        if not self.bearer_token:
            return None

        # First, try to find existing category
        try:
            url = f"{self.base_url}/wp-json/wp/v2/categories"
            params = {'search': category_name}

            response = requests.get(url, headers=self.get_headers(), params=params, timeout=15)
            response.raise_for_status()

            categories = response.json()
            if categories:
                # Check for exact match
                for cat in categories:
                    if cat.get('name', '').lower() == category_name.lower():
                        logger.info(f"Found existing category: {category_name} (ID: {cat['id']})")
                        return cat['id']

            # Category not found, create new one
            logger.info(f"Creating new category: {category_name}")
            create_response = requests.post(
                url,
                headers=self.get_headers(),
                json={'name': category_name},
                timeout=15
            )
            create_response.raise_for_status()

            new_category = create_response.json()
            category_id = new_category.get('id')
            logger.info(f"Category created: {category_name} (ID: {category_id})")
            return category_id

        except Exception as e:
            logger.error(f"Error getting/creating category: {str(e)}")
            return None

    def get_or_create_tag(self, tag_name: str) -> Optional[int]:
        """
        Get existing tag ID or create new tag

        Args:
            tag_name: Tag name

        Returns:
            Tag ID or None
        """
        if not self.bearer_token:
            return None

        # First, try to find existing tag
        try:
            url = f"{self.base_url}/wp-json/wp/v2/tags"
            params = {'search': tag_name}

            response = requests.get(url, headers=self.get_headers(), params=params, timeout=15)
            response.raise_for_status()

            tags = response.json()
            if tags:
                # Check for exact match
                for tag in tags:
                    if tag.get('name', '').lower() == tag_name.lower():
                        logger.info(f"Found existing tag: {tag_name} (ID: {tag['id']})")
                        return tag['id']

            # Tag not found, create new one
            logger.info(f"Creating new tag: {tag_name}")
            create_response = requests.post(
                url,
                headers=self.get_headers(),
                json={'name': tag_name},
                timeout=15
            )
            create_response.raise_for_status()

            new_tag = create_response.json()
            tag_id = new_tag.get('id')
            logger.info(f"Tag created: {tag_name} (ID: {tag_id})")
            return tag_id

        except Exception as e:
            logger.error(f"Error getting/creating tag: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    publisher = WordPressPublisher()

    # Test creating a post
    print("\n=== Testing WordPress Post Creation ===")
    test_post = publisher.create_post(
        title="Test News Article from Bot",
        content="<p>This is a test article created by the automated news bot.</p><p>It includes HTML formatting and multiple paragraphs.</p>",
        status="draft",  # Use 'draft' for testing
        excerpt="A test article from the automated news bot"
    )

    if test_post:
        print(f"Post ID: {test_post['id']}")
        print(f"Post URL: {test_post['url']}")
        print(f"Status: {test_post['status']}")
