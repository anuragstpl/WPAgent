import os
import requests
from dotenv import load_dotenv

load_dotenv()

# WordPress Configuration
WORDPRESS_BASE_URL = os.getenv('WORDPRESS_BASE_URL', 'https://vibebuilder.studio')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')

def test_wordpress_connection():
    """Test WordPress API connection step by step"""

    print("🔍 Testing WordPress API Connection...")
    print(f"📍 WordPress URL: {WORDPRESS_BASE_URL}")
    print(f"🔑 Bearer Token: {'✅ Present' if BEARER_TOKEN else '❌ Missing'}")
    print("-" * 50)

    # Test 1: Basic site connection
    print("Test 1: Basic site connection...")
    try:
        response = requests.get(f"{WORDPRESS_BASE_URL}/wp-json", timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Site Name: {data.get('name', 'Unknown')}")
            print(f"✅ WordPress Version: {data.get('wp_version', 'Unknown')}")
        else:
            print(f"❌ Failed to connect to WordPress site")
            print(f"Response: {response.text[:200]}")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print()
        return False

    # Test 2: Posts API without authentication
    print("Test 2: Posts API (without auth)...")
    try:
        response = requests.get(f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts", timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            posts = response.json()
            print(f"✅ Found {len(posts)} public posts")
        else:
            print(f"❌ Posts API failed: {response.text[:200]}")
        print()
    except Exception as e:
        print(f"❌ Posts API failed: {str(e)}")
        print()

    # Test 3: Posts API with authentication
    print("Test 3: Posts API (with auth)...")
    try:
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts",
                              headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            posts = response.json()
            print(f"✅ Found {len(posts)} posts (with auth)")
            if posts:
                first_post = posts[0]
                print(f"   Sample post: '{first_post.get('title', {}).get('rendered', 'No title')}'")
        elif response.status_code == 401:
            print("❌ Authentication failed - Invalid bearer token")
        elif response.status_code == 403:
            print("❌ Permission denied - Token doesn't have required permissions")
        else:
            print(f"❌ Error: {response.text[:200]}")
        print()
    except Exception as e:
        print(f"❌ Authenticated request failed: {str(e)}")
        print()

    # Test 4: Create post test (without actually creating)
    print("Test 4: Create post endpoint check...")
    try:
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}',
            'Content-Type': 'application/json'
        }
        # Just check if we can access the endpoint (OPTIONS request)
        response = requests.options(f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/posts",
                                  headers=headers, timeout=10)
        print(f"Options Status Code: {response.status_code}")
        if response.status_code in [200, 204]:
            print("✅ Create post endpoint accessible")
        else:
            print(f"❌ Create post endpoint issue: {response.status_code}")
        print()
    except Exception as e:
        print(f"❌ Create post endpoint test failed: {str(e)}")
        print()

    print("🔍 Connection test completed!")
    return True

if __name__ == "__main__":
    test_wordpress_connection()