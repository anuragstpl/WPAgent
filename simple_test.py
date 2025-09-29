import os
import requests
from dotenv import load_dotenv

load_dotenv()

# WordPress Configuration
WORDPRESS_BASE_URL = os.getenv('WORDPRESS_BASE_URL', 'https://vibebuilder.studio')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')

def test_wordpress_connection():
    """Test WordPress API connection"""

    print("Testing WordPress API Connection...")
    print(f"WordPress URL: {WORDPRESS_BASE_URL}")
    print(f"Bearer Token: {'Present' if BEARER_TOKEN else 'Missing'}")
    print("-" * 50)

    # Test 1: Basic site connection
    print("Test 1: Basic site connection...")
    try:
        response = requests.get(f"{WORDPRESS_BASE_URL}/wp-json", timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Site Name: {data.get('name', 'Unknown')}")
            print(f"WordPress Version: {data.get('wp_version', 'Unknown')}")
            print("SUCCESS: Basic connection works")
        else:
            print(f"FAILED: Status {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

    print()

    # Test 2: Posts API with authentication
    print("Test 2: Posts API with authentication...")
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
            print(f"SUCCESS: Found {len(posts)} posts")
            if posts:
                first_post = posts[0]
                title = first_post.get('title', {}).get('rendered', 'No title')
                print(f"Sample post: '{title}'")
        elif response.status_code == 401:
            print("ERROR: Authentication failed - Invalid bearer token")
        elif response.status_code == 403:
            print("ERROR: Permission denied - Token doesn't have required permissions")
        else:
            print(f"ERROR: Status {response.status_code}")
            print(f"Response: {response.text[:300]}")

    except Exception as e:
        print(f"ERROR: {str(e)}")

    print()
    print("Connection test completed!")
    return True

if __name__ == "__main__":
    test_wordpress_connection()