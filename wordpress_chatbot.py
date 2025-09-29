import os
import requests
from dotenv import load_dotenv
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai import Agent, Tool
from dataclasses import dataclass
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List, Dict, Any
import asyncio

load_dotenv()

# WordPress Configuration
WORDPRESS_BASE_URL = os.getenv('WORDPRESS_BASE_URL', 'https://vibebuilder.studio')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')

# Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

@dataclass
class WordPressPost:
    title: str
    content: str
    status: str = 'draft'

class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the post (required)")
    content: str = Field(..., min_length=1, description="Content of the post (required)")
    status: str = Field(default='draft', description="Post status: draft, publish, or private")

    def validate_status(cls, v):
        if v not in ['draft', 'publish', 'private']:
            raise ValueError("Status must be 'draft', 'publish', or 'private'")
        return v

class PostQuery(BaseModel):
    per_page: int = Field(default=10, ge=1, le=100, description="Number of posts to retrieve (1-100)")
    page: int = Field(default=1, ge=1, description="Page number to retrieve")
    search: Optional[str] = Field(default=None, description="Search term to filter posts")

def get_wordpress_headers():
    """Get WordPress API headers with authentication"""
    return {
        'Authorization': f'Bearer {BEARER_TOKEN}',
        'Content-Type': 'application/json'
    }

def validate_post_data(post_data: dict) -> Optional[PostCreate]:
    """Validate post creation data using Pydantic model"""
    try:
        return PostCreate(**post_data)
    except ValidationError as e:
        print(f"Validation error: {e}")
        return None

def validate_query_params(query_data: dict) -> Optional[PostQuery]:
    """Validate post query parameters"""
    try:
        return PostQuery(**query_data)
    except ValidationError as e:
        print(f"Query validation error: {e}")
        return None

@Tool
def get_posts(per_page: int = 10, page: int = 1, search: str = None) -> str:
    """
    Retrieve WordPress posts from the site.
    Parameters:
    - per_page: Number of posts to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - search: Optional search term to filter posts
    """

    # Validate query parameters
    query_data = {"per_page": per_page, "page": page}
    if search:
        query_data["search"] = search

    validated_query = validate_query_params(query_data)
    if not validated_query:
        return "Invalid query parameters. Please provide valid per_page (1-100), page (>=1), and optional search term."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts"
        params = {
            'per_page': validated_query.per_page,
            'page': validated_query.page,
            '_embed': True
        }

        if validated_query.search:
            params['search'] = validated_query.search

        response = requests.get(url, headers=get_wordpress_headers(), params=params)
        response.raise_for_status()

        posts = response.json()

        if not posts:
            search_info = f" matching '{validated_query.search}'" if validated_query.search else ""
            return f"No posts found{search_info} on page {validated_query.page}."

        result = f"Found {len(posts)} posts"
        if validated_query.search:
            result += f" matching '{validated_query.search}'"
        result += f" (page {validated_query.page}):\n\n"

        for i, post in enumerate(posts, 1):
            title = post.get('title', {}).get('rendered', 'Untitled')
            status = post.get('status', 'unknown')
            date = post.get('date', '')[:10]  # Get just the date part
            excerpt = post.get('excerpt', {}).get('rendered', '')

            # Clean excerpt from HTML tags
            if excerpt:
                import re
                excerpt = re.sub(r'<[^>]+>', '', excerpt).strip()
                if len(excerpt) > 100:
                    excerpt = excerpt[:100] + "..."

            result += f"{i}. **{title}**\n"
            result += f"   Status: {status.title()}\n"
            result += f"   Date: {date}\n"
            if excerpt:
                result += f"   Excerpt: {excerpt}\n"
            result += f"   URL: {post.get('link', 'N/A')}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        return f"Error retrieving posts: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@Tool
