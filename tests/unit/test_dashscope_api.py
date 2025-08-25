#!/usr/bin/env python3
"""
Test script to verify DashScope API key and connectivity
"""
import os
import sys
import requests
import json
from datetime import datetime

def test_dashscope_api():
    """Test DashScope API key and basic functionality"""
    
    print("🔍 Testing DashScope API Configuration...")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.environ.get('DASHSCOPE_API_KEY')
    workspace_id = os.environ.get('DASHSCOPE_WORKSPACE_ID')
    base_url = os.environ.get('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    
    print(f"📋 Configuration:")
    print(f"   API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print(f"   Workspace ID: {'✅ Set' if workspace_id else '⚠️ Not set (optional)'}")
    print(f"   Base URL: {base_url}")
    print()
    
    if not api_key:
        print("❌ DASHSCOPE_API_KEY environment variable is not set!")
        print("   Please set it with: export DASHSCOPE_API_KEY='your_api_key_here'")
        return False
    
    # Mask API key for display
    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"🔑 Using API Key: {masked_key}")
    print()
    
    # Test 1: Chat Completion
    print("🧪 Test 1: Chat Completion API")
    print("-" * 30)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    if workspace_id:
        headers['X-DashScope-WorkSpace'] = workspace_id
    
    chat_payload = {
        "model": "qwen-plus",
        "messages": [
            {"role": "user", "content": "Hello! Please respond with 'DashScope API is working correctly.'"}
        ],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=chat_payload,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                print(f"   ✅ Response: {content}")
                print(f"   ✅ Chat completion working!")
            else:
                print(f"   ⚠️ Unexpected response format: {data}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   ❌ Error details: {error_data}")
            except:
                print(f"   ❌ Error text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False
    
    print()
    
    # Test 2: Embeddings API
    print("🧪 Test 2: Embeddings API")
    print("-" * 30)
    
    embedding_payload = {
        "model": "text-embedding-v2",
        "input": ["Hello world", "Test embedding"],
        "encoding_format": "float"
    }
    
    try:
        response = requests.post(
            f"{base_url}/embeddings",
            headers=headers,
            json=embedding_payload,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                embedding_dim = len(data['data'][0]['embedding'])
                print(f"   ✅ Embedding dimension: {embedding_dim}")
                print(f"   ✅ Number of embeddings: {len(data['data'])}")
                print(f"   ✅ Embeddings working!")
            else:
                print(f"   ⚠️ Unexpected response format: {data}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   ❌ Error details: {error_data}")
            except:
                print(f"   ❌ Error text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False
    
    print()
    
    # Test 3: DeepWiki Integration
    print("🧪 Test 3: DeepWiki Integration Test")
    print("-" * 30)
    
    try:
        # Import DeepWiki's DashScope client
        sys.path.append('.')
        from api.dashscope_client import DashscopeClient
        
        client = DashscopeClient()
        print("   ✅ DashScope client initialized")
        
        # Test basic functionality
        from adalflow.core.types import ModelType
        
        # Test chat completion
        api_kwargs = client.convert_inputs_to_api_kwargs(
            input="Hello from DeepWiki!",
            model_kwargs={"model": "qwen-plus", "temperature": 0.1, "max_tokens": 50},
            model_type=ModelType.LLM
        )
        
        result = client.call(api_kwargs=api_kwargs, model_type=ModelType.LLM)
        
        if hasattr(result, 'data') and result.data:
            print(f"   ✅ DeepWiki integration working!")
            print(f"   ✅ Response: {result.data[:100]}...")
        else:
            print(f"   ⚠️ Unexpected result format: {result}")
            
    except ImportError as e:
        print(f"   ⚠️ Could not import DeepWiki modules: {e}")
        print("   ⚠️ Make sure you're running this from the project root")
    except Exception as e:
        print(f"   ❌ DeepWiki integration error: {e}")
        return False
    
    print()
    print("🎉 All tests completed successfully!")
    print("✅ DashScope API key is working correctly")
    return True

if __name__ == "__main__":
    print(f"🚀 DashScope API Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_dashscope_api()
    
    if success:
        print("\n🎯 Next steps:")
        print("   1. Your DashScope API is working correctly")
        print("   2. Try generating a wiki with a simple repository")
        print("   3. Check browser console for any frontend errors")
        sys.exit(0)
    else:
        print("\n❌ DashScope API test failed!")
        print("   Please check your API key and try again")
        sys.exit(1)
