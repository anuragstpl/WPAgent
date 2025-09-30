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
import re

load_dotenv()

# WordPress Configuration
WORDPRESS_BASE_URL = os.getenv('WORDPRESS_BASE_URL', 'https://vibebuilder.studio')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Pydantic Models for Input Validation
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
    status: Optional[str] = Field(default=None, description="Post status filter")
    author: Optional[int] = Field(default=None, description="Author ID filter")

class PageCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the page (required)")
    content: str = Field(..., min_length=1, description="Content of the page (required)")
    status: str = Field(default='draft', description="Page status: draft, publish, or private")
    parent: int = Field(default=0, ge=0, description="Parent page ID (0 for top-level)")

class MediaUpload(BaseModel):
    filename: str = Field(..., min_length=1, description="Name of the file to upload")
    title: Optional[str] = Field(default=None, description="Custom title for media")
    alt_text: Optional[str] = Field(default=None, description="Alt text for images")

class MenuItemCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Menu item title (required)")
    url: str = Field(..., min_length=1, description="Menu item URL (required)")
    menu_order: int = Field(default=0, ge=0, description="Menu order position")
    parent: int = Field(default=0, ge=0, description="Parent menu item ID")

class BlockCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Block title (required)")
    content: str = Field(..., min_length=1, description="Block content (required)")
    status: str = Field(default='publish', description="Block status: draft or publish")

def get_wordpress_headers():
    """Get WordPress API headers with authentication"""
    return {
        'Authorization': f'Bearer {BEARER_TOKEN}',
        'Content-Type': 'application/json',
        'User-Agent': 'WordPress-ChatBot/1.0'
    }

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).strip()

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

def validate_page_data(page_data: dict) -> Optional[PageCreate]:
    """Validate page creation data using Pydantic model"""
    try:
        return PageCreate(**page_data)
    except ValidationError as e:
        print(f"Validation error: {e}")
        return None

def validate_menu_item_data(menu_data: dict) -> Optional[MenuItemCreate]:
    """Validate menu item creation data using Pydantic model"""
    try:
        return MenuItemCreate(**menu_data)
    except ValidationError as e:
        print(f"Validation error: {e}")
        return None

def validate_block_data(block_data: dict) -> Optional[BlockCreate]:
    """Validate block creation data using Pydantic model"""
    try:
        return BlockCreate(**block_data)
    except ValidationError as e:
        print(f"Validation error: {e}")
        return None

# POSTS API TOOLS
@Tool
def get_posts(per_page: int = 10, page: int = 1, search: str = None, status: str = None, author: int = None) -> str:
    """
    Retrieve WordPress posts with filtering options.
    Parameters:
    - per_page: Number of posts to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - search: Optional search term to filter posts
    - status: Post status filter (publish, draft, private)
    - author: Author ID filter
    """
    query_data = {"per_page": per_page, "page": page}
    if search:
        query_data["search"] = search
    if status:
        query_data["status"] = status
    if author:
        query_data["author"] = author

    validated_query = validate_query_params(query_data)
    if not validated_query:
        return "Invalid query parameters. Please provide valid per_page (1-100), page (>=1), and optional filters."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts"
        params = {
            'per_page': validated_query.per_page,
            'page': validated_query.page
        }

        if validated_query.search:
            params['search'] = validated_query.search
        if validated_query.status:
            params['status'] = validated_query.status
        if validated_query.author:
            params['author'] = validated_query.author

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        response.raise_for_status()

        posts = response.json()
        if not posts:
            return "No posts found matching your criteria."

        result = f"Found {len(posts)} posts:\n\n"
        for i, post in enumerate(posts, 1):
            title = post.get('title', {}).get('rendered', 'Untitled')
            status = post.get('status', 'unknown')
            date = post.get('date', '')[:10]
            excerpt = post.get('excerpt', {}).get('rendered', '')

            if not excerpt:
                content = post.get('content', {}).get('rendered', '')
                excerpt = content[:200] + "..." if len(content) > 200 else content

            excerpt = clean_html(excerpt)[:150] + "..." if len(clean_html(excerpt)) > 150 else clean_html(excerpt)

            result += f"{i}. **{title}**\n"
            result += f"   Status: {status.title()}\n"
            result += f"   Date: {date}\n"
            if excerpt:
                result += f"   Preview: {excerpt}\n"
            result += f"   URL: {post.get('link', 'N/A')}\n\n"

        return result

    except Exception as e:
        return f"Error retrieving posts: {str(e)}"

