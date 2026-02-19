
import dashscope
from http import HTTPStatus
import os
from dotenv import load_dotenv

load_dotenv()

# Set your API key
dashscope.api_key = os.getenv("QWEN_API_KEY")

print(f"Testing with key: {dashscope.api_key[:10]}...")

try:
    response = dashscope.Generation.call(
        model='qwen-turbo',
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Hello!'}
        ],
        result_format='message',
    )
    
    if response.status_code == HTTPStatus.OK:
        print("✓ Success!")
        print(response.output.choices[0].message.content)
    else:
        print(f"✗ Error: {response.code} - {response.message}")
        
except Exception as e:
    print(f"✗ Exception: {e}")