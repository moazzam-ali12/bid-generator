import os
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("QWEN_API_KEY")
base_url = os.getenv("QWEN_BASE_URL")
model = os.getenv("QWEN_MODEL")

print(f"Testing with API key: {api_key[:10]}...")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

payload = {
    "model": model,
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
}

try:
    response = httpx.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    response.raise_for_status()
    print("✓ API connection successful!")
    print(response.json())
except httpx.HTTPStatusError as e:
    print(f"✗ Error: {e}")
    print(f"Response: {e.response.text}")