@Tool
def create_post(title: str, content: str, status: str = 'draft') -> str:
    """
    Create a new WordPress post with validation.
    Parameters:
    - title: Post title (required)
    - content: Post content (required)
    - status: Post status - 'draft', 'publish', or 'private' (default: 'draft')
    """
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

        response = requests.post(url, headers=get_wordpress_headers(), json=data, timeout=15)
        response.raise_for_status()

        post_response = response.json()
        post_id = post_response.get('id')
        post_url = post_response.get('link', 'N/A')

        return f"Post created successfully!\n\n" \
               f"**Title:** {validated_post.title}\n" \
               f"**Status:** {validated_post.status.title()}\n" \
               f"**ID:** {post_id}\n" \
               f"**URL:** {post_url}"

    except Exception as e:
        return f"Error creating post: {str(e)}"

@Tool
def update_post(post_id: int, title: str = None, content: str = None, status: str = None) -> str:
    """
    Update an existing WordPress post.
    Parameters:
    - post_id: ID of the post to update (required)
    - title: New title (optional)
    - content: New content (optional)
    - status: New status (optional)
    """
    if not post_id or post_id <= 0:
        return "Invalid post ID. Please provide a valid post ID."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts/{post_id}"
        data = {}

        if title:
            data['title'] = title
        if content:
            data['content'] = content
        if status:
            if status not in ['draft', 'publish', 'private']:
                return "Invalid status. Must be 'draft', 'publish', or 'private'."
            data['status'] = status

        if not data:
            return "No updates provided. Please specify title, content, or status to update."

        response = requests.post(url, headers=get_wordpress_headers(), json=data, timeout=15)
        response.raise_for_status()

        return f"Post {post_id} updated successfully!"

    except Exception as e:
        return f"Error updating post: {str(e)}"

@Tool
def delete_post(post_id: int, force: bool = False) -> str:
    """
    Delete a WordPress post.
    Parameters:
    - post_id: ID of the post to delete (required)
    - force: Whether to permanently delete (true) or move to trash (false)
    """
    if not post_id or post_id <= 0:
        return "Invalid post ID. Please provide a valid post ID."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts/{post_id}"
        params = {'force': force}

        response = requests.delete(url, headers=get_wordpress_headers(), params=params, timeout=15)
        response.raise_for_status()

        action = "permanently deleted" if force else "moved to trash"
        return f"Post {post_id} {action} successfully!"

    except Exception as e:
        return f"Error deleting post: {str(e)}"

# PAGES API TOOLS
@Tool
def get_pages(per_page: int = 10, page: int = 1, search: str = None, status: str = None, parent: int = None) -> str:
    """
    Retrieve WordPress pages with filtering options.
    Parameters:
    - per_page: Number of pages to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - search: Optional search term to filter pages
    - status: Page status filter (publish, draft, private)
    - parent: Parent page ID filter
    """
    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/pages"
        params = {'per_page': per_page, 'page': page}

        if search:
            params['search'] = search
        if status:
            params['status'] = status
        if parent is not None:
            params['parent'] = parent

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        response.raise_for_status()

        pages = response.json()
        if not pages:
            return "No pages found matching your criteria."

        result = f"Found {len(pages)} pages:\n\n"
        for i, page in enumerate(pages, 1):
            title = page.get('title', {}).get('rendered', 'Untitled')
            status = page.get('status', 'unknown')
            date = page.get('date', '')[:10]
            parent_id = page.get('parent', 0)

            result += f"{i}. **{title}**\n"
            result += f"   Status: {status.title()}\n"
            result += f"   Date: {date}\n"
            result += f"   Type: {'Child Page' if parent_id else 'Top Level Page'}\n"
            result += f"   URL: {page.get('link', 'N/A')}\n\n"

        return result

    except Exception as e:
        return f"Error retrieving pages: {str(e)}"

