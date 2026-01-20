import requests
import json

API_URL = "http://localhost:8000"

def test_streaming_query():
    payload = {"query": "What issues have we run into with operating forklifts?", "top_k": 3}
    try:
        print(f"Sending request to {API_URL}/query...")
        response = requests.post(f"{API_URL}/query", json=payload, stream=True)
        
        if response.status_code == 200:
            print("Successfully connected. Streaming response:")
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    if chunk["type"] == "status":
                        print(f"[{chunk['type'].upper()}]: {chunk['content']}")
                    elif chunk["type"] == "answer":
                        print(f"[{chunk['type'].upper()}]: {chunk['content']}", end="", flush=True)
                    elif chunk["type"] == "source":
                        print("\n[SOURCES]:")
                        for source in chunk['content']:
                            print(f" - Score: {source.get('score', 'N/A')} | Metadata: {source.get('metadata', {})}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_streaming_query()
