"""
Content Enhancer Module - Enhances news content and generates HTML using Gemini API
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from typing import Optional, Dict

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentEnhancer:
    """Enhances news content and generates formatted HTML using Gemini AI"""

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY', '').strip('"')
        if not self.api_key:
            logger.warning("Gemini API key not set. Please add GEMINI_API_KEY to .env file")
        else:
            genai.configure(api_key=self.api_key)
            # Using gemini-2.0-flash for stable, production-ready model
            self.model = genai.GenerativeModel('gemini-2.0-flash')

    def enhance_news_content(
        self,
        title: str,
        original_content: str,
        url: str,
        category: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Enhance news content and generate formatted HTML

        Args:
            title: News article title
            original_content: Original news content/summary
            url: Source URL
            category: News category
            image_url: URL of the featured image

        Returns:
            Dictionary containing enhanced content and HTML
        """
        if not self.api_key:
            logger.error("Gemini API key is not configured")
            return None

        try:
            # Create a prompt for Gemini to enhance the content
            prompt = f"""
You are a professional news content writer. I will provide you with a news article summary, and you need to:

1. Expand the content into a comprehensive, well-written article (300-500 words)
2. Maintain factual accuracy - DO NOT add false information
3. Make it engaging and professional
4. Structure it with proper paragraphs
5. Generate clean, semantic HTML format suitable for WordPress
6. Include the featured image at the top with proper attribution
7. Add a "Read more at source" link at the bottom

News Details:
- Title: {title}
- Category: {category or 'General'}
- Original Content: {original_content}
- Source URL: {url}
- Featured Image URL: {image_url or 'No image available'}

Generate a complete HTML article with:
- Featured image (if available) with alt text and caption
- Well-structured paragraphs
- Proper HTML formatting (h2, p, strong, em tags where appropriate)
- Source attribution at the end
- Professional styling classes

Return ONLY the HTML content without any markdown code blocks or explanations.
"""

            logger.info(f"Enhancing content for: {title[:50]}...")

            response = self.model.generate_content(prompt)
            html_content = response.text.strip()

            # Clean up any markdown code blocks if present
            if html_content.startswith('```html'):
                html_content = html_content.replace('```html', '', 1)
            if html_content.startswith('```'):
                html_content = html_content.replace('```', '', 1)
            if html_content.endswith('```'):
                html_content = html_content.rsplit('```', 1)[0]

            html_content = html_content.strip()

            logger.info("Content enhanced successfully")

            return {
                'title': title,
                'html_content': html_content,
                'category': category,
                'source_url': url,
                'image_url': image_url
            }

        except Exception as e:
            logger.error(f"Error enhancing content with Gemini: {str(e)}")
            return None

    def generate_html_with_image(
        self,
        title: str,
        content: str,
        image_url: Optional[str] = None,
        image_alt: str = "",
        photographer: Optional[str] = None,
        photographer_url: Optional[str] = None,
        source_url: Optional[str] = None,
        category: Optional[str] = None
    ) -> str:
        """
        Generate a well-formatted HTML article with image

        Args:
            title: Article title
            content: Article content
            image_url: Featured image URL
            image_alt: Image alt text
            photographer: Photographer name
            photographer_url: Photographer profile URL
            source_url: Original source URL
            category: Article category

        Returns:
            Complete HTML content
        """
        html_parts = []

        # Add featured image if available
        if image_url:
            html_parts.append('<div class="featured-image" style="margin-bottom: 20px;">')
            html_parts.append(
                f'<img src="{image_url}" alt="{image_alt or title}" '
                f'style="width: 100%; height: auto; max-height: 500px; object-fit: cover; border-radius: 8px;" />'
            )

            # Add image attribution
            if photographer:
                attribution = f'<p class="image-credit" style="font-size: 12px; color: #666; margin-top: 8px;">'
                if photographer_url:
                    attribution += f'Photo by <a href="{photographer_url}" target="_blank" rel="noopener">{photographer}</a> on Pexels'
                else:
                    attribution += f'Photo by {photographer} on Pexels'
                attribution += '</p>'
                html_parts.append(attribution)

            html_parts.append('</div>')

        # Add category badge if available
        if category:
            html_parts.append(
                f'<p class="category-badge" style="display: inline-block; background: #0073aa; '
                f'color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; '
                f'font-weight: bold; margin-bottom: 15px;">{category.upper()}</p>'
            )

        # Add main content
        html_parts.append(f'<div class="article-content">{content}</div>')

        # Add source attribution if available
        if source_url:
            html_parts.append(
                f'<div class="source-attribution" style="margin-top: 30px; padding-top: 20px; '
                f'border-top: 1px solid #ddd;">'
                f'<p style="font-size: 14px; color: #666;">'
                f'<strong>Source:</strong> <a href="{source_url}" target="_blank" rel="noopener nofollow">'
                f'Read the original article</a></p></div>'
            )

        return '\n'.join(html_parts)

    def summarize_content(self, content: str, max_words: int = 100) -> Optional[str]:
        """
        Generate a summary of the content

        Args:
            content: Content to summarize
            max_words: Maximum words in summary

        Returns:
            Summary text or None
        """
        if not self.api_key:
            logger.error("Gemini API key is not configured")
            return None

        try:
            prompt = f"""
Summarize the following content in {max_words} words or less. Make it concise and informative:

{content}
"""
            response = self.model.generate_content(prompt)
            summary = response.text.strip()

            logger.info("Content summarized successfully")
            return summary

        except Exception as e:
            logger.error(f"Error summarizing content: {str(e)}")
            return None

    def generate_seo_title(self, title: str) -> Optional[str]:
        """
        Generate an SEO-optimized title

        Args:
            title: Original title

        Returns:
            SEO-optimized title or None
        """
        if not self.api_key:
            logger.error("Gemini API key is not configured")
            return None

        try:
            prompt = f"""
Create an SEO-optimized, engaging title for this news article.
Make it catchy but professional, and keep it under 60 characters:

Original title: {title}

Return ONLY the new title, nothing else.
"""
            response = self.model.generate_content(prompt)
            seo_title = response.text.strip().strip('"').strip("'")

            logger.info(f"SEO title generated: {seo_title}")
            return seo_title

        except Exception as e:
            logger.error(f"Error generating SEO title: {str(e)}")
            return None

    def generate_tweet(
        self,
        title: str,
        content: str,
        url: Optional[str] = None,
        max_chars: int = 280
    ) -> Optional[str]:
        """
        Generate a tweet for the news article (max 280 characters)

        Args:
            title: Article title
            content: Article content
            url: Article URL to include
            max_chars: Maximum tweet length (default 280)

        Returns:
            Tweet text or None
        """
        if not self.api_key:
            logger.error("Gemini API key is not configured")
            return None

        # Reserve space for URL if provided (Twitter shortens URLs to ~23 chars)
        url_chars = 24 if url else 0
        available_chars = max_chars - url_chars

        try:
            prompt = f"""
Create an engaging, attention-grabbing tweet about this news article.

Requirements:
- Maximum {available_chars} characters (STRICT LIMIT)
- Include relevant hashtags (1-2 only)
- Make it compelling and shareable
- Professional tone
- Include emoji if appropriate (1-2 maximum)
{'- DO NOT include the URL, it will be added automatically' if url else ''}

Article Title: {title}
Article Summary: {content[:200]}

Return ONLY the tweet text, nothing else. Make sure it's under {available_chars} characters!
"""
            response = self.model.generate_content(prompt)
            tweet = response.text.strip().strip('"').strip("'")

            # Add URL if provided
            if url:
                # Ensure we have space for URL
                if len(tweet) > available_chars:
                    tweet = tweet[:available_chars - 3] + "..."

                tweet = f"{tweet}\n\n{url}"

            # Final length check
            if len(tweet) > max_chars:
                logger.warning(f"Tweet too long ({len(tweet)} chars), truncating")
                if url:
                    # Keep URL, truncate text
                    max_text = max_chars - len(url) - 3
                    tweet_text = tweet.split('\n\n')[0]
                    tweet = f"{tweet_text[:max_text]}...\n\n{url}"
                else:
                    tweet = tweet[:max_chars - 3] + "..."

            logger.info(f"Tweet generated ({len(tweet)} chars): {tweet[:100]}...")
            return tweet

        except Exception as e:
            logger.error(f"Error generating tweet: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    enhancer = ContentEnhancer()

    # Test content enhancement
    print("\n=== Testing Content Enhancement ===")
    test_article = {
        'title': 'New AI Technology Revolutionizes Healthcare',
        'content': 'A groundbreaking AI system has been developed that can detect diseases with 95% accuracy. The technology uses machine learning to analyze medical images and provide instant diagnoses.',
        'url': 'https://example.com/ai-healthcare',
        'category': 'technology'
    }

    enhanced = enhancer.enhance_news_content(
        title=test_article['title'],
        original_content=test_article['content'],
        url=test_article['url'],
        category=test_article['category'],
        image_url='https://example.com/image.jpg'
    )

    if enhanced:
        print(f"Title: {enhanced['title']}")
        print(f"Category: {enhanced['category']}")
        print(f"\nHTML Content Preview:")
        print(enhanced['html_content'][:500] + "...")

    # Test SEO title generation
    print("\n\n=== Testing SEO Title Generation ===")
    seo_title = enhancer.generate_seo_title(test_article['title'])
    if seo_title:
        print(f"Original: {test_article['title']}")
        print(f"SEO Optimized: {seo_title}")
