from flask import Flask, render_template, request, jsonify, session
import os
import requests
from dotenv import load_dotenv
import uuid
import re
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# WordPress Configuration
WORDPRESS_BASE_URL = os.getenv('WORDPRESS_BASE_URL', 'https://vibebuilder.studio')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')

def get_wordpress_headers():
    """Get WordPress API headers with authentication"""
    return {
        'Authorization': f'Bearer {BEARER_TOKEN}',
        'Content-Type': 'application/json',
        'User-Agent': 'WordPress-Chatbot/1.0'
    }

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).strip()

def get_posts_direct(per_page=10, page=1, search=None):
    """Get posts directly from WordPress API"""
    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts"
        params = {'per_page': per_page, 'page': page}
        if search:
            params['search'] = search

        response = requests.get(url, headers=get_wordpress_headers(), params=params, timeout=15)
        response.raise_for_status()
        posts = response.json()

        if not posts:
            return "No posts found."

        result = f"Found {len(posts)} posts:\n\n"
        for i, post in enumerate(posts, 1):
            title = post.get('title', {}).get('rendered', 'Untitled')
            status = post.get('status', 'unknown')
            date = post.get('date', '')[:10]

            # Get preview
            excerpt = post.get('excerpt', {}).get('rendered', '')
            if not excerpt:
                content = post.get('content', {}).get('rendered', '')
                excerpt = content[:200] + "..." if len(content) > 200 else content

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
    except Exception as e:
        return f"Error retrieving posts: {str(e)}"

def create_post_direct(title, content, status='draft'):
    """Create post directly via WordPress API"""
    try:
        url = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts"
        data = {
            'title': title,
            'content': content,
            'status': status
        }

        response = requests.post(url, headers=get_wordpress_headers(), json=data, timeout=15)
        response.raise_for_status()

        post_response = response.json()
        post_id = post_response.get('id')
        post_url = post_response.get('link', 'N/A')

        return f"✅ Post created successfully!\n\n" \
               f"**Title:** {title}\n" \
               f"**Status:** {status.title()}\n" \
               f"**ID:** {post_id}\n" \
               f"**URL:** {post_url}"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Authentication failed. Please check your bearer token."
        elif e.response.status_code == 403:
            return "❌ Permission denied. You don't have permission to create posts."
        else:
            return f"❌ HTTP Error {e.response.status_code}: {e.response.text[:200]}"
    except Exception as e:
        return f"❌ Error creating post: {str(e)}"

def process_message(message, conversation_state):
    """Process user message and return response"""
    message = message.lower().strip()

    # Handle different commands
    if 'show' in message and 'post' in message:
        return get_posts_direct()

    elif 'get' in message and 'post' in message:
        return get_posts_direct()

    elif 'list' in message and 'post' in message:
        return get_posts_direct()

    elif 'search' in message and 'post' in message:
        # Extract search term
        words = message.split()
        search_term = None
        if 'search' in words:
            idx = words.index('search')
            if idx + 2 < len(words):  # search posts term
                search_term = words[idx + 2]
        return get_posts_direct(search=search_term)

    elif 'create' in message and 'post' in message:
        # Check if we're in the middle of creating a post
        if 'creating_post' not in conversation_state:
            conversation_state['creating_post'] = {'step': 'ask_title'}
            return "I'll help you create a new post! What would you like the title to be?"

        elif conversation_state['creating_post']['step'] == 'ask_title':
            conversation_state['creating_post']['title'] = message
            conversation_state['creating_post']['step'] = 'ask_content'
            return f"Great! The title is '{message}'. Now, what should the content be?"

        elif conversation_state['creating_post']['step'] == 'ask_content':
            conversation_state['creating_post']['content'] = message
            conversation_state['creating_post']['step'] = 'ask_status'
            return "Perfect! What status should this post have?\n- 'draft' (default)\n- 'publish' (live on site)\n- 'private' (hidden)"

        elif conversation_state['creating_post']['step'] == 'ask_status':
            status = 'draft'
            if 'publish' in message.lower():
                status = 'publish'
            elif 'private' in message.lower():
                status = 'private'

            # Create the post
            title = conversation_state['creating_post']['title']
            content = conversation_state['creating_post']['content']

            result = create_post_direct(title, content, status)

            # Clear the creation state
            del conversation_state['creating_post']

            return result

    elif 'site' in message and 'info' in message:
        try:
            url = f"{WORDPRESS_BASE_URL}/wp-json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                site_info = response.json()
                return f"**WordPress Site Information:**\n\n" \
                       f"**Site URL:** {WORDPRESS_BASE_URL}\n" \
                       f"**Name:** {site_info.get('name', 'Unknown')}\n" \
                       f"**Description:** {site_info.get('description', 'No description')}\n"
            else:
                return f"**WordPress Site:** {WORDPRESS_BASE_URL}\n**Status:** API accessible"
        except Exception as e:
            return f"Error getting site info: {str(e)}"

    elif 'help' in message:
        return """I can help you with these WordPress tasks:

**Available Commands:**
• "show posts" or "get posts" - View recent posts
• "create post" - Create a new blog post (I'll guide you step by step)
• "search posts [term]" - Search for specific posts
• "site info" - Get WordPress site information
• "help" - Show this help message

Just tell me what you'd like to do!"""

    else:
        # Default response for unrecognized messages
        # Check if we're in the middle of creating a post
        if 'creating_post' in conversation_state:
            step = conversation_state['creating_post']['step']
            if step == 'ask_title':
                conversation_state['creating_post']['title'] = message
                conversation_state['creating_post']['step'] = 'ask_content'
                return f"Great! The title is '{message}'. Now, what should the content be?"
            elif step == 'ask_content':
                conversation_state['creating_post']['content'] = message
                conversation_state['creating_post']['step'] = 'ask_status'
                return "Perfect! What status should this post have?\n- 'draft' (default)\n- 'publish' (live on site)\n- 'private' (hidden)"

        return """I'm your WordPress assistant! I can help you:

• **View posts** - Say "show posts"
• **Create posts** - Say "create post"
• **Search posts** - Say "search posts [term]"
• **Get site info** - Say "site info"

What would you like to do?"""

# Store conversations in memory
conversations = {}

@app.route('/')
def index():
    return render_template('improved_chat.html')

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

        # Get conversation state
        if session_id not in conversations:
            conversations[session_id] = {}

        conversation_state = conversations[session_id]

        # Process message
        response_text = process_message(message, conversation_state)

        # Update conversation state
        conversations[session_id] = conversation_state

        return jsonify({
            'response': response_text,
            'session_id': session_id
        })

    except Exception as e:
        print(f"Chat route error: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_chat():
    session_id = session.get('chat_id')
    if session_id and session_id in conversations:
        conversations[session_id] = {}
    return jsonify({'message': 'Chat history cleared'})

if __name__ == '__main__':
    print("Starting Simple WordPress Chat App on http://127.0.0.1:5003")
    app.run(debug=True, host='0.0.0.0', port=5003)