# Quick Start Guide - Automated News Bot

## ⚡ Fast Setup (5 Minutes)

### Step 1: Verify API Keys

All API keys are already configured in your `.env` file:
- ✅ WordPress Bearer Token
- ✅ Gemini API Key
- ✅ Tavily API Key
- ✅ Pexels API Key

### Step 2: Test the System

```bash
python test_news_bot.py
```

If all tests pass (✅), you're ready to go!

### Step 3: Run Your First News Bot

```bash
python news_bot.py
```

## 🎯 Quick Examples

### Example 1: Fetch 3 Technology News Articles (as Drafts)

```bash
python news_bot.py
```
- Select: `1` (Single category)
- Category: `technology`
- Number of articles: `3`
- Status: `draft`

**Result**: 3 technology news posts will be created as drafts on your WordPress site

### Example 2: Fetch News from Multiple Categories

```bash
python news_bot.py
```
- Select: `2` (Multiple categories)
- Status: `draft`

**Result**: 2 articles each from Technology, Business, Sports, Health, and Science (10 total posts)

### Example 3: Fetch Trending News

```bash
python news_bot.py
```
- Select: `3` (Trending news)
- Number of articles: `5`
- Status: `draft`

**Result**: 5 trending news posts

## 📝 What Happens When You Run the Bot?

For each article, the bot will:

1. **Fetch News** - Get latest news from Tavily API
2. **Find Image** - Search for relevant image on Pexels
3. **Enhance Content** - Use Gemini AI to expand and improve the content
4. **Upload Image** - Upload to WordPress media library
5. **Create Category** - Automatically create/assign category
6. **Publish Post** - Create WordPress post with everything

## 🔍 Where to Find Your Posts?

1. Go to your WordPress admin: `https://vibebuilder.studio/wp-admin`
2. Navigate to **Posts** → **All Posts**
3. You'll see your new posts with status "Draft"
4. Review and click "Publish" when ready!

## 💡 Pro Tips

### Tip 1: Always Start with Drafts
```
Status: draft  ← Review before publishing
```

### Tip 2: Check the Logs
```
tail -f news_bot.log  # Watch logs in real-time
```

### Tip 3: Start Small
```
Number of articles: 2  ← Test with 2 articles first
```

## 📊 Available Categories

- `technology` - Tech news and innovations
- `business` - Business and finance
- `sports` - Sports updates
- `health` - Health and medical news
- `science` - Scientific discoveries
- `entertainment` - Entertainment news
- `politics` - Political news
- `world` - International news

## ⚙️ Common Commands

### Run the bot
```bash
python news_bot.py
```

### Test the system
```bash
python test_news_bot.py
```

### Check individual modules

```bash
# Test news fetching
python news_fetcher.py

# Test image fetching
python image_fetcher.py

# Test content enhancement
python content_enhancer.py

# Test WordPress publishing
python wordpress_publisher.py
```

## 🛠️ Troubleshooting

### Issue: "API key not configured"
**Solution**: Check `.env` file has all API keys without quotes

### Issue: "Authentication failed"
**Solution**: Verify WordPress Bearer Token is correct

### Issue: "No images found"
**Solution**: Normal - some topics may not have perfect image matches. Post will be created without image.

### Issue: Rate limiting
**Solution**: Wait a few minutes and try again. The bot has built-in delays to prevent this.

## 🎨 Customization

### Change Number of Articles per Category

Edit `news_bot.py`, line ~461:
```python
articles_per_category = 5  # Change from 2 to 5
```

### Change Default Categories

Edit `news_bot.py`, line ~460:
```python
categories = ['technology', 'business', 'health', 'world']
```

### Publish Immediately (Skip Draft)

When running the bot, enter:
```
Publish status: publish  # Instead of 'draft'
```

## 📅 Automation Ideas

### Daily Tech News (Windows Task Scheduler)

Create a batch file `daily_tech_news.bat`:
```batch
@echo off
cd D:\Chatbots\MCP\Wordpress\Agent
python -c "from news_bot import NewsBot; bot = NewsBot(); bot.run_single_category('technology', 5, 'draft')"
```

Schedule it to run daily at 9 AM.

### Hourly Trending News

```batch
@echo off
cd D:\Chatbots\MCP\Wordpress\Agent
python -c "from news_bot import NewsBot; bot = NewsBot(); bot.run_trending_news(3, 'draft')"
```

## 🚀 Next Steps

1. ✅ Run `test_news_bot.py` to verify setup
2. ✅ Run `news_bot.py` with 2-3 articles as draft
3. ✅ Check your WordPress site for the posts
4. ✅ Review and publish the best ones
5. ✅ Increase volume and automate!

## 📚 Full Documentation

For detailed documentation, see: `README_NEWS_BOT.md`

## 🆘 Need Help?

1. Check `news_bot.log` for error details
2. Run `test_news_bot.py` to verify all APIs
3. Review the README for detailed docs

---

**Happy News Automation! 🤖📰**
