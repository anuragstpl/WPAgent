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

class PageCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the page (required)")
    content: str = Field(..., min_length=1, description="Content of the page (required)")
    status: str = Field(default='draft', description="Page status: draft, publish, or private")

class PageQuery(BaseModel):
    per_page: int = Field(default=10, ge=1, le=100, description="Number of pages to retrieve (1-100)")
    page: int = Field(default=1, ge=1, description="Page number to retrieve")
    search: Optional[str] = Field(default=None, description="Search term to filter pages")

class MediaQuery(BaseModel):
    per_page: int = Field(default=10, ge=1, le=100, description="Number of media items to retrieve (1-100)")
    page: int = Field(default=1, ge=1, description="Page number to retrieve")
    media_type: Optional[str] = Field(default=None, description="Media type filter: image, video, audio, application")

class MenuItemQuery(BaseModel):
    per_page: int = Field(default=10, ge=1, le=100, description="Number of menu items to retrieve (1-100)")
    page: int = Field(default=1, ge=1, description="Page number to retrieve")
    menus: Optional[str] = Field(default=None, description="Menu ID or slug to filter by")

class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, description="Username for the new user (required)")
    email: str = Field(..., description="Email address for the new user (required)")
    password: str = Field(..., min_length=6, description="Password for the new user (required, min 6 chars)")
    name: Optional[str] = Field(default=None, description="Display name for the user")
    roles: Optional[list] = Field(default=["subscriber"], description="User roles")

class UserQuery(BaseModel):
    per_page: int = Field(default=10, ge=1, le=100, description="Number of users to retrieve (1-100)")
    page: int = Field(default=1, ge=1, description="Page number to retrieve")
    search: Optional[str] = Field(default=None, description="Search term to filter users")
    role: Optional[str] = Field(default=None, description="Filter by user role")

class CommentCreate(BaseModel):
    post: int = Field(..., description="Post ID to comment on (required)")
    content: str = Field(..., min_length=1, description="Comment content (required)")
    author_name: Optional[str] = Field(default=None, description="Comment author name")
    author_email: Optional[str] = Field(default=None, description="Comment author email")
    status: str = Field(default='hold', description="Comment status: approve, hold, spam, trash")

class CommentQuery(BaseModel):
    per_page: int = Field(default=10, ge=1, le=100, description="Number of comments to retrieve (1-100)")
    page: int = Field(default=1, ge=1, description="Page number to retrieve")
    search: Optional[str] = Field(default=None, description="Search term to filter comments")
    post: Optional[int] = Field(default=None, description="Filter by post ID")
    status: Optional[str] = Field(default=None, description="Filter by comment status")

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Category name (required)")
    description: Optional[str] = Field(default="", description="Category description")
    slug: Optional[str] = Field(default=None, description="Category slug")
    parent: Optional[int] = Field(default=0, description="Parent category ID")

class CategoryQuery(BaseModel):
    per_page: int = Field(default=10, ge=1, le=100, description="Number of categories to retrieve (1-100)")
    page: int = Field(default=1, ge=1, description="Page number to retrieve")
    search: Optional[str] = Field(default=None, description="Search term to filter categories")
    parent: Optional[int] = Field(default=None, description="Filter by parent category ID")

class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Tag name (required)")
    description: Optional[str] = Field(default="", description="Tag description")
    slug: Optional[str] = Field(default=None, description="Tag slug")

class TagQuery(BaseModel):
    per_page: int = Field(default=10, ge=1, le=100, description="Number of tags to retrieve (1-100)")
    page: int = Field(default=1, ge=1, description="Page number to retrieve")
    search: Optional[str] = Field(default=None, description="Search term to filter tags")

class PostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, description="Updated title")
    content: Optional[str] = Field(default=None, description="Updated content")
    status: Optional[str] = Field(default=None, description="Updated status: draft, publish, private")
    excerpt: Optional[str] = Field(default=None, description="Updated excerpt")
    categories: Optional[list] = Field(default=None, description="Category IDs")
    tags: Optional[list] = Field(default=None, description="Tag IDs")

class PageUpdate(BaseModel):
    title: Optional[str] = Field(default=None, description="Updated title")
    content: Optional[str] = Field(default=None, description="Updated content")
    status: Optional[str] = Field(default=None, description="Updated status: draft, publish, private")
    parent: Optional[int] = Field(default=None, description="Parent page ID")

class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Updated display name")
    email: Optional[str] = Field(default=None, description="Updated email address")
    roles: Optional[list] = Field(default=None, description="Updated user roles")
    password: Optional[str] = Field(default=None, min_length=6, description="New password (min 6 chars)")

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Updated category name")
    description: Optional[str] = Field(default=None, description="Updated description")
    parent: Optional[int] = Field(default=None, description="Updated parent category ID")

class TagUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Updated tag name")
    description: Optional[str] = Field(default=None, description="Updated description")

class CommentUpdate(BaseModel):
    content: Optional[str] = Field(default=None, description="Updated comment content")
    status: Optional[str] = Field(default=None, description="Updated status: approve, hold, spam, trash")
    author_name: Optional[str] = Field(default=None, description="Updated author name")
    author_email: Optional[str] = Field(default=None, description="Updated author email")

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

def validate_page_data(page_data: dict) -> Optional[PageCreate]:
    """Validate page creation data using Pydantic model"""
    try:
        return PageCreate(**page_data)
    except ValidationError as e:
        print(f"Page validation error: {e}")
        return None

def validate_page_query_params(query_data: dict) -> Optional[PageQuery]:
    """Validate page query parameters"""
    try:
        return PageQuery(**query_data)
    except ValidationError as e:
        print(f"Page query validation error: {e}")
        return None

def validate_media_query_params(query_data: dict) -> Optional[MediaQuery]:
    """Validate media query parameters"""
    try:
        return MediaQuery(**query_data)
    except ValidationError as e:
        print(f"Media query validation error: {e}")
        return None

def validate_menu_query_params(query_data: dict) -> Optional[MenuItemQuery]:
    """Validate menu item query parameters"""
    try:
        return MenuItemQuery(**query_data)
    except ValidationError as e:
        print(f"Menu query validation error: {e}")
        return None

def validate_user_data(user_data: dict) -> Optional[UserCreate]:
    """Validate user creation data using Pydantic model"""
    try:
        return UserCreate(**user_data)
    except ValidationError as e:
        print(f"User validation error: {e}")
        return None

def validate_user_query_params(query_data: dict) -> Optional[UserQuery]:
    """Validate user query parameters"""
    try:
        return UserQuery(**query_data)
    except ValidationError as e:
        print(f"User query validation error: {e}")
        return None

def validate_comment_data(comment_data: dict) -> Optional[CommentCreate]:
    """Validate comment creation data using Pydantic model"""
    try:
        return CommentCreate(**comment_data)
    except ValidationError as e:
        print(f"Comment validation error: {e}")
        return None

def validate_comment_query_params(query_data: dict) -> Optional[CommentQuery]:
    """Validate comment query parameters"""
    try:
        return CommentQuery(**query_data)
    except ValidationError as e:
        print(f"Comment query validation error: {e}")
        return None

def validate_category_data(category_data: dict) -> Optional[CategoryCreate]:
    """Validate category creation data using Pydantic model"""
    try:
        return CategoryCreate(**category_data)
    except ValidationError as e:
        print(f"Category validation error: {e}")
        return None

def validate_category_query_params(query_data: dict) -> Optional[CategoryQuery]:
    """Validate category query parameters"""
    try:
        return CategoryQuery(**query_data)
    except ValidationError as e:
        print(f"Category query validation error: {e}")
        return None

def validate_tag_data(tag_data: dict) -> Optional[TagCreate]:
    """Validate tag creation data using Pydantic model"""
    try:
        return TagCreate(**tag_data)
    except ValidationError as e:
        print(f"Tag validation error: {e}")
        return None

def validate_tag_query_params(query_data: dict) -> Optional[TagQuery]:
    """Validate tag query parameters"""
    try:
        return TagQuery(**query_data)
    except ValidationError as e:
        print(f"Tag query validation error: {e}")
        return None

def validate_post_update_data(update_data: dict) -> Optional[PostUpdate]:
    """Validate post update data"""
    try:
        return PostUpdate(**update_data)
    except ValidationError as e:
        print(f"Post update validation error: {e}")
        return None

def validate_page_update_data(update_data: dict) -> Optional[PageUpdate]:
    """Validate page update data"""
    try:
        return PageUpdate(**update_data)
    except ValidationError as e:
        print(f"Page update validation error: {e}")
        return None