@Tool
def create_page(title: str, content: str, status: str = 'draft', parent: int = 0) -> str:
    """
    Create a new WordPress page.
    Parameters:
    - title: Page title (required)
    - content: Page content (required)
    - status: Page status - 'draft', 'publish', or 'private' (default: 'draft')
    - parent: Parent page ID (0 for top-level page)
    """
    page_data = {"title": title, "content": content, "status": status, "parent": parent}
    validated_page = validate_page_data(page_data)

    if not validated_page:
        return "Invalid page data. Please provide valid title, content, status, and parent ID."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/pages"
        data = {
            'title': validated_page.title,
            'content': validated_page.content,
            'status': validated_page.status,
            'parent': validated_page.parent
        }

        response = requests.post(url, headers=get_wordpress_headers(), json=data, timeout=15)
        response.raise_for_status()

        page_response = response.json()
        page_id = page_response.get('id')
        page_url = page_response.get('link', 'N/A')

        return f"Page created successfully!\n\n" \
               f"**Title:** {validated_page.title}\n" \
               f"**Status:** {validated_page.status.title()}\n" \
               f"**Type:** {'Child Page' if validated_page.parent else 'Top Level Page'}\n" \
               f"**ID:** {page_id}\n" \
               f"**URL:** {page_url}"

    except Exception as e:
        return f"Error creating page: {str(e)}"

# MEDIA API TOOLS
@Tool
def get_media(per_page: int = 10, page: int = 1, media_type: str = None, search: str = None) -> str:
    """
    Retrieve WordPress media files.
    Parameters:
    - per_page: Number of media items to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - media_type: Media type filter (image, video, audio, application)
    - search: Search term for media titles
    """
    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/media"
        params = {'per_page': per_page, 'page': page}

        if media_type:
            params['media_type'] = media_type
        if search:
            params['search'] = search

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        response.raise_for_status()

        media_items = response.json()
        if not media_items:
            return "No media files found matching your criteria."

        result = f"Found {len(media_items)} media files:\n\n"
        for i, item in enumerate(media_items, 1):
            title = item.get('title', {}).get('rendered', 'Untitled')
            media_type = item.get('media_type', 'unknown')
            mime_type = item.get('mime_type', 'unknown')
            date = item.get('date', '')[:10]

            file_size = ""
            if item.get('media_details') and item['media_details'].get('filesize'):
                size_kb = item['media_details']['filesize'] / 1024
                file_size = f" ({size_kb:.1f} KB)"

            result += f"{i}. **{title}**\n"
            result += f"   Type: {media_type.title()}{file_size}\n"
            result += f"   Format: {mime_type}\n"
            result += f"   Date: {date}\n"
            result += f"   URL: {item.get('source_url', 'N/A')}\n\n"

        return result

    except Exception as e:
        return f"Error retrieving media: {str(e)}"

# MENU ITEMS API TOOLS
@Tool
def get_menu_items(per_page: int = 50, page: int = 1, menu_order: str = 'asc') -> str:
    """
    Retrieve WordPress menu items.
    Parameters:
    - per_page: Number of menu items to retrieve (1-100, default: 50)
    - page: Page number to retrieve (default: 1)
    - menu_order: Sort order ('asc' or 'desc')
    """
    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/menu-items"
        params = {
            'per_page': per_page,
            'page': page,
            'orderby': 'menu_order',
            'order': menu_order
        }

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        response.raise_for_status()

        menu_items = response.json()
        if not menu_items:
            return "No menu items found."

        result = f"Found {len(menu_items)} menu items:\n\n"
        for i, item in enumerate(menu_items, 1):
            title = item.get('title', {}).get('rendered', 'Untitled')
            url = item.get('url', 'No URL')
            menu_order = item.get('menu_order', 0)
            parent = item.get('parent', 0)

            result += f"{i}. **{title}**\n"
            result += f"   URL: {url}\n"
            result += f"   Order: {menu_order}\n"
            result += f"   Type: {'Child Item' if parent else 'Top Level Item'}\n\n"

        return result

    except Exception as e:
        return f"Error retrieving menu items: {str(e)}"

