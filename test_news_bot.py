"""
Test script for News Bot - Verifies all components are working
"""
import os
import sys
from dotenv import load_dotenv

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

print("""
╔══════════════════════════════════════════════════════════╗
║         NEWS BOT - SYSTEM TEST                           ║
╚══════════════════════════════════════════════════════════╝
""")

# Check environment variables
print("\n1. Checking Environment Variables...")
print("=" * 60)

env_vars = {
    'WORDPRESS_BASE_URL': os.getenv('WORDPRESS_BASE_URL'),
    'BEARER_TOKEN': os.getenv('BEARER_TOKEN'),
    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
    'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
    'PEXELS_API_KEY': os.getenv('PEXELS_API_KEY')
}

all_set = True
for key, value in env_vars.items():
    if value and value != f'your_{key.lower()}_here':
        print(f"✓ {key}: Set")
    else:
        print(f"✗ {key}: NOT SET")
        all_set = False

if all_set:
    print("\n✅ All environment variables are configured!")
else:
    print("\n❌ Some environment variables are missing. Please update .env file")
    exit(1)

# Test imports
print("\n2. Testing Module Imports...")
print("=" * 60)

try:
    from news_fetcher import NewsFetcher
    print("✓ news_fetcher imported successfully")
except Exception as e:
    print(f"✗ news_fetcher import failed: {e}")
    all_set = False

try:
    from image_fetcher import ImageFetcher
    print("✓ image_fetcher imported successfully")
except Exception as e:
    print(f"✗ image_fetcher import failed: {e}")
    all_set = False

try:
    from content_enhancer import ContentEnhancer
    print("✓ content_enhancer imported successfully")
except Exception as e:
    print(f"✗ content_enhancer import failed: {e}")
    all_set = False

try:
    from wordpress_publisher import WordPressPublisher
    print("✓ wordpress_publisher imported successfully")
except Exception as e:
    print(f"✗ wordpress_publisher import failed: {e}")
    all_set = False

try:
    from news_bot import NewsBot
    print("✓ news_bot imported successfully")
except Exception as e:
    print(f"✗ news_bot import failed: {e}")
    all_set = False

if not all_set:
    print("\n❌ Some imports failed. Please check the error messages above.")
    exit(1)

# Test API connections
print("\n3. Testing API Connections...")
print("=" * 60)

# Test Tavily
print("\n3a. Testing Tavily API...")
try:
    from news_fetcher import NewsFetcher
    fetcher = NewsFetcher()
    news = fetcher.fetch_news("test news", max_results=1)
    if news and len(news) > 0:
        print(f"✓ Tavily API working - Found article: {news[0]['title'][:50]}...")
    else:
        print("⚠ Tavily API connected but no results returned")
except Exception as e:
    print(f"✗ Tavily API test failed: {e}")

# Test Pexels
print("\n3b. Testing Pexels API...")
try:
    from image_fetcher import ImageFetcher
    fetcher = ImageFetcher()
    image = fetcher.search_image("technology", per_page=1)
    if image:
        print(f"✓ Pexels API working - Found image by {image['photographer']}")
    else:
        print("⚠ Pexels API connected but no results returned")
except Exception as e:
    print(f"✗ Pexels API test failed: {e}")

# Test Gemini
print("\n3c. Testing Gemini API...")
try:
    from content_enhancer import ContentEnhancer
    enhancer = ContentEnhancer()
    summary = enhancer.summarize_content("This is a test article about technology", max_words=20)
    if summary:
        print(f"✓ Gemini API working - Summary: {summary[:60]}...")
    else:
        print("⚠ Gemini API connected but no results returned")
except Exception as e:
    print(f"✗ Gemini API test failed: {e}")

# Test WordPress
print("\n3d. Testing WordPress Connection...")
try:
    from wordpress_publisher import WordPressPublisher
    import requests

    publisher = WordPressPublisher()
    url = f"{publisher.base_url}/wp-json/wp/v2"
    response = requests.get(url, timeout=10)

    if response.status_code == 200:
        print(f"✓ WordPress REST API accessible at {publisher.base_url}")

        # Try to get posts to verify authentication
        posts_url = f"{publisher.base_url}/wp-json/wp/v2/posts?per_page=1"
        posts_response = requests.get(posts_url, headers=publisher.get_headers(), timeout=10)

        if posts_response.status_code == 200:
            print("✓ WordPress authentication working")
        else:
            print(f"⚠ WordPress authentication issue: Status {posts_response.status_code}")
    else:
        print(f"✗ WordPress REST API not accessible: Status {response.status_code}")
except Exception as e:
    print(f"✗ WordPress connection test failed: {e}")

# Final summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("""
✅ If all tests passed, you can run the news bot with:
   python news_bot.py

⚠ If some tests showed warnings, the bot may still work but with limitations.

❌ If tests failed, please check:
   - API keys in .env file
   - Internet connection
   - API quotas and limits
""")

print("\n" + "=" * 60)
print("Ready to fetch news? Run: python news_bot.py")
print("=" * 60)
