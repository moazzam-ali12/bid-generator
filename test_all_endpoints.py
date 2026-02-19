import os
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("QWEN_API_KEY")
print(f"Testing with API key: {api_key[:10]}...\n")

endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

# Try different models to see which ones you have access to
models_to_try = [
    "qwen-turbo",
    "qwen-plus", 
    "qwen-max",
    "qwen-long",
    "qwen1.5-72b-chat",
    "qwen1.5-14b-chat",
    "qwen1.5-7b-chat",
]

for model in models_to_try:
    print(f"Trying model: {model}")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    
    try:
        response = httpx.post(endpoint, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            print(f"✓✓✓ SUCCESS with {model}! ✓✓✓\n")
            print(f"Use this model: QWEN_MODEL={model}\n")
            print(f"Response: {response.json()}\n")
            break
        elif response.status_code == 403:
            print(f"✗ Access denied (need to enable)\n")
        else:
            print(f"✗ Status {response.status_code}: {response.text[:200]}\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")