@Tool
def create_menu_item(title: str, url: str, menu_order: int = 0, parent: int = 0) -> str:
    """
    Create a new WordPress menu item.
    Parameters:
    - title: Menu item title (required)
    - url: Menu item URL (required)
    - menu_order: Menu order position (default: 0)
    - parent: Parent menu item ID (default: 0)
    """
    menu_data = {"title": title, "url": url, "menu_order": menu_order, "parent": parent}
    validated_menu = validate_menu_item_data(menu_data)

    if not validated_menu:
        return "Invalid menu item data. Please provide valid title, URL, menu_order, and parent ID."

    try:
        api_url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/menu-items"
        data = {
            'title': validated_menu.title,
            'url': validated_menu.url,
            'menu_order': validated_menu.menu_order,
            'parent': validated_menu.parent
        }

        response = requests.post(api_url, headers=get_wordpress_headers(), json=data, timeout=15)
        response.raise_for_status()

        menu_response = response.json()
        menu_id = menu_response.get('id')

        return f"Menu item created successfully!\n\n" \
               f"**Title:** {validated_menu.title}\n" \
               f"**URL:** {validated_menu.url}\n" \
               f"**Order:** {validated_menu.menu_order}\n" \
               f"**Type:** {'Child Item' if validated_menu.parent else 'Top Level Item'}\n" \
               f"**ID:** {menu_id}"

    except Exception as e:
        return f"Error creating menu item: {str(e)}"

# BLOCKS API TOOLS
@Tool
def get_blocks(per_page: int = 10, page: int = 1, search: str = None, status: str = None) -> str:
    """
    Retrieve WordPress blocks.
    Parameters:
    - per_page: Number of blocks to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - search: Search term for block titles
    - status: Block status filter (publish, draft)
    """
    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/blocks"
        params = {'per_page': per_page, 'page': page}

        if search:
            params['search'] = search
        if status:
            params['status'] = status

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        response.raise_for_status()

        blocks = response.json()
        if not blocks:
            return "No blocks found matching your criteria."

        result = f"Found {len(blocks)} blocks:\n\n"
        for i, block in enumerate(blocks, 1):
            title = block.get('title', {}).get('rendered', 'Untitled')
            status = block.get('status', 'unknown')
            date = block.get('date', '')[:10]
            content = block.get('content', {}).get('rendered', '')
            preview = clean_html(content)[:100] + "..." if len(clean_html(content)) > 100 else clean_html(content)

            result += f"{i}. **{title}**\n"
            result += f"   Status: {status.title()}\n"
            result += f"   Date: {date}\n"
            if preview:
                result += f"   Preview: {preview}\n"
            result += "\n"

        return result

    except Exception as e:
        return f"Error retrieving blocks: {str(e)}"

@Tool
def create_block(title: str, content: str, status: str = 'publish') -> str:
    """
    Create a new WordPress block.
    Parameters:
    - title: Block title (required)
    - content: Block content/code (required)
    - status: Block status - 'draft' or 'publish' (default: 'publish')
    """
    block_data = {"title": title, "content": content, "status": status}
    validated_block = validate_block_data(block_data)

    if not validated_block:
        return "Invalid block data. Please provide valid title, content, and status."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/blocks"
        data = {
            'title': validated_block.title,
            'content': validated_block.content,
            'status': validated_block.status
        }

        response = requests.post(url, headers=get_wordpress_headers(), json=data, timeout=15)
        response.raise_for_status()

        block_response = response.json()
        block_id = block_response.get('id')

        return f"Block created successfully!\n\n" \
               f"**Title:** {validated_block.title}\n" \
               f"**Status:** {validated_block.status.title()}\n" \
               f"**ID:** {block_id}\n" \
               f"**Content Preview:** {validated_block.content[:100]}..."

    except Exception as e:
        return f"Error creating block: {str(e)}"

# SITE INFO TOOL
@Tool
def get_site_info() -> str:
    """Get basic information about the WordPress site"""
    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        site_info = response.json()
        return f"**WordPress Site Information:**\n\n" \
               f"**Site URL:** {WORDPRESS_BASE_URL}\n" \
               f"**Name:** {site_info.get('name', 'Unknown')}\n" \
               f"**Description:** {site_info.get('description', 'No description')}\n" \
               f"**WordPress Version:** {site_info.get('wp_version', 'Unknown')}\n" \
               f"**API Namespaces:** {', '.join(site_info.get('namespaces', []))}"

    except Exception as e:
        return f"Error getting site info: {str(e)}"

# Validate environment variables
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

if not BEARER_TOKEN:
    raise ValueError("BEARER_TOKEN environment variable is required")

# Initialize the Pydantic AI Agent
provider = GoogleProvider(api_key=GEMINI_API_KEY)
model = GoogleModel('gemini-2.0-flash', provider=provider)

# All available tools
all_tools = [
    # Posts
    get_posts, create_post, update_post, delete_post,
    # Pages
    get_pages, create_page,
    # Media
    get_media,
    # Menu Items
    get_menu_items, create_menu_item,
    # Blocks
    get_blocks, create_block,
    # Site Info
    get_site_info
]