def create_post(title: str, content: str, status: str = 'draft') -> str:
    """
    Create a new WordPress post.
    Parameters:
    - title: Post title (required)
    - content: Post content (required)
    - status: Post status - 'draft', 'publish', or 'private' (default: 'draft')
    """

    # Validate post data
    post_data = {"title": title, "content": content, "status": status}
    validated_post = validate_post_data(post_data)

    if not validated_post:
        return "Invalid post data. Please provide:\n- title (non-empty string)\n- content (non-empty string)\n- status ('draft', 'publish', or 'private')"

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts"
        data = {
            'title': validated_post.title,
            'content': validated_post.content,
            'status': validated_post.status
        }

        response = requests.post(url, headers=get_wordpress_headers(), json=data)
        response.raise_for_status()

        post_response = response.json()
        post_id = post_response.get('id')
        post_url = post_response.get('link', 'N/A')

        return f"✅ Post created successfully!\n\n" \
               f"**Title:** {validated_post.title}\n" \
               f"**Status:** {validated_post.status.title()}\n" \
               f"**ID:** {post_id}\n" \
               f"**URL:** {post_url}\n\n" \
               f"Content preview: {validated_post.content[:100]}{'...' if len(validated_post.content) > 100 else ''}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to create posts."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error creating post: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error creating post: {str(e)}"

@Tool
def get_site_info() -> str:
    """Get basic information about the WordPress site"""
    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json"
        response = requests.get(url)
        response.raise_for_status()

        site_info = response.json()
        return f"📝 **WordPress Site Information:**\n\n" \
               f"**Site URL:** {WORDPRESS_BASE_URL}\n" \
               f"**Name:** {site_info.get('name', 'Unknown')}\n" \
               f"**Description:** {site_info.get('description', 'No description')}\n" \
               f"**WordPress Version:** {site_info.get('wp_version', 'Unknown')}\n" \
               f"**API Namespace:** {', '.join(site_info.get('namespaces', []))}"

    except Exception as e:
        return f"❌ Error getting site info: {str(e)}"

# Initialize the Pydantic AI Agent
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

if not BEARER_TOKEN:
    raise ValueError("BEARER_TOKEN environment variable is required")

provider = GoogleProvider(api_key=GEMINI_API_KEY)
model = GoogleModel('gemini-2.0-flash', provider=provider)

agent = Agent(
    model=model,
    instrument=True,
    tools=[get_posts, create_post, get_site_info],
    system_prompt="""You are a WordPress content management assistant. You can help users:

1. **View Posts**: Retrieve and display posts from the WordPress site with search functionality
2. **Create Posts**: Help create new blog posts with proper validation
3. **Site Information**: Get basic information about the WordPress site

**Important Guidelines:**
- Always validate user input thoroughly before making API calls
- If a user wants to create a post but doesn't provide all required information (title, content), ask for the missing details
- When creating posts, explain the different status options: 'draft' (default), 'publish', or 'private'
- Be helpful and guide users through the process step by step
- Use emojis and formatting to make responses more engaging
- If there are errors, explain them clearly and suggest solutions

**Available Commands:**
- "show posts" or "get posts" - Retrieve recent posts
- "create post" or "write post" - Create a new blog post
- "search posts [term]" - Search for specific posts
- "site info" - Get WordPress site information

Always be conversational and helpful. If users need clarification, ask follow-up questions to gather all required information."""
)

async def main():
    """Main function to run the WordPress chatbot with continuous input"""
    print("🚀 === WordPress Content Management Chatbot ===")
    print("💬 I can help you manage your WordPress content!")
    print("\n📋 Available commands:")
    print("  • 'show posts' - View recent posts")
    print("  • 'create post' - Create a new blog post")
    print("  • 'search posts [term]' - Search for posts")
    print("  • 'site info' - Get site information")
    print("\n💡 Type 'quit' to exit, 'clear' to clear history")
    print("=" * 60)

    message_history = []

    while True:
        try:
            user_input = input("\n🗣️  You: ").strip()

            if user_input.lower() == 'quit':
                print("\n👋 Thanks for using WordPress Chatbot! Goodbye!")
                break

            if user_input.lower() == 'clear':
                message_history = []
                print("🧹 Conversation history cleared!")
                continue

            if user_input.lower() == 'history':
                print("\n📜 === Conversation History ===")
                if message_history:
                    for i, msg in enumerate(message_history[-10:], 1):  # Show last 10 messages
                        print(f"{i}. {msg}")
                else:
                    print("No conversation history yet.")
                continue

            if not user_input:
                print("💭 Please enter a message or command.")
                continue

            print("🤖 Assistant: ", end="", flush=True)

            # Process the user input with the AI agent
            result = await agent.run(user_input, message_history=message_history)
            print(result.output)

            # Update message history
            message_history.extend(result.new_messages())

            # Keep message history manageable (last 20 messages)
            if len(message_history) > 20:
                message_history = message_history[-20:]

        except KeyboardInterrupt:
            print("\n\n👋 Thanks for using WordPress Chatbot! Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {str(e)}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    asyncio.run(main())