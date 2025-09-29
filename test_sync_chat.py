import requests
import json
import time

def test_chat_endpoint(message, port=5002):
    """Test the Flask chat endpoint"""

    url = f"http://127.0.0.1:{port}/chat"
    data = {"message": message}

    try:
        print(f"Testing: {message}")
        response = requests.post(url, json=data, timeout=60)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            try:
                result = response.json()
                print("SUCCESS!")
                print(f"Response: {result.get('response', 'No response')[:300]}...")
                return True
            except json.JSONDecodeError:
                print("ERROR: Response is not valid JSON")
                print(f"Raw response: {response.text[:200]}")
                return False
        else:
            print(f"ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing synchronous chat app on port 5002...")
    print("=" * 50)

    # Test 1: Get posts
    success1 = test_chat_endpoint("show me all posts")
    print()

    # Test 2: Create post request
    time.sleep(2)  # Small delay between requests
    success2 = test_chat_endpoint("create a new post")
    print()

    if success1 and success2:
        print("Both tests passed! Synchronous chat app is working correctly.")
    else:
        print("Some tests failed. Check the output above.")