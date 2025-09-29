from flask import Flask, render_template, request, jsonify, session
import os
import requests
from dotenv import load_dotenv
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai import Agent, Tool
from pydantic import BaseModel, Field, ValidationError
from typing import Optional
import asyncio
import uuid
import threading
import concurrent.futures
import re

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# WordPress Configuration
WORDPRESS_BASE_URL = os.getenv('WORDPRESS_BASE_URL', 'https://vibebuilder.studio')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')

# Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the post (required)")
    content: str = Field(..., min_length=1, description="Content of the post (required)")
    status: str = Field(default='draft', description="Post status: draft, publish, or private")

class PostQuery(BaseModel):
    per_page: int = Field(default=10, ge=1, le=100, description="Number of posts to retrieve (1-100)")
    page: int = Field(default=1, ge=1, description="Page number to retrieve")
    search: Optional[str] = Field(default=None, description="Search term to filter posts")

def get_wordpress_headers():
    """Get WordPress API headers with authentication"""
    return {
        'Authorization': f'Bearer {BEARER_TOKEN}',
        'Content-Type': 'application/json',
        'User-Agent': 'WordPress-Chatbot/1.0'
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

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).strip()

@Tool
def get_posts(per_page: int = 10, page: int = 1, search: str = None) -> str:
    """
    Retrieve WordPress posts from the site.
    Parameters:
    - per_page: Number of posts to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - search: Optional search term to filter posts
    """
    print(f"DEBUG: get_posts called with per_page={per_page}, page={page}, search={search}")

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
            'page': validated_query.page
        }

        if validated_query.search:
            params['search'] = validated_query.search

        print(f"DEBUG: Making request to {url} with params {params}")

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code != 200:
            print(f"DEBUG: Response text: {response.text[:300]}")

        response.raise_for_status()

        posts = response.json()
        print(f"DEBUG: Retrieved {len(posts)} posts")

        if not posts:
            search_info = f" matching '{validated_query.search}'" if validated_query.search else ""
            return f"No posts found{search_info} on page {validated_query.page}."

        result = f"Found {len(posts)} posts"
        if validated_query.search:
            result += f" matching '{validated_query.search}'"
        result += f" (page {validated_query.page}):\n\n"

        for i, post in enumerate(posts, 1):
            title = post.get('title', {})
            if isinstance(title, dict):
                title = title.get('rendered', 'Untitled')
            else:
                title = str(title) if title else 'Untitled'

            status = post.get('status', 'unknown')
            date = post.get('date', '')[:10] if post.get('date') else 'Unknown date'

            # Get excerpt or content preview
            excerpt = post.get('excerpt', {})
            if isinstance(excerpt, dict):
                excerpt = excerpt.get('rendered', '')
            else:
                excerpt = str(excerpt) if excerpt else ''

            if not excerpt:
                content = post.get('content', {})
                if isinstance(content, dict):
                    excerpt = content.get('rendered', '')[:200] + "..."

            # Clean HTML from excerpt
            excerpt = clean_html(excerpt)
            if len(excerpt) > 150:
                excerpt = excerpt[:150] + "..."

            result += f"{i}. **{title}**\n"
            result += f"   Status: {status.title()}\n"
            result += f"   Date: {date}\n"
            if excerpt:
                result += f"   Preview: {excerpt}\n"
            result += f"   URL: {post.get('link', 'N/A')}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving posts: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def create_post(title: str, content: str, status: str = 'draft') -> str:
    """
    Create a new WordPress post.
    Parameters:
    - title: Post title (required)
    - content: Post content (required)
    - status: Post status - 'draft', 'publish', or 'private' (default: 'draft')
    """
    print(f"DEBUG: create_post called with title='{title}', status='{status}'")

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

        print(f"DEBUG: Making POST request to {url}")

        response = requests.post(url, headers=get_wordpress_headers(), json=data, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code not in [200, 201]:
            print(f"DEBUG: Response text: {response.text[:300]}")

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
        # Try the authenticated endpoint first
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2"
        response = requests.get(url, headers=get_wordpress_headers(), timeout=10)

        if response.status_code == 200:
            site_info = response.json()
            return f"**WordPress Site Information:**\n\n" \
                   f"**Site URL:** {WORDPRESS_BASE_URL}\n" \
                   f"**API Version:** {site_info.get('name', 'WP REST API')}\n" \
                   f"**Description:** {site_info.get('description', 'WordPress REST API')}\n"

        # Fallback to basic endpoint
        url = f"{WORDPRESS_BASE_URL}/wp-json"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            site_info = response.json()
            return f"**WordPress Site Information:**\n\n" \
                   f"**Site URL:** {WORDPRESS_BASE_URL}\n" \
                   f"**Name:** {site_info.get('name', 'Unknown')}\n" \
                   f"**Description:** {site_info.get('description', 'No description')}\n" \
                   f"**WordPress Version:** {site_info.get('wp_version', 'Unknown')}\n"

        return f"**WordPress Site:** {WORDPRESS_BASE_URL}\n**Status:** API accessible but limited info available"

    except Exception as e:
        return f"❌ Error getting site info: {str(e)}"

# Validate environment variables
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

if not BEARER_TOKEN:
    raise ValueError("BEARER_TOKEN environment variable is required")

# Initialize the Pydantic AI Agent
provider = GoogleProvider(api_key=GEMINI_API_KEY)
model = GoogleModel('gemini-2.5-flash-lite', provider=provider)

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
- If a user wants to create a post but doesn't provide all required information (title, content), ask for the missing details step by step
- When creating posts, explain the different status options: 'draft' (default), 'publish', or 'private'
- Be helpful and guide users through the process step by step
- Use clear formatting to make responses easy to read
- If there are errors, explain them clearly and suggest solutions
- Always ask for confirmation before publishing posts

**Available Commands:**
- "show posts" or "get posts" - Retrieve recent posts
- "create post" or "write post" - Create a new blog post
- "search posts [term]" - Search for specific posts
- "site info" - Get WordPress site information

Always be conversational and helpful. If users need clarification, ask follow-up questions to gather all required information before proceeding."""
)

# Store conversations in memory (in production, use a database)
conversations = {}

# Function to run async agent in thread
def run_agent_in_thread(message, message_history):
    """Run the agent in a separate thread with its own event loop"""
    def _run_agent():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(agent.run(message, message_history=message_history))
        finally:
            loop.close()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(_run_agent)
        return future.result(timeout=60)  # 60 second timeout

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        # Get or create session ID
        session_id = session.get('chat_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['chat_id'] = session_id

        # Get conversation history
        if session_id not in conversations:
            conversations[session_id] = []

        message_history = conversations[session_id]

        # Process message with AI agent in separate thread
        try:
            result = run_agent_in_thread(message, message_history)
        except concurrent.futures.TimeoutError:
            return jsonify({'error': 'Request timeout. Please try again.'}), 500
        except Exception as e:
            print(f"Error running agent: {str(e)}")
            return jsonify({'error': f'Processing error: {str(e)}'}), 500

        # Update conversation history
        message_history.extend(result.new_messages())

        # Keep conversation history manageable
        if len(message_history) > 20:
            message_history = message_history[-20:]

        conversations[session_id] = message_history

        return jsonify({
            'response': result.output,
            'session_id': session_id
        })

    except Exception as e:
        print(f"Chat route error: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_chat():
    session_id = session.get('chat_id')
    if session_id and session_id in conversations:
        conversations[session_id] = []
    return jsonify({'message': 'Chat history cleared'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)