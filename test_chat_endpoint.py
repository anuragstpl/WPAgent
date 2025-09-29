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
        print(f"Response Headers: {response.headers.get('Content-Type')}")

        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ SUCCESS!")
                print(f"Response: {result.get('response', 'No response field')[:200]}...")
                print(f"Session ID: {result.get('session_id', 'No session ID')}")
            except json.JSONDecodeError:
                print("❌ Response is not valid JSON")
                print(f"Raw response: {response.text[:500]}")
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"Response: {response.text[:500]}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure Flask app is running on port 5001.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_chat_endpoint()