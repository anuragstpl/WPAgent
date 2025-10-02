# Automated News Bot for WordPress

An intelligent news automation system that fetches the latest news from multiple categories, finds relevant images, enhances content using AI, and automatically publishes to your WordPress site.

## 🚀 Features

- **News Fetching**: Retrieves latest news from various categories using Tavily API
- **Image Integration**: Automatically finds relevant images using Pexels API
- **AI Content Enhancement**: Enhances and expands news content using Google Gemini AI
- **HTML Formatting**: Generates clean, professional HTML suitable for WordPress
- **Automated Publishing**: Publishes directly to WordPress with proper formatting
- **Category Management**: Automatically creates and assigns categories
- **Media Upload**: Uploads images to WordPress media library
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

## 📋 Prerequisites

Before you begin, ensure you have:

1. **Python 3.8+** installed
2. **WordPress site** with REST API enabled
3. **API Keys** for:
   - Tavily (for news fetching) - [Get API Key](https://docs.tavily.com/)
   - Pexels (for images) - [Get API Key](https://www.pexels.com/api/)
   - Google Gemini (for AI content) - [Get API Key](https://ai.google.dev/)
   - WordPress Bearer Token

## 🛠️ Installation

### 1. Clone or Download the Project

```bash
cd D:\Chatbots\MCP\Wordpress\Agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Update the `.env` file with your API keys:

```env
# WordPress Configuration
WORDPRESS_BASE_URL=https://vibebuilder.studio
BEARER_TOKEN=your_wordpress_bearer_token

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Tavily API for news fetching
TAVILY_API_KEY=your_tavily_api_key

# Pexels API for images
PEXELS_API_KEY=your_pexels_api_key
```

## 📁 Project Structure

```
Agent/
├── news_bot.py              # Main automation script
├── news_fetcher.py          # Tavily news fetching module
├── image_fetcher.py         # Pexels image fetching module
├── content_enhancer.py      # Gemini AI content enhancement
├── wordpress_publisher.py   # WordPress publishing module
├── .env                     # Environment variables (API keys)
├── requirements.txt         # Python dependencies
└── news_bot.log            # Auto-generated log file
```

## 🎯 Usage

### Quick Start

Run the main bot script:

```bash
python news_bot.py
```

You'll see an interactive menu with options:

```
1. Fetch news from a single category
2. Fetch news from multiple categories
3. Fetch trending news
4. Run custom script
```

### Option 1: Single Category

Fetch news from a specific category:

```python
# Available categories:
# technology, business, sports, health, science, entertainment, politics, world

python news_bot.py
# Select option 1
# Enter category: technology
# Number of articles: 3
# Publish status: draft
```

### Option 2: Multiple Categories

Fetch news from multiple categories in one run:

```python
python news_bot.py
# Select option 2
# Publish status: draft
```

This will fetch 2 articles each from:
- Technology
- Business
- Sports
- Health
- Science

### Option 3: Trending News

Fetch trending/breaking news:

```python
python news_bot.py
# Select option 3
# Number of articles: 5
# Publish status: draft
```

### Option 4: Custom Script

Run a custom automation workflow (modify the script as needed).

## 🔧 Advanced Usage

### Using Individual Modules

#### 1. News Fetcher

```python
from news_fetcher import NewsFetcher

fetcher = NewsFetcher()

# Fetch technology news
tech_news = fetcher.fetch_news_by_category('technology', max_results=5)

# Fetch custom news
custom_news = fetcher.fetch_news(
    query="artificial intelligence breakthroughs",
    max_results=3,
    search_depth="advanced"
)

# Fetch trending news
trending = fetcher.fetch_trending_news(max_results=10)
```

#### 2. Image Fetcher

```python
from image_fetcher import ImageFetcher

fetcher = ImageFetcher()

# Search for specific image
image = fetcher.search_image('technology innovation', orientation='landscape')

# Get image for news article
image = fetcher.get_image_for_news(
    title="AI Revolution in Healthcare",
    category="technology"
)

print(image['src']['large'])  # Image URL
print(image['photographer'])  # Photographer name
```

#### 3. Content Enhancer

```python
from content_enhancer import ContentEnhancer

enhancer = ContentEnhancer()

# Enhance news content
enhanced = enhancer.enhance_news_content(
    title="Breaking: New AI Technology",
    original_content="Short news summary...",
    url="https://example.com/news",
    category="technology",
    image_url="https://example.com/image.jpg"
)

print(enhanced['html_content'])  # Enhanced HTML content

# Generate SEO title
seo_title = enhancer.generate_seo_title("Original Title")
```

#### 4. WordPress Publisher

```python
from wordpress_publisher import WordPressPublisher

publisher = WordPressPublisher()

# Upload image
media_id = publisher.upload_media(
    image_url="https://example.com/image.jpg",
    title="Image Title",
    alt_text="Image description"
)

# Create category
category_id = publisher.get_or_create_category("Technology")

# Create post
post = publisher.create_post(
    title="Article Title",
    content="<p>HTML content here</p>",
    status="publish",  # or 'draft'
    categories=[category_id],
    featured_media=media_id
)

print(post['url'])  # Post URL
```

### Programmatic Usage

```python
from news_bot import NewsBot

# Initialize bot
bot = NewsBot()

# Run for single category
posts = bot.run_single_category(
    category='technology',
    max_articles=5,
    publish_status='draft'
)

# Run for multiple categories
results = bot.run_multiple_categories(
    categories=['technology', 'business', 'sports'],
    articles_per_category=3,
    publish_status='publish'
)

# Run for trending news
trending_posts = bot.run_trending_news(
    max_articles=10,
    publish_status='draft'
)
```

## 🔄 Workflow

The bot follows this automated workflow for each article:

1. **Fetch News**: Retrieves latest news from Tavily API
2. **Find Image**: Searches for relevant image on Pexels
3. **Enhance Content**: Uses Gemini AI to expand and improve content
4. **Upload Image**: Uploads image to WordPress media library
5. **Create Category**: Gets or creates the appropriate category
6. **Publish Post**: Creates WordPress post with all content

## 📝 Logging

The bot generates detailed logs in `news_bot.log`:

```
2024-01-15 10:30:45 - NewsBot - INFO - Processing article: Breaking AI News...
2024-01-15 10:30:46 - ImageFetcher - INFO - Searching Pexels for: technology
2024-01-15 10:30:47 - ImageFetcher - INFO - Found image by John Doe
2024-01-15 10:30:48 - ContentEnhancer - INFO - Enhancing content...
2024-01-15 10:30:50 - WordPressPublisher - INFO - Uploading image to WordPress
2024-01-15 10:30:52 - WordPressPublisher - INFO - Post created successfully!
```

## ⚙️ Configuration

### News Categories

Available categories:
- `technology` - Tech news and innovations
- `business` - Business and finance news
- `sports` - Sports updates
- `health` - Health and medical news
- `science` - Scientific research and discoveries
- `entertainment` - Entertainment and celebrity news
- `politics` - Political news and updates
- `world` - International news

### Publish Status

- `draft` - Creates posts as drafts (recommended for testing)
- `publish` - Publishes posts immediately

### API Rate Limits

Be mindful of API rate limits:
- **Tavily**: Check your plan limits
- **Pexels**: 200 requests/hour for free tier
- **Gemini**: Check your quota

The bot includes delays between requests to avoid rate limiting.

## 🐛 Troubleshooting

### Common Issues

1. **"API key not configured"**
   - Ensure all API keys are set in `.env` file
   - Remove quotes around API keys if present

2. **"Authentication failed"**
   - Check WordPress Bearer Token is valid
   - Ensure WordPress REST API is enabled

3. **"No images found"**
   - Pexels API key may be invalid
   - Try different search terms
   - Check Pexels API quota

4. **"Failed to enhance content"**
   - Gemini API key may be invalid
   - Check API quota limits
   - Ensure internet connection is stable

### Debug Mode

Enable detailed logging by setting log level to DEBUG in the scripts:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Example Output

```
╔══════════════════════════════════════════════════════════╗
║         AUTOMATED NEWS BOT FOR WORDPRESS                 ║
║         Powered by Tavily, Pexels & Gemini AI            ║
╚══════════════════════════════════════════════════════════╝

============================================================
Processing article: AI Breakthrough in Medical Diagnosis...
============================================================
Step 1: Fetching relevant image...
✓ Image found by Jane Smith

Step 2: Enhancing content with AI...
✓ Content enhanced successfully

Step 3: Uploading image to WordPress...
✓ Image uploaded (Media ID: 123)

Step 4: Getting/creating category: technology
✓ Category ready (ID: 5)

Step 5: Creating WordPress post...
✓ Post created successfully!
  - Post ID: 456
  - URL: https://vibebuilder.studio/ai-breakthrough
  - Status: draft

============================================================
Summary for technology:
  - Articles fetched: 3
  - Posts created: 3
============================================================
```

## 🔐 Security Notes

- **Never commit** your `.env` file with real API keys
- Use **environment variables** in production
- Set posts to **'draft'** status for review before publishing
- **Review** AI-generated content before publishing
- Keep your **WordPress** installation updated

## 📚 API Documentation

- [Tavily API Docs](https://docs.tavily.com/documentation/api-reference/endpoint/search)
- [Pexels API Docs](https://www.pexels.com/api/documentation/)
- [Google Gemini API Docs](https://ai.google.dev/docs)
- [WordPress REST API](https://developer.wordpress.org/rest-api/)

## 🤝 Contributing

Feel free to customize and extend the bot:
- Add new news sources
- Implement custom content filters
- Add social media sharing
- Create scheduling functionality
- Add more AI features

## 📄 License

This project is for educational and personal use. Ensure you comply with:
- Tavily API Terms of Service
- Pexels API License
- Google Gemini API Terms
- WordPress usage policies

## 🆘 Support

For issues or questions:
1. Check the logs in `news_bot.log`
2. Review API documentation
3. Verify all API keys are correct
4. Ensure WordPress REST API is accessible

---

**Happy Automating! 🤖**
