from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

class WordPressAPI:
    def __init__(self):
        self.base_url = os.getenv('WORDPRESS_BASE_URL', 'https://vibebuilder.studio')
        self.bearer_token = os.getenv('BEARER_TOKEN')
        self.headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }

    def get_posts(self, per_page=10, page=1):
        """Get WordPress posts"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts"
            params = {'per_page': per_page, 'page': page, '_embed': True}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def create_post(self, title, content, status='draft'):
        """Create a new WordPress post"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts"
            data = {
                'title': title,
                'content': content,
                'status': status
            }
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def get_post(self, post_id):
        """Get a specific WordPress post"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    # Pages API Methods
    def get_pages(self, per_page=10, page=1):
        """Get WordPress pages"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/pages"
            params = {'per_page': per_page, 'page': page, '_embed': True}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def create_page(self, title, content, status='draft', parent=0):
        """Create a new WordPress page"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/pages"
            data = {
                'title': title,
                'content': content,
                'status': status,
                'parent': parent
            }
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    # Media API Methods
    def get_media(self, per_page=10, page=1):
        """Get WordPress media files"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/media"
            params = {'per_page': per_page, 'page': page}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def upload_media(self, file_data, filename, title=None):
        """Upload a media file to WordPress"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/media"
            headers = {
                'Authorization': f'Bearer {self.bearer_token}',
                'Content-Disposition': f'attachment; filename="{filename}"'
            }

            files = {'file': (filename, file_data)}
            data = {'title': title or filename}

            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    # Menu Items API Methods
    def get_menu_items(self, per_page=50, page=1):
        """Get WordPress menu items"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/menu-items"
            params = {'per_page': per_page, 'page': page}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def create_menu_item(self, title, url, menu_order=0, parent=0):
        """Create a new WordPress menu item"""
        try:
            api_url = f"{self.base_url}/wp-json/wp/v2/menu-items"
            data = {
                'title': title,
                'url': url,
                'menu_order': menu_order,
                'parent': parent
            }
            response = requests.post(api_url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    # Blocks API Methods
    def get_blocks(self, per_page=10, page=1):
        """Get WordPress blocks"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/blocks"
            params = {'per_page': per_page, 'page': page}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def create_block(self, title, content, status='draft'):
        """Create a new WordPress block"""
        try:
            url = f"{self.base_url}/wp-json/wp/v2/blocks"
            data = {
                'title': title,
                'content': content,
                'status': status
            }
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

wp_api = WordPressAPI()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/posts')
def posts():
    page = request.args.get('page', 1, type=int)
    posts_data = wp_api.get_posts(per_page=10, page=page)

    if 'error' in posts_data:
        flash(f'Error fetching posts: {posts_data["error"]}', 'error')
        posts_data = []

    return render_template('posts.html', posts=posts_data, current_page=page)

@app.route('/posts/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        status = request.form.get('status', 'draft')

        if not title or not content:
            flash('Title and content are required!', 'error')
            return render_template('new_post.html')

        result = wp_api.create_post(title, content, status)

        if 'error' in result:
            flash(f'Error creating post: {result["error"]}', 'error')
            return render_template('new_post.html')
        else:
            flash('Post created successfully!', 'success')
            return redirect(url_for('posts'))

    return render_template('new_post.html')

@app.route('/api/posts')
def api_posts():
    """API endpoint for posts data"""
    page = request.args.get('page', 1, type=int)
    posts_data = wp_api.get_posts(per_page=10, page=page)
    return jsonify(posts_data)

# Pages Routes
@app.route('/pages')
def pages():
    page = request.args.get('page', 1, type=int)
    pages_data = wp_api.get_pages(per_page=10, page=page)

    if 'error' in pages_data:
        flash(f'Error fetching pages: {pages_data["error"]}', 'error')
        pages_data = []

    return render_template('pages.html', pages=pages_data, current_page=page)

@app.route('/pages/new', methods=['GET', 'POST'])
def new_page():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        status = request.form.get('status', 'draft')
        parent = request.form.get('parent', 0, type=int)

        if not title or not content:
            flash('Title and content are required!', 'error')
            return render_template('new_page.html', pages=wp_api.get_pages(per_page=50))

        result = wp_api.create_page(title, content, status, parent)

        if 'error' in result:
            flash(f'Error creating page: {result["error"]}', 'error')
            return render_template('new_page.html', pages=wp_api.get_pages(per_page=50))
        else:
            flash('Page created successfully!', 'success')
            return redirect(url_for('pages'))

    return render_template('new_page.html', pages=wp_api.get_pages(per_page=50))

# Media Routes
@app.route('/media')
def media():
    page = request.args.get('page', 1, type=int)
    media_data = wp_api.get_media(per_page=12, page=page)

    if 'error' in media_data:
        flash(f'Error fetching media: {media_data["error"]}', 'error')
        media_data = []

    return render_template('media.html', media=media_data, current_page=page)

@app.route('/media/upload', methods=['GET', 'POST'])
def upload_media():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return render_template('upload_media.html')

        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'error')
            return render_template('upload_media.html')

        title = request.form.get('title')
        result = wp_api.upload_media(file.read(), file.filename, title)

        if 'error' in result:
            flash(f'Error uploading file: {result["error"]}', 'error')
            return render_template('upload_media.html')
        else:
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('media'))

    return render_template('upload_media.html')

# Menu Items Routes
@app.route('/menu-items')
def menu_items():
    page = request.args.get('page', 1, type=int)
    menu_data = wp_api.get_menu_items(per_page=20, page=page)

    if 'error' in menu_data:
        flash(f'Error fetching menu items: {menu_data["error"]}', 'error')
        menu_data = []

    return render_template('menu_items.html', menu_items=menu_data, current_page=page)

@app.route('/menu-items/new', methods=['GET', 'POST'])
def new_menu_item():
    if request.method == 'POST':
        title = request.form.get('title')
        url = request.form.get('url')
        menu_order = request.form.get('menu_order', 0, type=int)
        parent = request.form.get('parent', 0, type=int)

        if not title or not url:
            flash('Title and URL are required!', 'error')
            return render_template('new_menu_item.html')

        result = wp_api.create_menu_item(title, url, menu_order, parent)

        if 'error' in result:
            flash(f'Error creating menu item: {result["error"]}', 'error')
            return render_template('new_menu_item.html')
        else:
            flash('Menu item created successfully!', 'success')
            return redirect(url_for('menu_items'))

    return render_template('new_menu_item.html')

# Blocks Routes
@app.route('/blocks')
def blocks():
    page = request.args.get('page', 1, type=int)
    blocks_data = wp_api.get_blocks(per_page=10, page=page)

    if 'error' in blocks_data:
        flash(f'Error fetching blocks: {blocks_data["error"]}', 'error')
        blocks_data = []

    return render_template('blocks.html', blocks=blocks_data, current_page=page)

@app.route('/blocks/new', methods=['GET', 'POST'])
def new_block():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        status = request.form.get('status', 'draft')

        if not title or not content:
            flash('Title and content are required!', 'error')
            return render_template('new_block.html')

        result = wp_api.create_block(title, content, status)

        if 'error' in result:
            flash(f'Error creating block: {result["error"]}', 'error')
            return render_template('new_block.html')
        else:
            flash('Block created successfully!', 'success')
            return redirect(url_for('blocks'))

    return render_template('new_block.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)