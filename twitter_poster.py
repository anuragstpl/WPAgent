"""
Twitter/X Poster Module - Posts tweets with images to Twitter/X using Tweepy
"""
import os
import base64
import requests
import tweepy
from dotenv import load_dotenv
import logging
from typing import Optional, Dict
import io

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TwitterPoster:
    """Posts content to Twitter/X using Tweepy library"""

    def __init__(self):
        # Load credentials from environment
        self.consumer_key = os.getenv('X_CONSUMER_KEY')
        self.consumer_secret = os.getenv('X_CONSUMER_SECRET')
        self.access_token = os.getenv('X_ACCESS_TOKEN')
        self.access_secret = os.getenv('X_ACCESS_SECRET')

        # Validate credentials
        if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_secret]):
            logger.warning("Twitter/X credentials not fully configured. Please add to .env file")
            self.client = None
            self.api = None
        else:
            try:
                # Create Tweepy client for v2 endpoints
                self.client = tweepy.Client(
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_secret
                )

                # Create API object for v1.1 endpoints (for media upload)
                auth = tweepy.OAuth1UserHandler(
                    self.consumer_key,
                    self.consumer_secret,
                    self.access_token,
                    self.access_secret
                )
                self.api = tweepy.API(auth)

                logger.info("Twitter/X client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter/X client: {str(e)}")
                self.client = None
                self.api = None

    def upload_media(self, image_url: str) -> Optional[str]:
        """
        Upload media to Twitter and get media_id

        Args:
            image_url: URL of the image to upload

        Returns:
            media_id string or None
        """
        if not self.api:
            logger.error("Twitter/X API not configured")
            return None

        try:
            # Download the image
            logger.info(f"Downloading image from {image_url}")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Save temporarily or upload directly from bytes
            logger.info("Uploading image to Twitter/X...")

            # Upload media using Tweepy
            media = self.api.media_upload(filename="temp_image.jpg", file=io.BytesIO(response.content))
            media_id = media.media_id_string

            if media_id:
                logger.info(f"Media uploaded successfully! Media ID: {media_id}")
                return media_id
            else:
                logger.error("No media_id returned from Twitter")
                return None

        except Exception as e:
            logger.error(f"Error uploading media to Twitter: {str(e)}")
            return None

    def upload_media_from_base64(self, base64_data: str) -> Optional[str]:
        """
        Upload media from base64 data to Twitter

        Args:
            base64_data: Base64 encoded image data (with or without data URI prefix)

        Returns:
            media_id string or None
        """
        if not self.api:
            logger.error("Twitter/X API not configured")
            return None

        try:
            # Remove data URI prefix if present
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]

            # Decode base64
            image_bytes = base64.b64decode(base64_data)

            # Upload to Twitter
            logger.info("Uploading base64 image to Twitter/X...")

            media = self.api.media_upload(filename="temp_image.jpg", file=io.BytesIO(image_bytes))
            media_id = media.media_id_string

            if media_id:
                logger.info(f"Media uploaded successfully! Media ID: {media_id}")
                return media_id
            else:
                logger.error("No media_id returned from Twitter")
                return None

        except Exception as e:
            logger.error(f"Error uploading base64 media to Twitter: {str(e)}")
            return None

    def post_tweet(
        self,
        text: str,
        media_ids: Optional[list] = None,
        reply_to: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Post a tweet to Twitter/X

        Args:
            text: Tweet text (max 280 characters)
            media_ids: Optional list of media IDs from upload_media
            reply_to: Optional tweet ID to reply to

        Returns:
            Dictionary with tweet information or None
        """
        if not self.client:
            logger.error("Twitter/X client not configured")
            return None

        if len(text) > 280:
            logger.warning(f"Tweet text is {len(text)} characters, truncating to 280")
            text = text[:277] + "..."

        try:
            logger.info(f"Posting tweet: {text[:50]}...")

            # Post the tweet
            response = self.client.create_tweet(
                text=text,
                media_ids=media_ids,
                in_reply_to_tweet_id=reply_to
            )

            if response and response.data:
                tweet_id = response.data.get('id')
                logger.info(f"Tweet posted successfully! ID: {tweet_id}")

                # Construct tweet URL
                tweet_url = f"https://x.com/i/web/status/{tweet_id}" if tweet_id else None

                return {
                    'id': tweet_id,
                    'text': text,
                    'url': tweet_url
                }
            else:
                logger.error(f"Unexpected response format: {response}")
                return None

        except tweepy.TweepyException as e:
            logger.error(f"Tweepy error posting tweet: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error posting tweet: {str(e)}")
            return None

    def post_tweet_with_image(
        self,
        text: str,
        image_url: str
    ) -> Optional[Dict]:
        """
        Post a tweet with an image (convenience method)

        Args:
            text: Tweet text
            image_url: URL of image to include

        Returns:
            Dictionary with tweet information or None
        """
        # Upload the image first
        media_id = self.upload_media(image_url)

        if not media_id:
            logger.warning("Failed to upload image, posting text-only tweet")
            return self.post_tweet(text)

        # Post tweet with media
        return self.post_tweet(text, media_ids=[media_id])

    def post_tweet_with_base64_image(
        self,
        text: str,
        base64_data: str
    ) -> Optional[Dict]:
        """
        Post a tweet with a base64 encoded image

        Args:
            text: Tweet text
            base64_data: Base64 encoded image

        Returns:
            Dictionary with tweet information or None
        """
        # Upload the image first
        media_id = self.upload_media_from_base64(base64_data)

        if not media_id:
            logger.warning("Failed to upload image, posting text-only tweet")
            return self.post_tweet(text)

        # Post tweet with media
        return self.post_tweet(text, media_ids=[media_id])

    def verify_credentials(self) -> bool:
        """
        Verify Twitter/X API credentials

        Returns:
            True if credentials are valid, False otherwise
        """
        if not self.client:
            logger.error("Twitter/X client not configured")
            return False

        try:
            # Get authenticated user
            user = self.client.get_me()

            if user and user.data:
                username = user.data.get('username')
                logger.info(f"Twitter/X credentials verified for @{username}")
                return True
            else:
                logger.error("Failed to verify credentials")
                return False

        except tweepy.TweepyException as e:
            logger.error(f"Failed to verify Twitter/X credentials: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error verifying credentials: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    poster = TwitterPoster()

    # Verify credentials
    print("\n=== Testing Twitter/X Credentials ===")
    if poster.verify_credentials():
        print("✓ Twitter/X credentials are valid!")

        # Test posting a tweet
        print("\n=== Testing Tweet Post ===")
        test_tweet = "This is a test tweet from the automated news bot! 🤖 #NewsBot #Automation"

        result = poster.post_tweet(test_tweet)

        if result:
            print(f"✓ Tweet posted successfully!")
            print(f"  ID: {result['id']}")
            print(f"  URL: {result['url']}")
            print(f"  Text: {result['text']}")
        else:
            print("✗ Failed to post tweet")
    else:
        print("✗ Twitter/X credentials are invalid")
        print("Please check your .env file and ensure all Twitter/X credentials are set correctly")
