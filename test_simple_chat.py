import requests
import json
import time

def test_chat_endpoint(message, port=5003):
    """Test the Flask chat endpoint"""

    url = f"http://127.0.0.1:{port}/chat"
    data = {"message": message}

    try:
        print(f"Testing: {message}")
        response = requests.post(url, json=data, timeout=30)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            try:
                result = response.json()
                print("SUCCESS!")
                print(f"Response: {result.get('response', 'No response')[:200]}...")
                return True
            except json.JSONDecodeError:
                print("ERROR: Response is not valid JSON")
                return False
        else:
            print(f"ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Simple WordPress Chat App on port 5003...")
    print("=" * 50)

    # Test 1: Get posts
    success1 = test_chat_endpoint("show me all posts")
    print()

    # Test 2: Create post - start the process
    time.sleep(1)
    success2 = test_chat_endpoint("create post")
    print()

    if success1 and success2:
        print("Basic tests passed! Simple chat app is working.")
    else:
        print("Some tests failed.")