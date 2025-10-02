"""
Automated News Bot - Main Script
Fetches news, gets images, enhances content, and publishes to WordPress
"""
import os
import sys
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

from news_fetcher import NewsFetcher
from image_fetcher import ImageFetcher
from content_enhancer import ContentEnhancer
from wordpress_publisher import WordPressPublisher
from twitter_poster import TwitterPoster

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NewsBot:
    """Automated News Bot for fetching, enhancing, and publishing news"""

    def __init__(self, post_to_twitter=True):
        logger.info("Initializing News Bot...")
        self.news_fetcher = NewsFetcher()
        self.image_fetcher = ImageFetcher()
        self.content_enhancer = ContentEnhancer()
        self.wordpress_publisher = WordPressPublisher()
        self.post_to_twitter = post_to_twitter

        if self.post_to_twitter:
            try:
                self.twitter_poster = TwitterPoster()
                logger.info("Twitter posting enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Twitter poster: {e} - continuing without Twitter")
                self.twitter_poster = None
                self.post_to_twitter = False
        else:
            self.twitter_poster = None
            logger.info("Twitter posting disabled")

        logger.info("News Bot initialized successfully!")

    def process_news_article(
        self,
        article: Dict,
        category: Optional[str] = None,
        publish_status: str = 'publish'
    ) -> Optional[Dict]:
        """
        Process a single news article through the complete pipeline

        Args:
            article: News article dictionary from Tavily
            category: News category
            publish_status: WordPress post status ('publish' or 'draft')

        Returns:
            Dictionary containing post information or None
        """
        try:
            title = article.get('title', 'Untitled')
            content = article.get('content', '')
            url = article.get('url', '')

            logger.info(f"\n{'='*60}")
            logger.info(f"Processing article: {title[:60]}...")
            logger.info(f"{'='*60}")

            # Step 1: Fetch relevant image from Pexels
            logger.info("Step 1: Fetching relevant image...")
            try:
                image_data = self.image_fetcher.get_image_for_news(
                    title=title,
                    category=category,
                    content=content
                )

                image_url = None
                photographer = None
                photographer_url = None

                if image_data:
                    image_url = image_data['src']['large']
                    photographer = image_data.get('photographer')
                    photographer_url = image_data.get('photographer_url')
                    logger.info(f"✓ Image found by {photographer}")
                else:
                    logger.warning("✗ No image found, continuing without image")
            except Exception as e:
                logger.warning(f"✗ Image fetch failed: {e} - continuing without image")
                image_url = None
                photographer = None
                photographer_url = None

            # Step 2: Enhance content with Gemini AI
            logger.info("Step 2: Enhancing content with AI...")
            enhanced_content = self.content_enhancer.enhance_news_content(
                title=title,
                original_content=content,
                url=url,
                category=category,
                image_url=image_url
            )

            if not enhanced_content:
                logger.error("✗ Failed to enhance content - CRITICAL ERROR")
                raise Exception("Content enhancement failed - cannot continue")

            logger.info("✓ Content enhanced successfully")

            # Step 3: Upload image to WordPress (if available)
            media_id = None
            if image_url:
                logger.info("Step 3: Uploading image to WordPress...")
                try:
                    media_id = self.wordpress_publisher.upload_media(
                        image_url=image_url,
                        title=title,
                        alt_text=title,
                        caption=f"Photo by {photographer} on Pexels" if photographer else None
                    )
                    if media_id:
                        logger.info(f"✓ Image uploaded (Media ID: {media_id})")
                    else:
                        logger.warning("✗ Image upload failed - continuing without featured image")
                except Exception as e:
                    logger.warning(f"✗ Image upload failed: {e} - continuing without featured image")
                    media_id = None

            # Step 4: Get or create category
            category_id = None
            if category:
                logger.info(f"Step 4: Getting/creating category: {category}")
                try:
                    category_id = self.wordpress_publisher.get_or_create_category(category)
                    if category_id:
                        logger.info(f"✓ Category ready (ID: {category_id})")
                except Exception as e:
                    logger.warning(f"✗ Category creation failed: {e} - continuing without category")

            # Step 5: Create WordPress post
            logger.info("Step 5: Creating WordPress post...")

            # Generate excerpt
            try:
                excerpt = self.content_enhancer.summarize_content(content, max_words=50)
            except Exception as e:
                logger.warning(f"✗ Excerpt generation failed: {e} - using default excerpt")
                excerpt = content[:200] + "..." if len(content) > 200 else content

            post_result = self.wordpress_publisher.create_post(
                title=title,
                content=enhanced_content['html_content'],
                status=publish_status,
                excerpt=excerpt,
                categories=[category_id] if category_id else None,
                featured_media=media_id
            )

            if not post_result:
                logger.error("✗ Failed to create WordPress post - CRITICAL ERROR")
                raise Exception("WordPress post creation failed - cannot continue")

            logger.info(f"✓ Post created successfully!")
            logger.info(f"  - Post ID: {post_result['id']}")
            logger.info(f"  - URL: {post_result['url']}")
            logger.info(f"  - Status: {post_result['status']}")

            # Step 6: Post to Twitter/X (if enabled)
            tweet_result = None
            if self.post_to_twitter and self.twitter_poster:
                logger.info("Step 6: Posting to Twitter/X...")
                try:
                    # Generate tweet
                    tweet_text = self.content_enhancer.generate_tweet(
                        title=title,
                        content=content,
                        url=post_result['url'],
                        max_chars=280
                    )

                    if tweet_text:
                        logger.info(f"Tweet generated ({len(tweet_text)} chars)")

                        # Post tweet with image
                        if image_url:
                            tweet_result = self.twitter_poster.post_tweet_with_image(
                                text=tweet_text,
                                image_url=image_url
                            )
                        else:
                            # Post text-only tweet
                            tweet_result = self.twitter_poster.post_tweet(tweet_text)

                        if tweet_result:
                            logger.info(f"✓ Tweet posted successfully!")
                            logger.info(f"  - Tweet ID: {tweet_result['id']}")
                            logger.info(f"  - Tweet URL: {tweet_result['url']}")
                            post_result['tweet'] = tweet_result
                        else:
                            logger.warning("✗ Failed to post tweet - continuing")
                    else:
                        logger.warning("✗ Failed to generate tweet - continuing")
                except Exception as e:
                    logger.warning(f"✗ Twitter posting failed: {e} - continuing without tweet")

            return post_result

        except Exception as e:
            logger.error(f"CRITICAL ERROR processing article: {str(e)}", exc_info=True)
            raise  # Re-raise critical errors to stop execution

    def run_single_category(
        self,
        category: str,
        max_articles: int = 3,
        publish_status: str = 'publish'
    ) -> List[Dict]:
        """
        Fetch and publish news for a single category

        Args:
            category: News category
            max_articles: Maximum number of articles to process
            publish_status: WordPress post status

        Returns:
            List of created posts
        """
        logger.info(f"\n{'#'*60}")
        logger.info(f"# Running bot for category: {category.upper()}")
        logger.info(f"# Max articles: {max_articles}")
        logger.info(f"# Publish status: {publish_status}")
        logger.info(f"{'#'*60}\n")

        # Fetch news articles
        articles = self.news_fetcher.fetch_news_by_category(category, max_results=max_articles)

        if not articles:
            logger.warning(f"No articles found for category: {category}")
            return []

        logger.info(f"Found {len(articles)} articles for {category}")

        # Process each article
        created_posts = []
        for idx, article in enumerate(articles, 1):
            logger.info(f"\nProcessing article {idx}/{len(articles)}")

            post = self.process_news_article(
                article=article,
                category=category,
                publish_status=publish_status
            )

            if post:
                created_posts.append(post)

            # Add delay between articles to avoid rate limiting
            if idx < len(articles):
                logger.info("Waiting 5 seconds before next article...")
                time.sleep(5)

        logger.info(f"\n{'='*60}")
        logger.info(f"Summary for {category}:")
        logger.info(f"  - Articles fetched: {len(articles)}")
        logger.info(f"  - Posts created: {len(created_posts)}")
        logger.info(f"{'='*60}\n")

        return created_posts

    def run_multiple_categories(
        self,
        categories: List[str],
        articles_per_category: int = 2,
        publish_status: str = 'publish'
    ) -> Dict[str, List[Dict]]:
        """
        Fetch and publish news for multiple categories

        Args:
            categories: List of news categories
            articles_per_category: Number of articles per category
            publish_status: WordPress post status

        Returns:
            Dictionary mapping categories to created posts
        """
        logger.info(f"\n{'#'*60}")
        logger.info(f"# Starting Multi-Category News Bot Run")
        logger.info(f"# Categories: {', '.join(categories)}")
        logger.info(f"# Articles per category: {articles_per_category}")
        logger.info(f"# Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'#'*60}\n")

        results = {}

        for idx, category in enumerate(categories, 1):
            logger.info(f"\n{'*'*60}")
            logger.info(f"* Category {idx}/{len(categories)}: {category}")
            logger.info(f"{'*'*60}\n")

            posts = self.run_single_category(
                category=category,
                max_articles=articles_per_category,
                publish_status=publish_status
            )

            results[category] = posts

            # Add delay between categories
            if idx < len(categories):
                logger.info("Waiting 10 seconds before next category...")
                time.sleep(10)

        # Print final summary
        total_posts = sum(len(posts) for posts in results.values())
        logger.info(f"\n{'#'*60}")
        logger.info(f"# FINAL SUMMARY")
        logger.info(f"# Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"#")
        logger.info(f"# Total categories processed: {len(categories)}")
        logger.info(f"# Total posts created: {total_posts}")
        logger.info(f"#")
        for category, posts in results.items():
            logger.info(f"#   {category}: {len(posts)} posts")
        logger.info(f"{'#'*60}\n")

        return results

    def run_trending_news(
        self,
        max_articles: int = 5,
        publish_status: str = 'publish'
    ) -> List[Dict]:
        """
        Fetch and publish trending news

        Args:
            max_articles: Maximum number of articles
            publish_status: WordPress post status

        Returns:
            List of created posts
        """
        logger.info(f"\n{'#'*60}")
        logger.info(f"# Running bot for TRENDING NEWS")
        logger.info(f"# Max articles: {max_articles}")
        logger.info(f"{'#'*60}\n")

        # Fetch trending news
        articles = self.news_fetcher.fetch_trending_news(max_results=max_articles)

        if not articles:
            logger.warning("No trending articles found")
            return []

        logger.info(f"Found {len(articles)} trending articles")

        # Process each article
        created_posts = []
        for idx, article in enumerate(articles, 1):
            logger.info(f"\nProcessing article {idx}/{len(articles)}")

            post = self.process_news_article(
                article=article,
                category='Trending',
                publish_status=publish_status
            )

            if post:
                created_posts.append(post)

            # Add delay between articles
            if idx < len(articles):
                logger.info("Waiting 5 seconds before next article...")
                time.sleep(5)

        logger.info(f"\n{'='*60}")
        logger.info(f"Summary for Trending News:")
        logger.info(f"  - Articles fetched: {len(articles)}")
        logger.info(f"  - Posts created: {len(created_posts)}")
        logger.info(f"{'='*60}\n")

        return created_posts


def main():
    """Main function to run the news bot"""
    print("""
╔══════════════════════════════════════════════════════════╗
║         AUTOMATED NEWS BOT FOR WORDPRESS                 ║
║         Powered by Tavily, Pexels & Gemini AI            ║
║         Auto-Publishing | Auto-Tweeting                  ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Initialize the bot with Twitter enabled by default
    bot = NewsBot(post_to_twitter=True)
    print("✓ Auto-publish and auto-tweet enabled")
    print("✓ Will stop only on critical errors\n")

    # Choose what to run
    print("Select an option:")
    print("1. Fetch news from a single category")
    print("2. Fetch news from multiple categories")
    print("3. Fetch trending news")
    print("4. Run custom script")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == '1':
        # Single category
        print("\nAvailable categories:")
        print("technology, business, sports, health, science, entertainment, politics, world")
        category = input("\nEnter category: ").strip()
        max_articles = int(input("Number of articles (1-10): ").strip() or "3")

        bot.run_single_category(category, max_articles, publish_status='publish')

    elif choice == '2':
        # Multiple categories
        categories = ['technology', 'business', 'sports', 'health', 'science']
        articles_per_category = 2

        bot.run_multiple_categories(categories, articles_per_category, publish_status='publish')

    elif choice == '3':
        # Trending news
        max_articles = int(input("Number of trending articles (1-10): ").strip() or "5")

        bot.run_trending_news(max_articles, publish_status='publish')

    elif choice == '4':
        # Custom script example
        print("\nRunning custom script...")
        # Example: Post 2 technology and 2 business articles
        bot.run_single_category('technology', max_articles=2, publish_status='publish')
        bot.run_single_category('business', max_articles=2, publish_status='publish')

    else:
        print("Invalid choice!")

    print("\n✅ Bot execution completed!")


if __name__ == "__main__":
    main()
