import requests
import json

API_URL = "http://localhost:8000"

def test_streaming_query():
    payload = {"query": "How did we handle moisture in 2022?", "top_k": 3}
    try:
        print(f"Sending request to {API_URL}/query...")
        response = requests.post(f"{API_URL}/query", json=payload, stream=True)
        
        if response.status_code == 200:
            print("Successfully connected. Streaming response:")
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    print(f"[{chunk['type'].upper()}]: {chunk['content']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_streaming_query()