def validate_user_update_data(update_data: dict) -> Optional[UserUpdate]:
    """Validate user update data"""
    try:
        return UserUpdate(**update_data)
    except ValidationError as e:
        print(f"User update validation error: {e}")
        return None

def validate_category_update_data(update_data: dict) -> Optional[CategoryUpdate]:
    """Validate category update data"""
    try:
        return CategoryUpdate(**update_data)
    except ValidationError as e:
        print(f"Category update validation error: {e}")
        return None

def validate_tag_update_data(update_data: dict) -> Optional[TagUpdate]:
    """Validate tag update data"""
    try:
        return TagUpdate(**update_data)
    except ValidationError as e:
        print(f"Tag update validation error: {e}")
        return None

def validate_comment_update_data(update_data: dict) -> Optional[CommentUpdate]:
    """Validate comment update data"""
    try:
        return CommentUpdate(**update_data)
    except ValidationError as e:
        print(f"Comment update validation error: {e}")
        return None

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return ""
    import re
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
        result += f" (page {validated_query.page}):\\n\\n"

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

            result += f"{i}. **{title}**\\n"
            result += f"   Status: {status.title()}\\n"
            result += f"   Date: {date}\\n"
            if excerpt:
                result += f"   Preview: {excerpt}\\n"
            result += f"   URL: {post.get('link', 'N/A')}\\n\\n"

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
def get_pages(per_page: int = 10, page: int = 1, search: str = None) -> str:
    """
    Retrieve WordPress pages from the site.
    Parameters:
    - per_page: Number of pages to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - search: Optional search term to filter pages
    """
    print(f"DEBUG: get_pages called with per_page={per_page}, page={page}, search={search}")

    # Validate query parameters
    query_data = {"per_page": per_page, "page": page}
    if search:
        query_data["search"] = search

    validated_query = validate_page_query_params(query_data)
    if not validated_query:
        return "Invalid query parameters. Please provide valid per_page (1-100), page (>=1), and optional search term."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/pages"
        params = {
            'per_page': validated_query.per_page,
            'page': validated_query.page
        }

        if validated_query.search:
            params['search'] = validated_query.search

        print(f"DEBUG: Making request to {url} with params {params}")

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()

        pages = response.json()
        print(f"DEBUG: Retrieved {len(pages)} pages")

        if not pages:
            search_info = f" matching '{validated_query.search}'" if validated_query.search else ""
            return f"No pages found{search_info} on page {validated_query.page}."

        result = f"Found {len(pages)} pages"
        if validated_query.search:
            result += f" matching '{validated_query.search}'"
        result += f" (page {validated_query.page}):\n\n"

        for i, page_item in enumerate(pages, 1):
            title = page_item.get('title', {})
            if isinstance(title, dict):
                title = title.get('rendered', 'Untitled')
            else:
                title = str(title) if title else 'Untitled'

            status = page_item.get('status', 'unknown')
            date = page_item.get('date', '')[:10] if page_item.get('date') else 'Unknown date'

            # Get excerpt or content preview
            excerpt = page_item.get('excerpt', {})
            if isinstance(excerpt, dict):
                excerpt = excerpt.get('rendered', '')
            else:
                excerpt = str(excerpt) if excerpt else ''

            if not excerpt:
                content = page_item.get('content', {})
                if isinstance(content, dict):
                    excerpt = content.get('rendered', '')[:200] + "..."

            # Clean HTML from excerpt
            excerpt = clean_html(excerpt)
            if len(excerpt) > 150:
                excerpt = excerpt[:150] + "..."

            result += f"{i}. **{title}\n"
            result += f"   Status: {status.title()}\n"
            result += f"   Date: {date}\n"
            if excerpt:
                result += f"   Preview: {excerpt}\n"
            result += f"   URL: {page_item.get('link', 'N/A')}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving pages: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def create_page(title: str, content: str, status: str = 'draft') -> str:
    """
    Create a new WordPress page.
    Parameters:
    - title: Page title (required)
    - content: Page content (required)
    - status: Page status - 'draft', 'publish', or 'private' (default: 'draft')
    """
    print(f"DEBUG: create_page called with title='{title}', status='{status}'")

    # Validate page data
    page_data = {"title": title, "content": content, "status": status}
    validated_page = validate_page_data(page_data)

    if not validated_page:
        return "Invalid page data. Please provide:\n- title (non-empty string)\n- content (non-empty string)\n- status ('draft', 'publish', or 'private')"

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/pages"
        data = {
            'title': validated_page.title,
            'content': validated_page.content,
            'status': validated_page.status
        }

        print(f"DEBUG: Making POST request to {url}")

        response = requests.post(url, headers=get_wordpress_headers(), json=data, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code not in [200, 201]:
            print(f"DEBUG: Response text: {response.text[:300]}")

        response.raise_for_status()

        page_response = response.json()
        page_id = page_response.get('id')
        page_url = page_response.get('link', 'N/A')

        return f"✅ Page created successfully!\n\n" \
               f"**Title:** {validated_page.title}\n" \
               f"**Status:** {validated_page.status.title()}\n" \
               f"**ID:** {page_id}\n" \
               f"**URL:** {page_url}\n\n" \
               f"Content preview: {validated_page.content[:100]}{'...' if len(validated_page.content) > 100 else ''}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to create pages."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error creating page: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error creating page: {str(e)}"

@Tool
def get_media(per_page: int = 10, page: int = 1, media_type: str = None) -> str:
    """
    Retrieve WordPress media files from the site.
    Parameters:
    - per_page: Number of media items to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - media_type: Optional media type filter (image, video, audio, application)
    """
    print(f"DEBUG: get_media called with per_page={per_page}, page={page}, media_type={media_type}")

    # Validate query parameters
    query_data = {"per_page": per_page, "page": page}
    if media_type:
        query_data["media_type"] = media_type

    validated_query = validate_media_query_params(query_data)
    if not validated_query:
        return "Invalid query parameters. Please provide valid per_page (1-100), page (>=1), and optional media_type."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/media"
        params = {
            'per_page': validated_query.per_page,
            'page': validated_query.page
        }

        if validated_query.media_type:
            params['media_type'] = validated_query.media_type

        print(f"DEBUG: Making request to {url} with params {params}")

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()

        media_items = response.json()
        print(f"DEBUG: Retrieved {len(media_items)} media items")

        if not media_items:
            media_filter = f" of type '{validated_query.media_type}'" if validated_query.media_type else ""
            return f"No media items found{media_filter} on page {validated_query.page}."

        result = f"Found {len(media_items)} media items"
        if validated_query.media_type:
            result += f" of type '{validated_query.media_type}'"
        result += f" (page {validated_query.page}):\n\n"

        for i, media_item in enumerate(media_items, 1):
            title = media_item.get('title', {})
            if isinstance(title, dict):
                title = title.get('rendered', 'Untitled')
            else:
                title = str(title) if title else 'Untitled'

            media_type = media_item.get('media_type', 'unknown')
            mime_type = media_item.get('mime_type', 'unknown')
            date = media_item.get('date', '')[:10] if media_item.get('date') else 'Unknown date'
            source_url = media_item.get('source_url', 'N/A')

            # Get file size if available
            media_details = media_item.get('media_details', {})
            file_size = media_details.get('filesize', 'Unknown')
            if isinstance(file_size, int):
                file_size = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"

            result += f"{i}. **{title}\n"
            result += f"   Type: {media_type.title()} ({mime_type})\n"
            result += f"   Date: {date}\n"
            result += f"   Size: {file_size}\n"
            result += f"   URL: {source_url}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving media: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def get_menu_items(per_page: int = 10, page: int = 1, menus: str = None) -> str:
    """
    Retrieve WordPress menu items from the site.
    Parameters:
    - per_page: Number of menu items to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - menus: Optional menu ID or slug to filter by
    """
    print(f"DEBUG: get_menu_items called with per_page={per_page}, page={page}, menus={menus}")

    # Validate query parameters
    query_data = {"per_page": per_page, "page": page}
    if menus:
        query_data["menus"] = menus

    validated_query = validate_menu_query_params(query_data)
    if not validated_query:
        return "Invalid query parameters. Please provide valid per_page (1-100), page (>=1), and optional menus filter."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/menu-items"
        params = {
            'per_page': validated_query.per_page,
            'page': validated_query.page
        }

        if validated_query.menus:
            params['menus'] = validated_query.menus

        print(f"DEBUG: Making request to {url} with params {params}")

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()

        menu_items = response.json()
        print(f"DEBUG: Retrieved {len(menu_items)} menu items")

        if not menu_items:
            menu_filter = f" from menu '{validated_query.menus}'" if validated_query.menus else ""
            return f"No menu items found{menu_filter} on page {validated_query.page}."

        result = f"Found {len(menu_items)} menu items"
        if validated_query.menus:
            result += f" from menu '{validated_query.menus}'"
        result += f" (page {validated_query.page}):\n\n"

        for i, menu_item in enumerate(menu_items, 1):
            title = menu_item.get('title', {})
            if isinstance(title, dict):
                title = title.get('rendered', 'Untitled')
            else:
                title = str(title) if title else 'Untitled'

            url_item = menu_item.get('url', 'N/A')
            menu_order = menu_item.get('menu_order', 0)
            parent = menu_item.get('parent', 0)
            object_type = menu_item.get('object', 'unknown')
            type_label = menu_item.get('type_label', 'Unknown')

            result += f"{i}. **{title}\n"
            result += f"   Type: {type_label} ({object_type})\n"
            result += f"   URL: {url_item}\n"
            result += f"   Order: {menu_order}\n"
            if parent > 0:
                result += f"   Parent ID: {parent}\n"
            result += "\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving menu items: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def get_blocks(per_page: int = 10, page: int = 1) -> str:
    """
    Retrieve WordPress reusable blocks from the site.
    Parameters:
    - per_page: Number of blocks to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    """
    print(f"DEBUG: get_blocks called with per_page={per_page}, page={page}")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/blocks"
        params = {
            'per_page': per_page,
            'page': page
        }

        print(f"DEBUG: Making request to {url} with params {params}")

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()

        blocks = response.json()
        print(f"DEBUG: Retrieved {len(blocks)} blocks")

        if not blocks:
            return f"No reusable blocks found on page {page}."

        result = f"Found {len(blocks)} reusable blocks (page {page}):\n\n"

        for i, block in enumerate(blocks, 1):
            title = block.get('title', {})
            if isinstance(title, dict):
                title = title.get('rendered', 'Untitled')
            else:
                title = str(title) if title else 'Untitled'

            status = block.get('status', 'unknown')
            date = block.get('date', '')[:10] if block.get('date') else 'Unknown date'

            # Get content preview
            content = block.get('content', {})
            if isinstance(content, dict):
                content_preview = content.get('rendered', '')[:200]
            else:
                content_preview = str(content)[:200] if content else ''

            content_preview = clean_html(content_preview)
            if len(content_preview) > 100:
                content_preview = content_preview[:100] + "..."

            result += f"{i}. **{title}\n"
            result += f"   Status: {status.title()}\n"
            result += f"   Date: {date}\n"
            if content_preview:
                result += f"   Content: {content_preview}\n"
            result += "\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving blocks: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def get_users(per_page: int = 10, page: int = 1, search: str = None, role: str = None) -> str:
    """
    Retrieve WordPress users from the site.
    Parameters:
    - per_page: Number of users to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - search: Optional search term to filter users
    - role: Optional role filter (subscriber, contributor, author, editor, administrator)
    """
    print(f"DEBUG: get_users called with per_page={per_page}, page={page}, search={search}, role={role}")

    # Validate query parameters
    query_data = {"per_page": per_page, "page": page}
    if search:
        query_data["search"] = search
    if role:
        query_data["role"] = role

    validated_query = validate_user_query_params(query_data)
    if not validated_query:
        return "Invalid query parameters. Please provide valid per_page (1-100), page (>=1), and optional search term or role."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/users"
        params = {
            'per_page': validated_query.per_page,
            'page': validated_query.page,
            'context': 'view'
        }

        if validated_query.search:
            params['search'] = validated_query.search
        if validated_query.role:
            params['roles'] = validated_query.role

        print(f"DEBUG: Making request to {url} with params {params}")

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()

        users = response.json()
        print(f"DEBUG: Retrieved {len(users)} users")

        if not users:
            filter_info = ""
            if validated_query.search:
                filter_info += f" matching '{validated_query.search}'"
            if validated_query.role:
                filter_info += f" with role '{validated_query.role}'"
            return f"No users found{filter_info} on page {validated_query.page}."

        result = f"Found {len(users)} users"
        if validated_query.search:
            result += f" matching '{validated_query.search}'"
        if validated_query.role:
            result += f" with role '{validated_query.role}'"
        result += f" (page {validated_query.page}):\n\n"

        for i, user in enumerate(users, 1):
            username = user.get('slug', 'unknown')
            name = user.get('name', 'No name')
            email = user.get('email', 'No email')
            roles = user.get('roles', [])
            registered = user.get('registered_date', '')[:10] if user.get('registered_date') else 'Unknown'

            result += f"{i}. **{name}** (@{username})\n"
            result += f"   Email: {email}\n"
            result += f"   Roles: {', '.join(roles)}\n"
            result += f"   Registered: {registered}\n"
            result += f"   ID: {user.get('id', 'N/A')}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving users: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def create_user(username: str, email: str, password: str, name: str = None, roles: list = None) -> str:
    """
    Create a new WordPress user.
    Parameters:
    - username: Username for the new user (required)
    - email: Email address for the new user (required)
    - password: Password for the new user (required, min 6 chars)
    - name: Display name for the user (optional)
    - roles: List of user roles (default: ["subscriber"])
    """
    print(f"DEBUG: create_user called with username='{username}', email='{email}'")

    # Validate user data
    user_data = {"username": username, "email": email, "password": password}
    if name:
        user_data["name"] = name
    if roles:
        user_data["roles"] = roles

    validated_user = validate_user_data(user_data)
    if not validated_user:
        return "Invalid user data. Please provide:\n- username (non-empty string)\n- email (valid email address)\n- password (min 6 characters)\n- name (optional)\n- roles (optional list)"

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/users"
        data = {
            'username': validated_user.username,
            'email': validated_user.email,
            'password': validated_user.password,
            'roles': validated_user.roles
        }

        if validated_user.name:
            data['name'] = validated_user.name

        print(f"DEBUG: Making POST request to {url}")

        response = requests.post(url, headers=get_wordpress_headers(), json=data, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code not in [200, 201]:
            print(f"DEBUG: Response text: {response.text[:300]}")

        response.raise_for_status()

        user_response = response.json()
        user_id = user_response.get('id')

        return f"✅ User created successfully!\n\n" \
               f"**Username:** {validated_user.username}\n" \
               f"**Email:** {validated_user.email}\n" \
               f"**Name:** {validated_user.name or 'Not provided'}\n" \
               f"**Roles:** {', '.join(validated_user.roles)}\n" \
               f"**ID:** {user_id}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to create users."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error creating user: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error creating user: {str(e)}"

@Tool
def get_comments(per_page: int = 10, page: int = 1, search: str = None, post: int = None, status: str = None) -> str:
    """
    Retrieve WordPress comments from the site.
    Parameters:
    - per_page: Number of comments to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - search: Optional search term to filter comments
    - post: Optional post ID to filter comments by
    - status: Optional status filter (approve, hold, spam, trash)
    """
    print(f"DEBUG: get_comments called with per_page={per_page}, page={page}, search={search}, post={post}, status={status}")

    # Validate query parameters
    query_data = {"per_page": per_page, "page": page}
    if search:
        query_data["search"] = search
    if post:
        query_data["post"] = post
    if status:
        query_data["status"] = status

    validated_query = validate_comment_query_params(query_data)
    if not validated_query:
        return "Invalid query parameters. Please provide valid per_page (1-100), page (>=1), and optional search term, post ID, or status."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/comments"
        params = {
            'per_page': validated_query.per_page,
            'page': validated_query.page
        }

        if validated_query.search:
            params['search'] = validated_query.search
        if validated_query.post:
            params['post'] = validated_query.post
        if validated_query.status:
            params['status'] = validated_query.status

        print(f"DEBUG: Making request to {url} with params {params}")

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()

        comments = response.json()
        print(f"DEBUG: Retrieved {len(comments)} comments")

        if not comments:
            filter_info = ""
            if validated_query.search:
                filter_info += f" matching '{validated_query.search}'"
            if validated_query.post:
                filter_info += f" on post {validated_query.post}"
            if validated_query.status:
                filter_info += f" with status '{validated_query.status}'"
            return f"No comments found{filter_info} on page {validated_query.page}."

        result = f"Found {len(comments)} comments"
        if validated_query.search:
            result += f" matching '{validated_query.search}'"
        if validated_query.post:
            result += f" on post {validated_query.post}"
        if validated_query.status:
            result += f" with status '{validated_query.status}'"
        result += f" (page {validated_query.page}):\n\n"

        for i, comment in enumerate(comments, 1):
            content = comment.get('content', {})
            if isinstance(content, dict):
                content_text = content.get('rendered', 'No content')
            else:
                content_text = str(content) if content else 'No content'

            author_name = comment.get('author_name', 'Anonymous')
            status = comment.get('status', 'unknown')
            date = comment.get('date', '')[:10] if comment.get('date') else 'Unknown date'
            post_id = comment.get('post', 'N/A')

            # Clean and truncate content
            content_clean = clean_html(content_text)
            if len(content_clean) > 150:
                content_clean = content_clean[:150] + "..."

            result += f"{i}. **{author_name}** (Status: {status.title()})\n"
            result += f"   Date: {date}\n"
            result += f"   Post ID: {post_id}\n"
            result += f"   Content: {content_clean}\n"
            result += f"   ID: {comment.get('id', 'N/A')}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving comments: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def get_categories(per_page: int = 10, page: int = 1, search: str = None, parent: int = None) -> str:
    """
    Retrieve WordPress categories from the site.
    Parameters:
    - per_page: Number of categories to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - search: Optional search term to filter categories
    - parent: Optional parent category ID to filter by
    """
    print(f"DEBUG: get_categories called with per_page={per_page}, page={page}, search={search}, parent={parent}")

    # Validate query parameters
    query_data = {"per_page": per_page, "page": page}
    if search:
        query_data["search"] = search
    if parent is not None:
        query_data["parent"] = parent

    validated_query = validate_category_query_params(query_data)
    if not validated_query:
        return "Invalid query parameters. Please provide valid per_page (1-100), page (>=1), and optional search term or parent ID."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/categories"
        params = {
            'per_page': validated_query.per_page,
            'page': validated_query.page
        }

        if validated_query.search:
            params['search'] = validated_query.search
        if validated_query.parent is not None:
            params['parent'] = validated_query.parent

        print(f"DEBUG: Making request to {url} with params {params}")

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()

        categories = response.json()
        print(f"DEBUG: Retrieved {len(categories)} categories")

        if not categories:
            filter_info = ""
            if validated_query.search:
                filter_info += f" matching '{validated_query.search}'"
            if validated_query.parent is not None:
                filter_info += f" under parent {validated_query.parent}"
            return f"No categories found{filter_info} on page {validated_query.page}."

        result = f"Found {len(categories)} categories"
        if validated_query.search:
            result += f" matching '{validated_query.search}'"
        if validated_query.parent is not None:
            result += f" under parent {validated_query.parent}"
        result += f" (page {validated_query.page}):\n\n"

        for i, category in enumerate(categories, 1):
            name = category.get('name', 'Unnamed')
            slug = category.get('slug', 'no-slug')
            description = category.get('description', 'No description')
            count = category.get('count', 0)
            parent_id = category.get('parent', 0)

            result += f"{i}. **{name}** ({slug})\n"
            result += f"   Description: {description or 'None'}\n"
            result += f"   Post Count: {count}\n"
            if parent_id > 0:
                result += f"   Parent ID: {parent_id}\n"
            result += f"   ID: {category.get('id', 'N/A')}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving categories: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def create_category(name: str, description: str = "", slug: str = None, parent: int = 0) -> str:
    """
    Create a new WordPress category.
    Parameters:
    - name: Category name (required)
    - description: Category description (optional)
    - slug: Category slug (optional, auto-generated if not provided)
    - parent: Parent category ID (optional, 0 for top-level)
    """
    print(f"DEBUG: create_category called with name='{name}'")

    # Validate category data
    category_data = {"name": name, "description": description, "parent": parent}
    if slug:
        category_data["slug"] = slug

    validated_category = validate_category_data(category_data)
    if not validated_category:
        return "Invalid category data. Please provide:\n- name (non-empty string)\n- description (optional)\n- slug (optional)\n- parent (optional parent category ID)"

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/categories"
        data = {
            'name': validated_category.name,
            'description': validated_category.description,
            'parent': validated_category.parent
        }

        if validated_category.slug:
            data['slug'] = validated_category.slug

        print(f"DEBUG: Making POST request to {url}")

        response = requests.post(url, headers=get_wordpress_headers(), json=data, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code not in [200, 201]:
            print(f"DEBUG: Response text: {response.text[:300]}")

        response.raise_for_status()

        category_response = response.json()
        category_id = category_response.get('id')
        category_slug = category_response.get('slug')

        return f"✅ Category created successfully!\n\n" \
               f"**Name:** {validated_category.name}\n" \
               f"**Slug:** {category_slug}\n" \
               f"**Description:** {validated_category.description or 'None'}\n" \
               f"**Parent ID:** {validated_category.parent}\n" \
               f"**ID:** {category_id}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to create categories."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error creating category: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error creating category: {str(e)}"

@Tool
def get_tags(per_page: int = 10, page: int = 1, search: str = None) -> str:
    """
    Retrieve WordPress tags from the site.
    Parameters:
    - per_page: Number of tags to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    - search: Optional search term to filter tags
    """
    print(f"DEBUG: get_tags called with per_page={per_page}, page={page}, search={search}")

    # Validate query parameters
    query_data = {"per_page": per_page, "page": page}
    if search:
        query_data["search"] = search

    validated_query = validate_tag_query_params(query_data)
    if not validated_query:
        return "Invalid query parameters. Please provide valid per_page (1-100), page (>=1), and optional search term."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/tags"
        params = {
            'per_page': validated_query.per_page,
            'page': validated_query.page
        }

        if validated_query.search:
            params['search'] = validated_query.search

        print(f"DEBUG: Making request to {url} with params {params}")

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()

        tags = response.json()
        print(f"DEBUG: Retrieved {len(tags)} tags")

        if not tags:
            search_info = f" matching '{validated_query.search}'" if validated_query.search else ""
            return f"No tags found{search_info} on page {validated_query.page}."

        result = f"Found {len(tags)} tags"
        if validated_query.search:
            result += f" matching '{validated_query.search}'"
        result += f" (page {validated_query.page}):\n\n"

        for i, tag in enumerate(tags, 1):
            name = tag.get('name', 'Unnamed')
            slug = tag.get('slug', 'no-slug')
            description = tag.get('description', 'No description')
            count = tag.get('count', 0)

            result += f"{i}. **{name}** ({slug})\n"
            result += f"   Description: {description or 'None'}\n"
            result += f"   Post Count: {count}\n"
            result += f"   ID: {tag.get('id', 'N/A')}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving tags: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def create_tag(name: str, description: str = "", slug: str = None) -> str:
    """
    Create a new WordPress tag.
    Parameters:
    - name: Tag name (required)
    - description: Tag description (optional)
    - slug: Tag slug (optional, auto-generated if not provided)
    """
    print(f"DEBUG: create_tag called with name='{name}'")

    # Validate tag data
    tag_data = {"name": name, "description": description}
    if slug:
        tag_data["slug"] = slug

    validated_tag = validate_tag_data(tag_data)
    if not validated_tag:
        return "Invalid tag data. Please provide:\n- name (non-empty string)\n- description (optional)\n- slug (optional)"

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/tags"
        data = {
            'name': validated_tag.name,
            'description': validated_tag.description
        }

        if validated_tag.slug:
            data['slug'] = validated_tag.slug

        print(f"DEBUG: Making POST request to {url}")

        response = requests.post(url, headers=get_wordpress_headers(), json=data, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code not in [200, 201]:
            print(f"DEBUG: Response text: {response.text[:300]}")

        response.raise_for_status()

        tag_response = response.json()
        tag_id = tag_response.get('id')
        tag_slug = tag_response.get('slug')

        return f"✅ Tag created successfully!\n\n" \
               f"**Name:** {validated_tag.name}\n" \
               f"**Slug:** {tag_slug}\n" \
               f"**Description:** {validated_tag.description or 'None'}\n" \
               f"**ID:** {tag_id}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to create tags."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error creating tag: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error creating tag: {str(e)}"

@Tool
def update_post(post_id: int, title: str = None, content: str = None, status: str = None, excerpt: str = None, categories: list = None, tags: list = None) -> str:
    """
    Update an existing WordPress post.
    Parameters:
    - post_id: The ID of the post to update (required)
    - title: Updated title (optional)
    - content: Updated content (optional)
    - status: Updated status - 'draft', 'publish', or 'private' (optional)
    - excerpt: Updated excerpt (optional)
    - categories: List of category IDs (optional)
    - tags: List of tag IDs (optional)
    """
    print(f"DEBUG: update_post called with post_id={post_id}")

    # Build update data
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if content is not None:
        update_data["content"] = content
    if status is not None:
        update_data["status"] = status
    if excerpt is not None:
        update_data["excerpt"] = excerpt
    if categories is not None:
        update_data["categories"] = categories
    if tags is not None:
        update_data["tags"] = tags

    if not update_data:
        return "No update data provided. Please provide at least one field to update."

    validated_update = validate_post_update_data(update_data)
    if not validated_update:
        return "Invalid update data provided."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts/{post_id}"
        data = {}

        if validated_update.title is not None:
            data['title'] = validated_update.title
        if validated_update.content is not None:
            data['content'] = validated_update.content
        if validated_update.status is not None:
            data['status'] = validated_update.status
        if validated_update.excerpt is not None:
            data['excerpt'] = validated_update.excerpt
        if validated_update.categories is not None:
            data['categories'] = validated_update.categories
        if validated_update.tags is not None:
            data['tags'] = validated_update.tags

        print(f"DEBUG: Making PATCH request to {url}")

        response = requests.patch(url, headers=get_wordpress_headers(), json=data, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code == 404:
            return f"❌ Post with ID {post_id} not found."

        response.raise_for_status()
        updated_post = response.json()

        title_updated = updated_post.get('title', {})
        if isinstance(title_updated, dict):
            title_updated = title_updated.get('rendered', 'Unknown')

        return f"✅ Post updated successfully!\n\n" \
               f"**Title:** {title_updated}\n" \
               f"**Status:** {updated_post.get('status', 'unknown').title()}\n" \
               f"**ID:** {post_id}\n" \
               f"**URL:** {updated_post.get('link', 'N/A')}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to update posts."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error updating post: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error updating post: {str(e)}"

@Tool
def delete_post(post_id: int) -> str:
    """
    Delete a WordPress post by ID.
    Parameters:
    - post_id: The ID of the post to delete (required)
    """
    print(f"DEBUG: delete_post called with post_id={post_id}")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts/{post_id}"

        print(f"DEBUG: Making DELETE request to {url}")

        response = requests.delete(url, headers=get_wordpress_headers(), timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code == 404:
            return f"❌ Post with ID {post_id} not found."

        response.raise_for_status()
        deleted_post = response.json()

        title = deleted_post.get('title', {})
        if isinstance(title, dict):
            title = title.get('rendered', 'Unknown')

        return f"✅ Post deleted successfully!\n\n" \
               f"**Title:** {title}\n" \
               f"**ID:** {post_id}\n" \
               f"**Status:** Deleted"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to delete posts."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error deleting post: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error deleting post: {str(e)}"

@Tool
def update_page(page_id: int, title: str = None, content: str = None, status: str = None, parent: int = None) -> str:
    """
    Update an existing WordPress page.
    Parameters:
    - page_id: The ID of the page to update (required)
    - title: Updated title (optional)
    - content: Updated content (optional)
    - status: Updated status - 'draft', 'publish', or 'private' (optional)
    - parent: Updated parent page ID (optional)
    """
    print(f"DEBUG: update_page called with page_id={page_id}")

    # Build update data
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if content is not None:
        update_data["content"] = content
    if status is not None:
        update_data["status"] = status
    if parent is not None:
        update_data["parent"] = parent

    if not update_data:
        return "No update data provided. Please provide at least one field to update."

    validated_update = validate_page_update_data(update_data)
    if not validated_update:
        return "Invalid update data provided."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/pages/{page_id}"
        data = {}

        if validated_update.title is not None:
            data['title'] = validated_update.title
        if validated_update.content is not None:
            data['content'] = validated_update.content
        if validated_update.status is not None:
            data['status'] = validated_update.status
        if validated_update.parent is not None:
            data['parent'] = validated_update.parent

        print(f"DEBUG: Making PATCH request to {url}")

        response = requests.patch(url, headers=get_wordpress_headers(), json=data, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code == 404:
            return f"❌ Page with ID {page_id} not found."

        response.raise_for_status()
        updated_page = response.json()

        title_updated = updated_page.get('title', {})
        if isinstance(title_updated, dict):
            title_updated = title_updated.get('rendered', 'Unknown')

        return f"✅ Page updated successfully!\n\n" \
               f"**Title:** {title_updated}\n" \
               f"**Status:** {updated_page.get('status', 'unknown').title()}\n" \
               f"**ID:** {page_id}\n" \
               f"**URL:** {updated_page.get('link', 'N/A')}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to update pages."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error updating page: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error updating page: {str(e)}"

@Tool
def delete_page(page_id: int) -> str:
    """
    Delete a WordPress page by ID.
    Parameters:
    - page_id: The ID of the page to delete (required)
    """
    print(f"DEBUG: delete_page called with page_id={page_id}")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/pages/{page_id}"

        print(f"DEBUG: Making DELETE request to {url}")

        response = requests.delete(url, headers=get_wordpress_headers(), timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code == 404:
            return f"❌ Page with ID {page_id} not found."

        response.raise_for_status()
        deleted_page = response.json()

        title = deleted_page.get('title', {})
        if isinstance(title, dict):
            title = title.get('rendered', 'Unknown')

        return f"✅ Page deleted successfully!\n\n" \
               f"**Title:** {title}\n" \
               f"**ID:** {page_id}\n" \
               f"**Status:** Deleted"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to delete pages."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error deleting page: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error deleting page: {str(e)}"

@Tool
def update_user(user_id: int, name: str = None, email: str = None, roles: list = None, password: str = None) -> str:
    """
    Update an existing WordPress user.
    Parameters:
    - user_id: The ID of the user to update (required)
    - name: Updated display name (optional)
    - email: Updated email address (optional)
    - roles: Updated user roles (optional)
    - password: New password (optional, min 6 chars)
    """
    print(f"DEBUG: update_user called with user_id={user_id}")

    # Build update data
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if email is not None:
        update_data["email"] = email
    if roles is not None:
        update_data["roles"] = roles
    if password is not None:
        update_data["password"] = password

    if not update_data:
        return "No update data provided. Please provide at least one field to update."

    validated_update = validate_user_update_data(update_data)
    if not validated_update:
        return "Invalid update data provided."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/users/{user_id}"
        data = {}

        if validated_update.name is not None:
            data['name'] = validated_update.name
        if validated_update.email is not None:
            data['email'] = validated_update.email
        if validated_update.roles is not None:
            data['roles'] = validated_update.roles
        if validated_update.password is not None:
            data['password'] = validated_update.password

        print(f"DEBUG: Making PATCH request to {url}")

        response = requests.patch(url, headers=get_wordpress_headers(), json=data, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code == 404:
            return f"❌ User with ID {user_id} not found."

        response.raise_for_status()
        updated_user = response.json()

        return f"✅ User updated successfully!\n\n" \
               f"**Name:** {updated_user.get('name', 'Unknown')}\n" \
               f"**Email:** {updated_user.get('email', 'Unknown')}\n" \
               f"**Roles:** {', '.join(updated_user.get('roles', []))}\n" \
               f"**ID:** {user_id}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to update users."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error updating user: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error updating user: {str(e)}"

@Tool
def delete_user(user_id: int, reassign_to: int = None) -> str:
    """
    Delete a WordPress user by ID.
    Parameters:
    - user_id: The ID of the user to delete (required)
    - reassign_to: User ID to reassign content to (optional)
    """
    print(f"DEBUG: delete_user called with user_id={user_id}")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/users/{user_id}"
        params = {'force': True}

        if reassign_to:
            params['reassign'] = reassign_to

        print(f"DEBUG: Making DELETE request to {url}")

        response = requests.delete(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code == 404:
            return f"❌ User with ID {user_id} not found."

        response.raise_for_status()
        deleted_user = response.json()

        return f"✅ User deleted successfully!\n\n" \
               f"**Name:** {deleted_user.get('name', 'Unknown')}\n" \
               f"**ID:** {user_id}\n" \
               f"**Status:** Deleted"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to delete users."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error deleting user: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error deleting user: {str(e)}"

@Tool
def get_post_types() -> str:
    """
    Retrieve all available post types from the WordPress site.
    """
    print("DEBUG: get_post_types called")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/types"
        print(f"DEBUG: Making request to {url}")

        response = requests.get(url, headers=get_wordpress_headers(), timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()
        post_types = response.json()
        print(f"DEBUG: Retrieved {len(post_types)} post types")

        if not post_types:
            return "No post types found."

        result = f"Found {len(post_types)} post types:\n\n"

        for i, (type_key, post_type) in enumerate(post_types.items(), 1):
            name = post_type.get('name', 'Unnamed')
            description = post_type.get('description', 'No description')
            hierarchical = post_type.get('hierarchical', False)
            public = post_type.get('viewable', False)
            rest_base = post_type.get('rest_base', 'N/A')

            result += f"{i}. **{name}** ({type_key})\n"
            result += f"   Description: {description}\n"
            result += f"   Hierarchical: {'Yes' if hierarchical else 'No'}\n"
            result += f"   Public: {'Yes' if public else 'No'}\n"
            result += f"   REST Base: {rest_base}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving post types: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def get_post_statuses() -> str:
    """
    Retrieve all available post statuses from the WordPress site.
    """
    print("DEBUG: get_post_statuses called")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/statuses"
        print(f"DEBUG: Making request to {url}")

        response = requests.get(url, headers=get_wordpress_headers(), timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()
        statuses = response.json()
        print(f"DEBUG: Retrieved {len(statuses)} post statuses")

        if not statuses:
            return "No post statuses found."

        result = f"Found {len(statuses)} post statuses:\n\n"

        for i, (status_key, status) in enumerate(statuses.items(), 1):
            name = status.get('name', 'Unnamed')
            public = status.get('public', False)
            queryable = status.get('queryable', False)
            show_in_list = status.get('show_in_admin_status_list', False)

            result += f"{i}. **{name}** ({status_key})\n"
            result += f"   Public: {'Yes' if public else 'No'}\n"
            result += f"   Queryable: {'Yes' if queryable else 'No'}\n"
            result += f"   Show in Admin: {'Yes' if show_in_list else 'No'}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving post statuses: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def get_taxonomies() -> str:
    """
    Retrieve all available taxonomies from the WordPress site.
    """
    print("DEBUG: get_taxonomies called")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/taxonomies"
        print(f"DEBUG: Making request to {url}")

        response = requests.get(url, headers=get_wordpress_headers(), timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()
        taxonomies = response.json()
        print(f"DEBUG: Retrieved {len(taxonomies)} taxonomies")

        if not taxonomies:
            return "No taxonomies found."

        result = f"Found {len(taxonomies)} taxonomies:\n\n"

        for i, (tax_key, taxonomy) in enumerate(taxonomies.items(), 1):
            name = taxonomy.get('name', 'Unnamed')
            description = taxonomy.get('description', 'No description')
            hierarchical = taxonomy.get('hierarchical', False)
            public = taxonomy.get('public', False)
            rest_base = taxonomy.get('rest_base', 'N/A')
            object_types = taxonomy.get('types', [])

            result += f"{i}. **{name}** ({tax_key})\n"
            result += f"   Description: {description}\n"
            result += f"   Hierarchical: {'Yes' if hierarchical else 'No'}\n"
            result += f"   Public: {'Yes' if public else 'No'}\n"
            result += f"   REST Base: {rest_base}\n"
            result += f"   Object Types: {', '.join(object_types) if object_types else 'None'}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving taxonomies: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def get_themes() -> str:
    """
    Retrieve all available themes from the WordPress site.
    """
    print("DEBUG: get_themes called")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/themes"
        print(f"DEBUG: Making request to {url}")

        response = requests.get(url, headers=get_wordpress_headers(), timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()
        themes = response.json()
        print(f"DEBUG: Retrieved {len(themes)} themes")

        if not themes:
            return "No themes found."

        result = f"Found {len(themes)} themes:\n\n"

        for i, theme in enumerate(themes, 1):
            name = theme.get('name', {})
            if isinstance(name, dict):
                name = name.get('rendered', 'Unnamed')

            stylesheet = theme.get('stylesheet', 'unknown')
            description = theme.get('description', {})
            if isinstance(description, dict):
                description = description.get('rendered', 'No description')

            version = theme.get('version', 'Unknown')
            author = theme.get('author', {})
            if isinstance(author, dict):
                author = author.get('rendered', 'Unknown')

            status = theme.get('status', 'unknown')

            result += f"{i}. **{name}** ({stylesheet})\n"
            result += f"   Author: {clean_html(str(author))}\n"
            result += f"   Version: {version}\n"
            result += f"   Status: {status.title()}\n"
            description_clean = clean_html(str(description))
            if len(description_clean) > 100:
                description_clean = description_clean[:100] + "..."
            result += f"   Description: {description_clean}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving themes: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def search_content(search_term: str, per_page: int = 10, page: int = 1) -> str:
    """
    Search across all WordPress content types (posts, pages, etc.).
    Parameters:
    - search_term: Search term to look for (required)
    - per_page: Number of results to retrieve (1-100, default: 10)
    - page: Page number to retrieve (default: 1)
    """
    print(f"DEBUG: search_content called with search_term='{search_term}', per_page={per_page}, page={page}")

    if not search_term or len(search_term.strip()) < 2:
        return "Search term must be at least 2 characters long."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/search"
        params = {
            'search': search_term.strip(),
            'per_page': min(max(per_page, 1), 100),
            'page': max(page, 1)
        }

        print(f"DEBUG: Making request to {url} with params {params}")

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()
        results = response.json()
        print(f"DEBUG: Retrieved {len(results)} search results")

        if not results:
            return f"No content found matching '{search_term}'."

        result = f"Found {len(results)} results for '{search_term}' (page {params['page']}):\n\n"

        for i, item in enumerate(results, 1):
            title = item.get('title', 'Untitled')
            item_type = item.get('type', 'unknown')
            subtype = item.get('subtype', 'unknown')
            url = item.get('url', 'N/A')

            result += f"{i}. **{title}\n"
            result += f"   Type: {item_type.title()} ({subtype})\n"
            result += f"   URL: {url}\n"
            result += f"   ID: {item.get('id', 'N/A')}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Error searching content: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

@Tool
def update_category(category_id: int, name: str = None, description: str = None, parent: int = None) -> str:
    """
    Update an existing WordPress category.
    Parameters:
    - category_id: The ID of the category to update (required)
    - name: Updated category name (optional)
    - description: Updated description (optional)
    - parent: Updated parent category ID (optional)
    """
    print(f"DEBUG: update_category called with category_id={category_id}")

    # Build update data
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if parent is not None:
        update_data["parent"] = parent

    if not update_data:
        return "No update data provided. Please provide at least one field to update."

    validated_update = validate_category_update_data(update_data)
    if not validated_update:
        return "Invalid update data provided."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/categories/{category_id}"
        data = {}

        if validated_update.name is not None:
            data['name'] = validated_update.name
        if validated_update.description is not None:
            data['description'] = validated_update.description
        if validated_update.parent is not None:
            data['parent'] = validated_update.parent

        print(f"DEBUG: Making PATCH request to {url}")

        response = requests.patch(url, headers=get_wordpress_headers(), json=data, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code == 404:
            return f"❌ Category with ID {category_id} not found."

        response.raise_for_status()
        updated_category = response.json()

        return f"✅ Category updated successfully!\n\n" \
               f"**Name:** {updated_category.get('name', 'Unknown')}\n" \
               f"**Slug:** {updated_category.get('slug', 'unknown')}\n" \
               f"**Description:** {updated_category.get('description', 'None')}\n" \
               f"**Parent ID:** {updated_category.get('parent', 0)}\n" \
               f"**ID:** {category_id}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to update categories."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error updating category: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error updating category: {str(e)}"

@Tool
def delete_category(category_id: int) -> str:
    """
    Delete a WordPress category by ID.
    Parameters:
    - category_id: The ID of the category to delete (required)
    """
    print(f"DEBUG: delete_category called with category_id={category_id}")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/categories/{category_id}"
        params = {'force': True}

        print(f"DEBUG: Making DELETE request to {url}")

        response = requests.delete(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code == 404:
            return f"❌ Category with ID {category_id} not found."

        response.raise_for_status()
        deleted_category = response.json()

        return f"✅ Category deleted successfully!\n\n" \
               f"**Name:** {deleted_category.get('name', 'Unknown')}\n" \
               f"**ID:** {category_id}\n" \
               f"**Status:** Deleted"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to delete categories."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error deleting category: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error deleting category: {str(e)}"

@Tool
def update_tag(tag_id: int, name: str = None, description: str = None) -> str:
    """
    Update an existing WordPress tag.
    Parameters:
    - tag_id: The ID of the tag to update (required)
    - name: Updated tag name (optional)
    - description: Updated description (optional)
    """
    print(f"DEBUG: update_tag called with tag_id={tag_id}")

    # Build update data
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description

    if not update_data:
        return "No update data provided. Please provide at least one field to update."

    validated_update = validate_tag_update_data(update_data)
    if not validated_update:
        return "Invalid update data provided."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/tags/{tag_id}"
        data = {}

        if validated_update.name is not None:
            data['name'] = validated_update.name
        if validated_update.description is not None:
            data['description'] = validated_update.description

        print(f"DEBUG: Making PATCH request to {url}")

        response = requests.patch(url, headers=get_wordpress_headers(), json=data, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code == 404:
            return f"❌ Tag with ID {tag_id} not found."

        response.raise_for_status()
        updated_tag = response.json()

        return f"✅ Tag updated successfully!\n\n" \
               f"**Name:** {updated_tag.get('name', 'Unknown')}\n" \
               f"**Slug:** {updated_tag.get('slug', 'unknown')}\n" \
               f"**Description:** {updated_tag.get('description', 'None')}\n" \
               f"**ID:** {tag_id}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to update tags."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error updating tag: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error updating tag: {str(e)}"

@Tool
def delete_tag(tag_id: int) -> str:
    """
    Delete a WordPress tag by ID.
    Parameters:
    - tag_id: The ID of the tag to delete (required)
    """
    print(f"DEBUG: delete_tag called with tag_id={tag_id}")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/tags/{tag_id}"
        params = {'force': True}

        print(f"DEBUG: Making DELETE request to {url}")

        response = requests.delete(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code == 404:
            return f"❌ Tag with ID {tag_id} not found."

        response.raise_for_status()
        deleted_tag = response.json()

        return f"✅ Tag deleted successfully!\n\n" \
               f"**Name:** {deleted_tag.get('name', 'Unknown')}\n" \
               f"**ID:** {tag_id}\n" \
               f"**Status:** Deleted"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to delete tags."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error deleting tag: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error deleting tag: {str(e)}"

@Tool
def update_comment(comment_id: int, content: str = None, status: str = None, author_name: str = None, author_email: str = None) -> str:
    """
    Update an existing WordPress comment.
    Parameters:
    - comment_id: The ID of the comment to update (required)
    - content: Updated comment content (optional)
    - status: Updated status - 'approve', 'hold', 'spam', 'trash' (optional)
    - author_name: Updated author name (optional)
    - author_email: Updated author email (optional)
    """
    print(f"DEBUG: update_comment called with comment_id={comment_id}")

    # Build update data
    update_data = {}
    if content is not None:
        update_data["content"] = content
    if status is not None:
        update_data["status"] = status
    if author_name is not None:
        update_data["author_name"] = author_name
    if author_email is not None:
        update_data["author_email"] = author_email

    if not update_data:
        return "No update data provided. Please provide at least one field to update."

    validated_update = validate_comment_update_data(update_data)
    if not validated_update:
        return "Invalid update data provided."

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/comments/{comment_id}"
        data = {}

        if validated_update.content is not None:
            data['content'] = validated_update.content
        if validated_update.status is not None:
            data['status'] = validated_update.status
        if validated_update.author_name is not None:
            data['author_name'] = validated_update.author_name
        if validated_update.author_email is not None:
            data['author_email'] = validated_update.author_email

        print(f"DEBUG: Making PATCH request to {url}")

        response = requests.patch(url, headers=get_wordpress_headers(), json=data, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code == 404:
            return f"❌ Comment with ID {comment_id} not found."

        response.raise_for_status()
        updated_comment = response.json()

        content_text = updated_comment.get('content', {})
        if isinstance(content_text, dict):
            content_text = content_text.get('rendered', 'No content')
        content_clean = clean_html(str(content_text))[:100] + "..."

        return f"✅ Comment updated successfully!\n\n" \
               f"**Author:** {updated_comment.get('author_name', 'Unknown')}\n" \
               f"**Status:** {updated_comment.get('status', 'unknown').title()}\n" \
               f"**Content:** {content_clean}\n" \
               f"**ID:** {comment_id}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to update comments."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error updating comment: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error updating comment: {str(e)}"

@Tool
def delete_comment(comment_id: int, force: bool = False) -> str:
    """
    Delete a WordPress comment by ID.
    Parameters:
    - comment_id: The ID of the comment to delete (required)
    - force: Permanently delete (true) or move to trash (false, default)
    """
    print(f"DEBUG: delete_comment called with comment_id={comment_id}, force={force}")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/comments/{comment_id}"
        params = {'force': force}

        print(f"DEBUG: Making DELETE request to {url}")

        response = requests.delete(url, headers=get_wordpress_headers(), params=params, timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        if response.status_code == 404:
            return f"❌ Comment with ID {comment_id} not found."

        response.raise_for_status()
        deleted_comment = response.json()

        action = "permanently deleted" if force else "moved to trash"

        return f"✅ Comment {action} successfully!\n\n" \
               f"**Author:** {deleted_comment.get('author_name', 'Unknown')}\n" \
               f"**ID:** {comment_id}\n" \
               f"**Status:** {'Deleted' if force else 'Trashed'}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to delete comments."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error deleting comment: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error deleting comment: {str(e)}"

@Tool
def get_site_settings() -> str:
    """
    Get WordPress site settings.
    """
    print("DEBUG: get_site_settings called")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/settings"
        print(f"DEBUG: Making request to {url}")

        response = requests.get(url, headers=get_wordpress_headers(), timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()
        settings = response.json()

        result = "⚙️ **WordPress Site Settings:\n\n"

        # Key settings to display
        key_settings = {
            'title': 'Site Title',
            'description': 'Tagline',
            'url': 'WordPress Address (URL)',
            'email': 'Admin Email',
            'timezone': 'Timezone',
            'date_format': 'Date Format',
            'time_format': 'Time Format',
            'start_of_week': 'Week Starts On',
            'language': 'Site Language',
            'use_smilies': 'Convert emoticons',
            'default_ping_status': 'Default ping status',
            'default_comment_status': 'Default comment status'
        }

        for key, label in key_settings.items():
            value = settings.get(key, 'Not set')
            if isinstance(value, bool):
                value = 'Enabled' if value else 'Disabled'
            elif isinstance(value, int) and key == 'start_of_week':
                days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                value = days[value] if 0 <= value < 7 else str(value)

            result += f"**{label}:** {value}\n"

        return result

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to view settings."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error retrieving settings: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@Tool
def get_templates() -> str:
    """
    Get WordPress block templates.
    """
    print("DEBUG: get_templates called")

    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/templates"
        print(f"DEBUG: Making request to {url}")

        response = requests.get(url, headers=get_wordpress_headers(), timeout=15)
        print(f"DEBUG: Response status: {response.status_code}")

        response.raise_for_status()
        templates = response.json()

        if not templates:
            return "No block templates found."

        result = f"Found {len(templates)} block templates:\n\n"

        for i, template in enumerate(templates, 1):
            title = template.get('title', {})
            if isinstance(title, dict):
                title = title.get('rendered', 'Untitled')

            slug = template.get('slug', 'unknown')
            theme = template.get('theme', 'unknown')
            template_type = template.get('type', 'wp_template')
            is_custom = template.get('is_custom', False)

            result += f"{i}. **{title}** ({slug})\n"
            result += f"   Theme: {theme}\n"
            result += f"   Type: {template_type}\n"
            result += f"   Custom: {'Yes' if is_custom else 'No'}\n"
            result += f"   ID: {template.get('id', 'N/A')}\n\n"

        return result

    except requests.exceptions.RequestException as e:
        return f"❌ Error retrieving templates: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@Tool
def get_site_info() -> str:
    """Get basic information about the WordPress site"""
    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json"
        response = requests.get(url)
        response.raise_for_status()

        site_info = response.json()
        return f"📝 **WordPress Site Information:\n\n" \
               f"**Site URL:** {WORDPRESS_BASE_URL}\n" \
               f"**Name:** {site_info.get('name', 'Unknown')}\n" \
               f"**Description:** {site_info.get('description', 'No description')}\n" \
               f"**WordPress Version:** {site_info.get('wp_version', 'Unknown')}\n" \
               f"**API Namespace:** {', '.join(site_info.get('namespaces', []))}"

    except Exception as e:
        return f"❌ Error getting site info: {str(e)}"

@Tool
def get_widgets() -> str:
    """Get all WordPress widgets from the widgets endpoint."""
    try:
        print("DEBUG: get_widgets called")

        headers = get_wordpress_headers()
        response = requests.get(f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/widgets", headers=headers)

        if response.status_code == 200:
            widgets = response.json()
            if not widgets:
                return "📦 No widgets found."

            result = "🧩 **WordPress Widgets:**\n\n"
            for widget in widgets:
                result += f"**{widget.get('id', 'Unknown ID')}**\n"
                result += f"**Type:** {widget.get('id_base', 'Unknown')}\n"
                result += f"**Title:** {widget.get('instance', {}).get('title', 'No title')}\n"
                result += f"**Sidebar:** {widget.get('sidebar', 'None')}\n\n"

            return result
        elif response.status_code == 401:
            return "❌ Unauthorized: Cannot access widgets endpoint."
        else:
            return f"❌ Error getting widgets: {response.status_code}"

    except Exception as e:
        return f"❌ Error getting widgets: {str(e)}"

@Tool
def get_revisions(post_id: int, per_page: int = 10, page: int = 1) -> str:
    """Get revisions for a specific post or page."""
    try:
        print(f"DEBUG: get_revisions called for post_id={post_id}")

        headers = get_wordpress_headers()
        params = {
            'per_page': per_page,
            'page': page
        }

        response = requests.get(
            f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts/{post_id}/revisions",
            headers=headers,
            params=params
        )

        if response.status_code == 200:
            revisions = response.json()
            if not revisions:
                return f"📝 No revisions found for post ID {post_id}."

            result = f"📚 **Revisions for Post ID {post_id}:**\n\n"
            for revision in revisions:
                result += f"**Revision ID:** {revision.get('id', 'Unknown')}\n"
                result += f"**Modified:** {revision.get('date', 'Unknown date')}\n"
                result += f"**Author:** {revision.get('author', 'Unknown')}\n"
                result += f"**Title:** {revision.get('title', {}).get('rendered', 'No title')}\n\n"

            return result
        elif response.status_code == 404:
            return f"❌ Post ID {post_id} not found or no revisions available."
        else:
            return f"❌ Error getting revisions: {response.status_code}"

    except Exception as e:
        return f"❌ Error getting revisions: {str(e)}"

@Tool
def optimize_site_cache() -> str:
    """Manage SiteGround cache optimization."""
    try:
        print("DEBUG: optimize_site_cache called")

        headers = get_wordpress_headers()

        # Try to get cache status first
        response = requests.get(f"{WORDPRESS_BASE_URL}/wp-json/siteground-optimizer/v1/cache", headers=headers)

        if response.status_code == 200:
            cache_data = response.json()
            return f"🚀 **SiteGround Cache Status:**\n\n" \
                   f"**File Cache:** {cache_data.get('file_cache', 'Unknown')}\n" \
                   f"**Browser Cache:** {cache_data.get('browser_cache', 'Unknown')}\n" \
                   f"**Memcached:** {cache_data.get('memcached', 'Unknown')}\n"
        elif response.status_code == 401:
            return "❌ Unauthorized: Cannot access SiteGround optimizer."
        else:
            return f"❌ SiteGround optimizer not available: {response.status_code}"

    except Exception as e:
        return f"❌ Error accessing SiteGround optimizer: {str(e)}"

@Tool
def get_site_health() -> str:
    """Get WordPress site health information."""
    try:
        print("DEBUG: get_site_health called")

        headers = get_wordpress_headers()
        response = requests.get(f"{WORDPRESS_BASE_URL}/wp-json/wp-site-health/v1/tests/page-cache", headers=headers)

        if response.status_code == 200:
            health_data = response.json()
            return f"🏥 **Site Health:**\n\n" \
                   f"**Status:** {health_data.get('status', 'Unknown')}\n" \
                   f"**Description:** {health_data.get('description', 'No description')}\n"
        else:
            # Fallback - just return basic site info
            return "🏥 **Site Health:** Information not available through REST API."

    except Exception as e:
        return f"❌ Error getting site health: {str(e)}"

# Initialize the Pydantic AI Agent
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

if not BEARER_TOKEN:
    raise ValueError("BEARER_TOKEN environment variable is required")

provider = GoogleProvider(api_key=GEMINI_API_KEY)
model = GoogleModel('gemini-2.5-flash', provider=provider)

agent = Agent(
    model=model,
    instrument=False,  # Disable instrumentation to reduce complexity
    tools=[get_posts, create_post, get_pages, create_page, get_media, get_menu_items, get_blocks,
           get_users, create_user, get_comments, get_categories, create_category, get_tags, create_tag,
           get_post_types, get_post_statuses, get_taxonomies, get_themes,
           get_site_settings, get_templates, search_content, get_site_info,
           update_post, delete_post, update_page, delete_page, update_user, delete_user,
           update_comment, delete_comment, update_category, delete_category, update_tag, delete_tag,
           get_widgets, get_revisions, optimize_site_cache, get_site_health],
    system_prompt="""You are a comprehensive WordPress content management assistant. You can help users with:

**Content Management:**
1. **Posts**: View, search, and create blog posts
2. **Pages**: View, search, and create static pages
3. **Media**: Browse and manage media files (images, videos, audio, documents)
4. **Blocks**: View reusable blocks
5. **Menu Items**: View navigation menu items
6. **Site Info**: Get basic WordPress site information

**Important Guidelines:**
- Always validate user input thoroughly before making API calls
- If a user wants to create content but doesn't provide all required information (title, content), ask for the missing details step by step
- When creating posts/pages, explain the different status options: 'draft' (default), 'publish', or 'private'
- Be helpful and guide users through the process step by step
- Use emojis and formatting to make responses more engaging and readable
- If there are errors, explain them clearly and suggest solutions
- Always ask for confirmation before publishing content
- Keep responses concise but informative

**Available Commands:**
- "show posts" or "get posts" - Retrieve recent posts
- "create post" or "write post" - Create a new blog post
- "search posts [term]" - Search for specific posts
- "show pages" or "get pages" - Retrieve pages
- "create page" - Create a new page
- "search pages [term]" - Search for specific pages
- "show media" or "get media" - Browse media files
- "media [type]" - Filter media by type (image, video, audio, application)
- "menu items" or "menus" - View menu items
- "blocks" or "reusable blocks" - View reusable blocks
- "site info" - Get WordPress site information

I have comprehensive access to the WordPress REST API and can perform most administrative tasks. Always feel free to ask for clarification or help with complex operations."""
)

# Store conversations in memory (in production, use a database)
conversations = {}

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

        # Process message with AI agent (synchronously)
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Loop is closed")
        except RuntimeError:
            # Create new event loop if none exists or is closed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(agent.run(message, message_history=message_history))
        except Exception as e:
            error_msg = str(e)
            print(f"Error running agent: {error_msg}")

            # Handle specific PydanticAI conversation flow errors
            if "function response turn" in error_msg.lower() or "invalid_argument" in error_msg.lower():
                # Clear conversation history to reset the flow
                message_history = []
                conversations[session_id] = message_history
                # Retry with clean history
                try:
                    result = loop.run_until_complete(agent.run(message, message_history=message_history))
                except Exception as retry_error:
                    return jsonify({'error': f'Agent error: {str(retry_error)}'}), 500
            # If there's an issue with the loop, create a fresh one
            elif loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(agent.run(message, message_history=message_history))
            else:
                raise

        # Update conversation history carefully to avoid function call flow issues
        new_messages = result.new_messages()

        # Filter out potential problematic messages that could cause function call flow errors
        safe_messages = []
        for msg in new_messages:
            # Only add messages that don't cause flow issues
            if hasattr(msg, 'content') and msg.content:
                safe_messages.append(msg)

        message_history.extend(safe_messages)

        # Keep conversation history manageable - more aggressive cleanup to prevent issues
        if len(message_history) > 10:
            message_history = message_history[-10:]

        conversations[session_id] = message_history

        return jsonify({
            'response': result.output,
            'session_id': session_id
        })

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_chat():
    session_id = session.get('chat_id')
    if session_id and session_id in conversations:
        conversations[session_id] = []
    return jsonify({'message': 'Chat history cleared'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)