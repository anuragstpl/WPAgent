"""
Blog Content Generator Module - Generates blog posts based on themes and keywords
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, List
import random

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlogGenerator:
    """Generates complete blog posts using Gemini AI based on themes and keywords"""

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY', '').strip('"')
        if not self.api_key:
            logger.warning("Gemini API key not set. Please add GEMINI_API_KEY to .env file")
        else:
            genai.configure(api_key=self.api_key)
            # Using gemini-2.0-flash for stable, production-ready model
            self.model = genai.GenerativeModel('gemini-2.0-flash')

        # Predefined themes with sample keywords
        self.themes = {
            'travel': {
                'description': 'Travel, tourism, destinations, adventures',
                'keywords': ['destinations', 'travel tips', 'adventure', 'vacation', 'tourist attractions', 'hotels', 'flights', 'backpacking', 'cruise', 'road trip']
            },
            'food': {
                'description': 'Food, recipes, cooking, restaurants, cuisine',
                'keywords': ['recipes', 'cooking tips', 'restaurants', 'cuisine', 'healthy eating', 'desserts', 'vegetarian', 'baking', 'street food', 'meal prep']
            },
            'technology': {
                'description': 'Technology, gadgets, software, AI, innovation',
                'keywords': ['AI', 'smartphones', 'apps', 'software', 'gadgets', 'coding', 'cloud computing', 'cybersecurity', 'blockchain', 'IoT']
            },
            'health': {
                'description': 'Health, fitness, wellness, nutrition, mental health',
                'keywords': ['fitness', 'nutrition', 'mental health', 'yoga', 'meditation', 'exercise', 'diet', 'wellness', 'sleep', 'stress management']
            },
            'lifestyle': {
                'description': 'Lifestyle, fashion, beauty, home decor, personal development',
                'keywords': ['fashion', 'beauty', 'home decor', 'productivity', 'minimalism', 'self-care', 'hobbies', 'organization', 'skincare', 'DIY']
            },
            'business': {
                'description': 'Business, entrepreneurship, marketing, finance',
                'keywords': ['entrepreneurship', 'marketing', 'finance', 'startups', 'leadership', 'productivity', 'sales', 'investing', 'e-commerce', 'branding']
            },
            'education': {
                'description': 'Education, learning, study tips, online courses',
                'keywords': ['study tips', 'online learning', 'education technology', 'teaching', 'student life', 'career development', 'skills', 'certifications', 'e-learning', 'scholarships']
            },
            'entertainment': {
                'description': 'Entertainment, movies, music, gaming, celebrity',
                'keywords': ['movies', 'music', 'gaming', 'celebrities', 'TV shows', 'streaming', 'concerts', 'books', 'podcasts', 'reviews']
            },
            'sports': {
                'description': 'Sports, fitness, athletics, competitions',
                'keywords': ['football', 'basketball', 'training', 'athletes', 'competitions', 'Olympics', 'sports news', 'cricket', 'tennis', 'fitness']
            },
            'parenting': {
                'description': 'Parenting, kids, family, child development',
                'keywords': ['parenting tips', 'child development', 'family activities', 'pregnancy', 'baby care', 'education', 'behavior', 'health', 'toys', 'teenagers']
            }
        }

    def get_themes(self) -> Dict:
        """Get all available themes"""
        return self.themes

    def generate_blog_title(
        self,
        theme: str,
        keywords: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Generate an engaging blog title

        Args:
            theme: Blog theme
            keywords: Optional list of keywords

        Returns:
            Blog title or None
        """
        if not self.api_key:
            logger.error("Gemini API key is not configured")
            return None

        try:
            keyword_str = ', '.join(keywords) if keywords else ''
            theme_desc = self.themes.get(theme, {}).get('description', theme)

            prompt = f"""
Generate a catchy, SEO-friendly blog post title about {theme_desc}.

{f'Focus on these keywords: {keyword_str}' if keyword_str else ''}

Requirements:
- Make it engaging and click-worthy
- Keep it under 60 characters for SEO
- Professional and informative tone
- Include numbers if relevant (e.g., "10 Tips...", "5 Ways...")

Return ONLY the title, nothing else.
"""
            response = self.model.generate_content(prompt)
            title = response.text.strip().strip('"').strip("'")

            logger.info(f"Generated title: {title}")
            return title

        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            return None

    def generate_blog_content(
        self,
        theme: str,
        keywords: Optional[List[str]] = None,
        title: Optional[str] = None,
        word_count: int = 800
    ) -> Optional[Dict]:
        """
        Generate complete blog post content

        Args:
            theme: Blog theme
            keywords: Optional list of keywords to focus on
            title: Optional custom title (if None, will be generated)
            word_count: Target word count (default 800)

        Returns:
            Dictionary with title, content, excerpt, tags, or None
        """
        if not self.api_key:
            logger.error("Gemini API key is not configured")
            return None

        try:
            # Generate title if not provided
            if not title:
                title = self.generate_blog_title(theme, keywords)
                if not title:
                    logger.error("Failed to generate title")
                    return None

            keyword_str = ', '.join(keywords) if keywords else ''
            theme_desc = self.themes.get(theme, {}).get('description', theme)

            prompt = f"""
Write a comprehensive, high-quality blog post with the following specifications:

**Title:** {title}
**Theme:** {theme_desc}
{f'**Focus Keywords:** {keyword_str}' if keyword_str else ''}
**Target Word Count:** {word_count} words

Requirements:
1. Write engaging, informative content that provides real value
2. Use a conversational yet professional tone
3. Include proper structure with introduction, body, and conclusion
4. Add subheadings (use ## for H2, ### for H3)
5. Use bullet points or numbered lists where appropriate
6. Make it SEO-friendly with natural keyword integration
7. Include practical tips, examples, or insights
8. Write in markdown format

Return ONLY the blog content in markdown format, starting with ## Introduction
DO NOT include the main title (it will be added separately).
"""

            logger.info(f"Generating blog content for: {title}")
            response = self.model.generate_content(prompt)
            content = response.text.strip()

            # Generate excerpt
            excerpt_prompt = f"""
Create a compelling 2-3 sentence excerpt/summary for this blog post:

Title: {title}
Content: {content[:500]}...

Make it engaging and encourage readers to read more.
Return ONLY the excerpt, nothing else.
"""
            excerpt_response = self.model.generate_content(excerpt_prompt)
            excerpt = excerpt_response.text.strip().strip('"').strip("'")

            # Generate tags
            tags = self.generate_tags(theme, keywords, content)

            logger.info(f"Blog content generated successfully ({len(content.split())} words)")

            return {
                'title': title,
                'content': content,
                'excerpt': excerpt,
                'tags': tags,
                'theme': theme,
                'keywords': keywords or [],
                'word_count': len(content.split())
            }

        except Exception as e:
            logger.error(f"Error generating blog content: {str(e)}")
            return None

    def generate_tags(
        self,
        theme: str,
        keywords: Optional[List[str]],
        content: str
    ) -> List[str]:
        """
        Generate relevant tags for the blog post

        Args:
            theme: Blog theme
            keywords: Keywords used
            content: Blog content

        Returns:
            List of tags
        """
        try:
            prompt = f"""
Based on this blog post content and theme, generate 5-8 relevant tags/categories.

Theme: {theme}
Content: {content[:300]}...

Return ONLY a comma-separated list of tags, nothing else.
Example: technology, AI, innovation, future, gadgets
"""
            response = self.model.generate_content(prompt)
            tags_str = response.text.strip()

            # Parse tags
            tags = [tag.strip() for tag in tags_str.split(',')]
            tags = [tag for tag in tags if tag]  # Remove empty tags

            return tags[:8]  # Limit to 8 tags

        except Exception as e:
            logger.error(f"Error generating tags: {str(e)}")
            # Return default tags based on theme and keywords
            default_tags = [theme]
            if keywords:
                default_tags.extend(keywords[:5])
            return default_tags

    def generate_multiple_blogs(
        self,
        theme: str,
        count: int = 3,
        keywords: Optional[List[str]] = None,
        word_count: int = 800
    ) -> List[Dict]:
        """
        Generate multiple blog posts

        Args:
            theme: Blog theme
            count: Number of blogs to generate
            keywords: Optional keywords
            word_count: Target word count per blog

        Returns:
            List of blog dictionaries
        """
        blogs = []

        for i in range(count):
            logger.info(f"Generating blog {i+1}/{count}...")

            # Generate unique title for each blog
            title = self.generate_blog_title(theme, keywords)

            if title:
                blog = self.generate_blog_content(
                    theme=theme,
                    keywords=keywords,
                    title=title,
                    word_count=word_count
                )

                if blog:
                    blogs.append(blog)
                    logger.info(f"✓ Blog {i+1}/{count} generated: {title[:50]}...")
                else:
                    logger.warning(f"✗ Failed to generate blog {i+1}")
            else:
                logger.warning(f"✗ Failed to generate title for blog {i+1}")

        logger.info(f"Generated {len(blogs)}/{count} blogs successfully")
        return blogs

    def markdown_to_html(self, markdown_content: str) -> str:
        """
        Convert markdown to HTML (basic conversion)

        Args:
            markdown_content: Markdown text

        Returns:
            HTML content
        """
        import re

        html = markdown_content

        # Convert headers
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Convert bold
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)

        # Convert italic
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)

        # Convert paragraphs
        paragraphs = html.split('\n\n')
        html = ''.join([f'<p>{p}</p>\n' if not p.startswith('<h') else f'{p}\n' for p in paragraphs if p.strip()])

        return html


# Example usage
if __name__ == "__main__":
    generator = BlogGenerator()

    print("\n=== Available Themes ===")
    for theme, info in generator.get_themes().items():
        print(f"{theme.upper()}: {info['description']}")

    print("\n=== Testing Blog Generation ===")

    # Test single blog generation
    blog = generator.generate_blog_content(
        theme='technology',
        keywords=['AI', 'machine learning', 'future'],
        word_count=600
    )

    if blog:
        print(f"\nTitle: {blog['title']}")
        print(f"Theme: {blog['theme']}")
        print(f"Word Count: {blog['word_count']}")
        print(f"Tags: {', '.join(blog['tags'])}")
        print(f"\nExcerpt: {blog['excerpt']}")
        print(f"\nContent Preview:\n{blog['content'][:300]}...")
