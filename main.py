from openai import OpenAI
from app.config import config
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_api_key():
    """Debug chi tiết API key"""
    print("=== DEBUG API KEY ===")

    # Kiểm tra xem config có tồn tại không
    if not hasattr(config, 'OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in config")
        return False

    api_key = config.OPENAI_API_KEY

    print(f"API Key type: {type(api_key)}")
    print(f"API Key length: {len(api_key) if api_key else 0}")
    print(f"API Key first 10 chars: {api_key[:10] if api_key else 'None'}")
    print(f"API Key last 10 chars: {api_key[-10:] if api_key else 'None'}")

    # Kiểm tra định dạng
    if api_key:
        if api_key.startswith('sk-or-'):
            print("✅ API Key format: OpenRouter")
        elif api_key.startswith('sk-'):
            print("✅ API Key format: OpenAI")
        else:
            print("❌ API Key format: Unknown")

    return bool(api_key)


def check_direct_key():
    """Test với API key trực tiếp (tạm thời)"""
    test_key = "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"
 # Thay thế tạm bằng key thật

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=test_key,
    )

    try:
        completion = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1:free",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("✅ Direct key test: SUCCESS")
        print(f"API Key: {test_key}")
        return True
    except Exception as e:
        print(f"❌ Direct key test failed: {e}")
        return False


def check_connection():
    print("=== CHECKING CONNECTION ===")

    # Khởi tạo client
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config.OPENROUTER_API_KEY,
    )

    try:
        print("Testing API call...")
        print(f"API Key: {config.OPENROUTER_API_KEY}")
        completion = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1:free",
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Hello World' only"
                }
            ],
            max_tokens=10
        )
        print("✅ Connection SUCCESS!")
        print(f"Response: {completion.choices[0].message.content}")

    except Exception as e:
        print(f"❌ Connection FAILED: {e}")


if __name__ == '__main__':
    check_direct_key()
    check_connection()