agent = Agent(
    model=model,
    instrument=True,
    tools=all_tools,
    system_prompt="""You are a comprehensive WordPress content management assistant with full access to WordPress REST API. You can help users with:

**POSTS MANAGEMENT:**
- View posts with filtering (status, author, search)
- Create new blog posts with validation
- Update existing posts (title, content, status)
- Delete posts (trash or permanent)

**PAGES MANAGEMENT:**
- View pages with filtering options
- Create new pages with parent/child relationships
- Manage page hierarchy

**MEDIA MANAGEMENT:**
- Browse media library with filters
- View media details and metadata
- Filter by media type (image, video, audio, etc.)

**MENU MANAGEMENT:**
- View menu items and structure
- Create new menu items with ordering
- Manage menu hierarchy

**BLOCKS MANAGEMENT:**
- Browse reusable blocks
- Create new blocks for content reuse
- Manage block library

**SITE INFORMATION:**
- Get WordPress site details and API info

**IMPORTANT GUIDELINES:**
- Always validate user input before making API calls
- For multi-step operations (like creating content), gather all required information step by step
- Ask for confirmation before destructive operations (delete, publish)
- Provide clear, helpful error messages
- Use formatting to make responses readable
- When users ask for help, explain available commands and options
- Maintain conversation context to provide personalized assistance

**INPUT VALIDATION:**
- All operations include proper validation using Pydantic models
- Invalid inputs will be rejected with clear error messages
- Required fields must be provided before proceeding

**AVAILABLE COMMANDS:**
Use natural language - I understand requests like:
- "Show me all posts" / "List recent posts"
- "Create a new post about AI" / "Write a blog post"
- "Show pages" / "List all pages"
- "Create a page called About Us"
- "Show media files" / "List images"
- "Show menu items" / "List navigation"
- "Create menu item" / "Add to menu"
- "Show blocks" / "List reusable blocks"
- "Create a block" / "Make reusable content"
- "Site information" / "WordPress details"
- "Update post 123" / "Delete post 456"

Always be helpful, clear, and ensure users understand each step of complex operations."""
)

async def main():
    """Main function to run the comprehensive WordPress chatbot"""
    print("=== Comprehensive WordPress Content Management Assistant ===")
    print("Full WordPress REST API integration with proper validation!")
    print("\nAvailable features:")
    print("  Posts: Create, read, update, delete with filtering")
    print("  Pages: Manage pages and hierarchy")
    print("  Media: Browse and manage media library")
    print("  Menu: Create and manage navigation menus")
    print("  Blocks: Create and manage reusable blocks")
    print("  Site: Get WordPress site information")
    print("\nType 'quit' to exit, 'clear' to clear history")
    print("=" * 70)

    message_history = []

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() == 'quit':
                print("\nThank you for using WordPress Assistant! Goodbye!")
                break

            if user_input.lower() == 'clear':
                message_history = []
                print("Conversation history cleared!")
                continue

            if user_input.lower() == 'help':
                print("""
WordPress Assistant Help:

**POSTS:**
- "show posts" - View all posts
- "create post" - Create new blog post
- "search posts [term]" - Search posts
- "update post [id]" - Update existing post
- "delete post [id]" - Delete post

**PAGES:**
- "show pages" - View all pages
- "create page" - Create new page
- "search pages [term]" - Search pages

**MEDIA:**
- "show media" - View media library
- "show images" - Filter by images only

**MENUS:**
- "show menu items" - View navigation items
- "create menu item" - Add new menu item

**BLOCKS:**
- "show blocks" - View reusable blocks
- "create block" - Create reusable content

**GENERAL:**
- "site info" - WordPress site details
- "help" - Show this help message
""")
                continue

            if not user_input:
                print("Please enter a message or command.")
                continue

            print("Assistant: ", end="", flush=True)

            # Process the user input with the AI agent
            result = await agent.run(user_input, message_history=message_history)
            print(result.output)

            # Update message history
            message_history.extend(result.new_messages())

            # Keep message history manageable (last 30 messages for better context)
            if len(message_history) > 30:
                message_history = message_history[-30:]

        except KeyboardInterrupt:
            print("\n\nThank you for using WordPress Assistant! Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    asyncio.run(main())