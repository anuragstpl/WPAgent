"""
Demo Script - Shows the News Bot in action with a simple example
Run this to see the bot create 1 technology news post
"""
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from news_bot import NewsBot

print("""
╔══════════════════════════════════════════════════════════╗
║              NEWS BOT - DEMO MODE                        ║
║                                                          ║
║  This demo will fetch 1 technology news article and      ║
║  create it as a DRAFT on your WordPress site            ║
╚══════════════════════════════════════════════════════════╝
""")

input("\nPress Enter to start the demo...")

print("\n🚀 Initializing News Bot...\n")

# Initialize the bot
bot = NewsBot()

print("\n📰 Fetching 1 technology news article...\n")
print("=" * 60)

# Fetch and publish 1 technology article as draft
result = bot.run_single_category(
    category='technology',
    max_articles=1,
    publish_status='draft'
)

print("\n" + "=" * 60)
print("DEMO COMPLETED!")
print("=" * 60)

if result and len(result) > 0:
    post = result[0]
    print(f"""
✅ SUCCESS! News article created:

   Title: {post['title']}
   Status: {post['status'].upper()}
   URL: {post['url']}

📌 Next Steps:
   1. Visit: {post['url']}
   2. Review the article
   3. Click 'Publish' if you're happy with it!

💡 Want more? Run: python news_bot.py
""")
else:
    print("""
❌ No posts were created. Please check:
   1. API keys in .env file
   2. Internet connection
   3. Run: python test_news_bot.py
""")

print("=" * 60)
