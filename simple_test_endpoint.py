import requests
import json

def test_chat_endpoint():
    """Test the Flask chat endpoint"""

    url = "http://127.0.0.1:5001/chat"
    data = {
        "message": "show me all posts"
    }

    try:
        print("Testing chat endpoint...")
        response = requests.post(url, json=data, timeout=30)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            try:
                result = response.json()
                print("SUCCESS!")
                print(f"Response preview: {result.get('response', 'No response')[:200]}...")
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
    success = test_chat_endpoint()
    if success:
        print("Chat endpoint is working correctly!")
    else:
        print("Chat endpoint has issues.")