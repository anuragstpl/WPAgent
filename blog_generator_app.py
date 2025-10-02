"""
Blog Generator Web Application
Beautiful UI for generating and publishing blog posts
"""
from flask import Flask, render_template, request, jsonify, session
import os
import sys
from dotenv import load_dotenv
import uuid
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog_generator import BlogGenerator
from image_fetcher import ImageFetcher
from wordpress_publisher import WordPressPublisher
from twitter_poster import TwitterPoster
from content_enhancer import ContentEnhancer

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
blog_gen = BlogGenerator()
image_fetcher = ImageFetcher()
wp_publisher = WordPressPublisher()
twitter_poster = TwitterPoster()
content_enhancer = ContentEnhancer()


@app.route('/')
def index():
    """Main page"""
    themes = blog_gen.get_themes()
    return render_template('blog_generator.html', themes=themes)


@app.route('/api/generate-blog', methods=['POST'])
def generate_blog():
    """Generate blog posts based on theme and keywords"""
    try:
        data = request.json

        theme = data.get('theme')
        keywords_str = data.get('keywords', '')
        count = int(data.get('count', 1))
        word_count = int(data.get('word_count', 800))
        include_images = data.get('include_images', True)

        # Parse keywords
        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()] if keywords_str else None

        logger.info(f"Generating {count} blog(s) for theme: {theme}")

        # Generate blogs
        if count == 1:
            blog = blog_gen.generate_blog_content(
                theme=theme,
                keywords=keywords,
                word_count=word_count
            )
            blogs = [blog] if blog else []
        else:
            blogs = blog_gen.generate_multiple_blogs(
                theme=theme,
                count=count,
                keywords=keywords,
                word_count=word_count
            )

        # Add images if requested
        if include_images:
            for blog in blogs:
                image = image_fetcher.get_image_for_news(
                    title=blog['title'],
                    category=theme,
                    content=blog['content'][:200]
                )
                if image:
                    blog['image_url'] = image['src']['large']
                    blog['image_photographer'] = image.get('photographer')
                else:
                    blog['image_url'] = None

        return jsonify({
            'success': True,
            'blogs': blogs,
            'count': len(blogs)
        })

    except Exception as e:
        logger.error(f"Error generating blog: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/publish-blog', methods=['POST'])
def publish_blog():
    """Publish blog to WordPress"""
    try:
        data = request.json

        title = data.get('title')
        content = data.get('content')
        excerpt = data.get('excerpt')
        tags = data.get('tags', [])
        theme = data.get('theme')
        image_url = data.get('image_url')
        publish_status = data.get('status', 'publish')  # Default to publish
        post_to_twitter = data.get('post_to_twitter', True)  # Default to True

        logger.info(f"Publishing blog: {title} (status: {publish_status}, Twitter: {post_to_twitter})")

        # Convert markdown to HTML
        html_content = blog_gen.markdown_to_html(content)

        # Upload image if available
        media_id = None
        if image_url:
            try:
                media_id = wp_publisher.upload_media(
                    image_url=image_url,
                    title=title,
                    alt_text=title
                )
                if media_id:
                    logger.info(f"✓ Image uploaded (Media ID: {media_id})")
            except Exception as e:
                logger.warning(f"✗ Image upload failed: {e} - continuing without featured image")

        # Get or create category
        category_id = None
        if theme:
            try:
                category_id = wp_publisher.get_or_create_category(theme.title())
                if category_id:
                    logger.info(f"✓ Category ready (ID: {category_id})")
            except Exception as e:
                logger.warning(f"✗ Category creation failed: {e} - continuing without category")

        # Create tags
        tag_ids = []
        for tag_name in tags:
            try:
                tag_id = wp_publisher.get_or_create_tag(tag_name)
                if tag_id:
                    tag_ids.append(tag_id)
            except Exception as e:
                logger.warning(f"✗ Tag creation failed for '{tag_name}': {e}")

        # Create post
        post_result = wp_publisher.create_post(
            title=title,
            content=html_content,
            status=publish_status,
            excerpt=excerpt,
            categories=[category_id] if category_id else None,
            tags=tag_ids if tag_ids else None,
            featured_media=media_id
        )

        if not post_result:
            logger.error("✗ Failed to create WordPress post - CRITICAL ERROR")
            return jsonify({
                'success': False,
                'error': 'Failed to create WordPress post'
            }), 500

        logger.info(f"✓ Post published: {post_result['url']}")

        # Post to Twitter if requested
        tweet_result = None
        if post_to_twitter and post_result:
            try:
                tweet_text = content_enhancer.generate_tweet(
                    title=title,
                    content=content[:200],
                    url=post_result['url']
                )

                if tweet_text:
                    if image_url:
                        tweet_result = twitter_poster.post_tweet_with_image(
                            text=tweet_text,
                            image_url=image_url
                        )
                    else:
                        tweet_result = twitter_poster.post_tweet(tweet_text)

                    if tweet_result:
                        logger.info(f"✓ Tweet posted: {tweet_result['url']}")
                    else:
                        logger.warning("✗ Tweet posting failed - continuing")
            except Exception as e:
                logger.warning(f"✗ Twitter posting failed: {e} - continuing")

        return jsonify({
            'success': True,
            'post': post_result,
            'tweet': tweet_result
        })

    except Exception as e:
        logger.error(f"CRITICAL ERROR publishing blog: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/publish-all', methods=['POST'])
def publish_all():
    """Publish multiple blogs at once"""
    try:
        data = request.json
        blogs = data.get('blogs', [])
        publish_status = data.get('status', 'publish')  # Default to publish
        post_to_twitter = data.get('post_to_twitter', True)  # Default to True

        logger.info(f"Batch publishing {len(blogs)} blogs (status: {publish_status}, Twitter: {post_to_twitter})")
        results = []

        for idx, blog in enumerate(blogs, 1):
            logger.info(f"Processing blog {idx}/{len(blogs)}: {blog.get('title', 'Untitled')}")
            try:
                # Convert markdown to HTML
                html_content = blog_gen.markdown_to_html(blog['content'])

                # Upload image
                media_id = None
                if blog.get('image_url'):
                    try:
                        media_id = wp_publisher.upload_media(
                            image_url=blog['image_url'],
                            title=blog['title'],
                            alt_text=blog['title']
                        )
                        if media_id:
                            logger.info(f"✓ Image uploaded for blog {idx}")
                    except Exception as e:
                        logger.warning(f"✗ Image upload failed for blog {idx}: {e} - continuing")

                # Get category
                category_id = None
                if blog.get('theme'):
                    try:
                        category_id = wp_publisher.get_or_create_category(blog['theme'].title())
                    except Exception as e:
                        logger.warning(f"✗ Category creation failed for blog {idx}: {e}")

                # Create tags
                tag_ids = []
                for tag_name in blog.get('tags', []):
                    try:
                        tag_id = wp_publisher.get_or_create_tag(tag_name)
                        if tag_id:
                            tag_ids.append(tag_id)
                    except Exception as e:
                        logger.warning(f"✗ Tag creation failed for '{tag_name}': {e}")

                # Create post
                post_result = wp_publisher.create_post(
                    title=blog['title'],
                    content=html_content,
                    status=publish_status,
                    excerpt=blog.get('excerpt'),
                    categories=[category_id] if category_id else None,
                    tags=tag_ids if tag_ids else None,
                    featured_media=media_id
                )

                if not post_result:
                    raise Exception(f"WordPress post creation failed for blog {idx}")

                logger.info(f"✓ Blog {idx} published: {post_result['url']}")

                # Post to Twitter
                tweet_result = None
                if post_to_twitter and post_result:
                    try:
                        tweet_text = content_enhancer.generate_tweet(
                            title=blog['title'],
                            content=blog['content'][:200],
                            url=post_result['url']
                        )

                        if tweet_text and blog.get('image_url'):
                            tweet_result = twitter_poster.post_tweet_with_image(
                                text=tweet_text,
                                image_url=blog['image_url']
                            )
                        elif tweet_text:
                            tweet_result = twitter_poster.post_tweet(tweet_text)

                        if tweet_result:
                            logger.info(f"✓ Blog {idx} tweeted: {tweet_result['url']}")
                    except Exception as e:
                        logger.warning(f"✗ Twitter posting failed for blog {idx}: {e} - continuing")

                results.append({
                    'title': blog['title'],
                    'success': True,
                    'post': post_result,
                    'tweet': tweet_result
                })

            except Exception as e:
                logger.error(f"CRITICAL ERROR publishing blog {idx} '{blog.get('title')}': {str(e)}")
                results.append({
                    'title': blog.get('title'),
                    'success': False,
                    'error': str(e)
                })
                # Continue with next blog instead of stopping

        successful = sum(1 for r in results if r['success'])
        logger.info(f"Batch publish completed: {successful}/{len(blogs)} successful")

        return jsonify({
            'success': True,
            'results': results,
            'total': len(blogs),
            'successful': successful
        })

    except Exception as e:
        logger.error(f"CRITICAL ERROR in batch publish: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)

    print("""
╔══════════════════════════════════════════════════════════╗
║         BLOG GENERATOR WEB APPLICATION                   ║
║         Auto-Publishing | Auto-Tweeting                  ║
╚══════════════════════════════════════════════════════════╝

🌐 Open your browser and visit: http://localhost:5001

Features:
✅ Select blog theme (Travel, Food, Tech, etc.)
✅ Add custom keywords for focused content
✅ Generate multiple blogs at once
✅ Beautiful web interface
✅ Automatic image selection
✅ Auto-publish directly to WordPress (live by default)
✅ Auto-post to Twitter/X with images
✅ Continues on non-critical errors
    """)

    app.run(debug=True, port=5001, host='0.0.0.0')
