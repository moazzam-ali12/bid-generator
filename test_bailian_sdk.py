from alibabacloud_bailian20231229.client import Client
from alibabacloud_bailian20231229 import models
from alibabacloud_tea_openapi import models as open_api_models
import os
from dotenv import load_dotenv

load_dotenv()

config = open_api_models.Config(
    access_key_id=os.getenv("QWEN_API_KEY"),
)

# For China region
config.endpoint = 'bailian.aliyuncs.com'

try:
    client = Client(config)
    print("✓ SDK client created successfully\n")
    
    # List all available methods
    print("Available methods in client:")
    methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
    for method in methods[:20]:  # Show first 20
        print(f"  - {method}")
    
    print("\n" + "="*60)
    print("Attempting to make a completion call...")
    print("="*60 + "\n")
    
    # Try different possible method names
    possible_methods = [
        'create_text_embeds',
        'create_completion',
        'generate_text',
        'chat_completion',
        'create_chat_completion',
        'invoke',
    ]
    
    for method_name in possible_methods:
        if hasattr(client, method_name):
            print(f"\n✓ Found method: {method_name}")
            print(f"Signature: {getattr(client, method_name).__doc__}")
            break
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()