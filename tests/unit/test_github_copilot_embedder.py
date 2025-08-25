#!/usr/bin/env python3
"""Unit tests for GitHub Copilot embedder functionality."""

import os
import sys
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_github_copilot_client_import():
    """Test that GitHubCopilotClient can be imported successfully."""
    print("🔧 Testing GitHubCopilotClient import...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        print("✅ GitHubCopilotClient imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import GitHubCopilotClient: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_github_copilot_client_initialization():
    """Test GitHub Copilot client initialization."""
    print("\n🔧 Testing GitHubCopilotClient initialization...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        
        # Test default initialization (zero configuration)
        client = GitHubCopilotClient()
        print("✅ GitHubCopilotClient initialized with zero configuration")
        
        # Test with optional parameters (should be ignored)
        client_with_params = GitHubCopilotClient(
            api_key="test_key",
            base_url="https://test.com"
        )
        print("✅ GitHubCopilotClient initialized with ignored parameters")
        
        return True
    except Exception as e:
        print(f"❌ Failed to initialize GitHubCopilotClient: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_name_formatting():
    """Test model name formatting for GitHub Copilot."""
    print("\n🔧 Testing model name formatting...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        
        client = GitHubCopilotClient()
        
        # Test model name formatting
        test_cases = [
            ("text-embedding-3-small", "github_copilot/text-embedding-3-small"),
            ("gpt-4o", "github_copilot/gpt-4o"),
            ("github_copilot/gpt-4o", "github_copilot/gpt-4o"),  # Already formatted
            ("claude-3-5-sonnet", "github_copilot/claude-3-5-sonnet"),
        ]
        
        for input_model, expected_output in test_cases:
            formatted = client._format_model_name(input_model)
            if formatted == expected_output:
                print(f"✅ {input_model} → {formatted}")
            else:
                print(f"❌ {input_model} → {formatted} (expected {expected_output})")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test model name formatting: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_embedding_api_kwargs_conversion():
    """Test conversion of inputs to API kwargs for embeddings."""
    print("\n🔧 Testing embedding API kwargs conversion...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core.types import ModelType
        
        client = GitHubCopilotClient()
        
        # Test string input
        api_kwargs = client.convert_inputs_to_api_kwargs(
            input="Test embedding text",
            model_kwargs={
                "model": "text-embedding-3-small",
                "encoding_format": "float"
            },
            model_type=ModelType.EMBEDDER
        )
        
        expected_model = "github_copilot/text-embedding-3-small"
        if api_kwargs.get("model") == expected_model:
            print(f"✅ Model correctly formatted: {api_kwargs['model']}")
        else:
            print(f"❌ Model incorrectly formatted: {api_kwargs.get('model')} (expected {expected_model})")
            return False
        
        if api_kwargs.get("input") == "Test embedding text":
            print("✅ Input correctly set")
        else:
            print(f"❌ Input incorrectly set: {api_kwargs.get('input')}")
            return False
        
        if api_kwargs.get("encoding_format") == "float":
            print("✅ Encoding format correctly set")
        else:
            print(f"❌ Encoding format incorrectly set: {api_kwargs.get('encoding_format')}")
            return False
        
        # Test list input
        api_kwargs_list = client.convert_inputs_to_api_kwargs(
            input=["Text 1", "Text 2", "Text 3"],
            model_kwargs={
                "model": "text-embedding-3-large",
                "dimensions": 3072
            },
            model_type=ModelType.EMBEDDER
        )
        
        if api_kwargs_list.get("input") == ["Text 1", "Text 2", "Text 3"]:
            print("✅ List input correctly set")
        else:
            print(f"❌ List input incorrectly set: {api_kwargs_list.get('input')}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test embedding API kwargs conversion: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_api_kwargs_conversion():
    """Test conversion of inputs to API kwargs for chat."""
    print("\n🔧 Testing chat API kwargs conversion...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core.types import ModelType
        
        client = GitHubCopilotClient()
        
        # Test chat input
        api_kwargs = client.convert_inputs_to_api_kwargs(
            input="Hello, how are you?",
            model_kwargs={
                "model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 100,
                "stream": False
            },
            model_type=ModelType.LLM
        )
        
        expected_model = "github_copilot/gpt-4o"
        if api_kwargs.get("model") == expected_model:
            print(f"✅ Chat model correctly formatted: {api_kwargs['model']}")
        else:
            print(f"❌ Chat model incorrectly formatted: {api_kwargs.get('model')} (expected {expected_model})")
            return False
        
        # Check messages format
        messages = api_kwargs.get("messages", [])
        if len(messages) == 1 and messages[0].get("role") == "user" and messages[0].get("content") == "Hello, how are you?":
            print("✅ Messages correctly formatted")
        else:
            print(f"❌ Messages incorrectly formatted: {messages}")
            return False
        
        # Check other parameters
        if api_kwargs.get("temperature") == 0.7:
            print("✅ Temperature correctly set")
        else:
            print(f"❌ Temperature incorrectly set: {api_kwargs.get('temperature')}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test chat API kwargs conversion: {e}")
        import traceback
        traceback.print_exc()
        return False

@patch('api.github_copilot_client.embedding')
def test_embedding_response_parsing(mock_embedding):
    """Test parsing of embedding responses."""
    print("\n🔧 Testing embedding response parsing...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        
        client = GitHubCopilotClient()
        
        # Mock a successful embedding response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5]),
            Mock(embedding=[0.6, 0.7, 0.8, 0.9, 1.0])
        ]
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.total_tokens = 10
        
        # Parse the response
        parsed = client.parse_embedding_response(mock_response)
        
        if parsed.error is None:
            print("✅ No error in parsed response")
        else:
            print(f"❌ Unexpected error in parsed response: {parsed.error}")
            return False
        
        if len(parsed.data) == 2:
            print("✅ Correct number of embeddings")
        else:
            print(f"❌ Incorrect number of embeddings: {len(parsed.data)}")
            return False
        
        # Check if the first embedding data is correct (now raw lists)
        first_embedding_data = parsed.data[0]
        if first_embedding_data == [0.1, 0.2, 0.3, 0.4, 0.5]:
            print("✅ First embedding correctly parsed")
        else:
            print(f"❌ First embedding incorrectly parsed: {first_embedding_data}")
            return False
        
        if parsed.usage and parsed.usage.prompt_tokens == 10:
            print("✅ Usage information correctly parsed")
        else:
            print(f"❌ Usage information incorrectly parsed: {parsed.usage}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test embedding response parsing: {e}")
        import traceback
        traceback.print_exc()
        return False

@patch('api.github_copilot_client.completion')
def test_chat_response_parsing(mock_completion):
    """Test parsing of chat responses."""
    print("\n🔧 Testing chat response parsing...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        
        client = GitHubCopilotClient()
        
        # Mock a successful chat response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Hello! I'm doing well, thank you for asking."
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 12
        mock_response.usage.total_tokens = 17
        
        # Parse the response
        parsed = client.parse_chat_completion(mock_response)
        
        if parsed.error is None:
            print("✅ No error in parsed chat response")
        else:
            print(f"❌ Unexpected error in parsed chat response: {parsed.error}")
            return False
        
        expected_content = "Hello! I'm doing well, thank you for asking."
        if parsed.data == expected_content:
            print("✅ Chat content correctly parsed")
        else:
            print(f"❌ Chat content incorrectly parsed: {parsed.data}")
            return False
        
        if parsed.usage and parsed.usage.total_tokens == 17:
            print("✅ Chat usage information correctly parsed")
        else:
            print(f"❌ Chat usage information incorrectly parsed: {parsed.usage}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test chat response parsing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_live_embedding_with_logging():
    """Test live GitHub Copilot embedding with detailed logging."""
    print("\n🧪 Testing live GitHub Copilot embedding with detailed logging...")
    
    try:
        # Import necessary modules
        import asyncio
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core import Embedder
        from adalflow.core.types import ModelType
        
        async def run_embedding_test():
            # Initialize GitHub Copilot client (this will show initialization logs)
            print("   Initializing GitHub Copilot client...")
            client = GitHubCopilotClient()
            
            # Create embedder
            print("   Creating embedder...")
            embedder = Embedder(
                model_client=client,
                model_kwargs={
                    "model": "text-embedding-3-small",
                    "encoding_format": "float"
                }
            )
            
            # Test single string embedding
            print("   Testing single string embedding...")
            test_text = "GitHub Copilot embedding test: This is a sample text for testing."
            result = await embedder.acall(test_text)
            
            if result.data:
                print(f"   ✅ Single embedding successful! Count: {len(result.data)}")
                # Embeddings are now raw lists
                first_embedding = result.data[0]
                print(f"   First embedding dimensions: {len(first_embedding)}")
                print(f"   First 3 values: {first_embedding[:3]}")
            else:
                print(f"   ❌ Single embedding failed: {result.error}")
                return False
            
            # Test batch embeddings
            print("   Testing batch embeddings...")
            test_texts = [
                "First test text for batch embedding",
                "Second test text for batch embedding",
                "Third test text for batch embedding"
            ]
            batch_result = await embedder.acall(test_texts)
            
            if batch_result.data and len(batch_result.data) == 3:
                print(f"   ✅ Batch embedding successful! Count: {len(batch_result.data)}")
                # Embeddings are now raw lists
                first_embedding = batch_result.data[0]
                print(f"   Each embedding dimensions: {len(first_embedding)}")
            else:
                print(f"   ❌ Batch embedding failed: {batch_result.error if batch_result else 'No result'}")
                return False
                
            print("   ✅ All live embedding tests passed!")
            return True
        
        # Run the async test
        result = asyncio.run(run_embedding_test())
        return result
        
    except Exception as e:
        print(f"❌ Failed to test live embedding: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_integration():
    """Test GitHub Copilot configuration integration."""
    print("\n🔧 Testing configuration integration...")
    
    try:
        # Load configuration files directly to avoid circular imports
        import json
        
        # Load embedder configuration
        embedder_config_path = project_root / "api" / "config" / "embedder.json"
        with open(embedder_config_path) as f:
            embedder_config = json.load(f)
        
        # Check embedder configurations
        github_embedder_configs = [k for k in embedder_config.keys() if 'github_copilot' in k]
        if github_embedder_configs:
            print(f"✅ Found GitHub Copilot embedder configs: {github_embedder_configs}")
        else:
            print("❌ No GitHub Copilot embedder configurations found")
            return False
        
        # Test specific embedder config
        if 'embedder_github_copilot' in embedder_config:
            config = embedder_config['embedder_github_copilot']
            if config.get('client_class') == 'GitHubCopilotClient':
                print("✅ GitHub Copilot embedder config has correct client class")
            else:
                print(f"❌ GitHub Copilot embedder config has incorrect client class: {config.get('client_class')}")
                return False
            
            model_kwargs = config.get('model_kwargs', {})
            if model_kwargs.get('model') == 'text-embedding-3-small':
                print("✅ GitHub Copilot embedder config has correct model")
            else:
                print(f"❌ GitHub Copilot embedder config has incorrect model: {model_kwargs.get('model')}")
                return False
        
        # Only one embedder configuration should exist for GitHub Copilot
        if len(github_embedder_configs) == 1:
            print("✅ Correct number of GitHub Copilot embedder configurations (1)")
        else:
            print(f"❌ Unexpected number of GitHub Copilot embedder configurations: {len(github_embedder_configs)}")
            return False
        
        # Load generator configuration
        generator_config_path = project_root / "api" / "config" / "generator.json"
        with open(generator_config_path) as f:
            generator_config = json.load(f)
        
        # Check if github_copilot provider exists
        if 'github_copilot' in generator_config.get('providers', {}):
            print("✅ GitHub Copilot provider found in generator.json")
            
            github_provider = generator_config['providers']['github_copilot']
            if github_provider.get('client_class') == 'GitHubCopilotClient':
                print("✅ GitHub Copilot generator config has correct client class")
            else:
                print(f"❌ GitHub Copilot generator config has incorrect client class: {github_provider.get('client_class')}")
                return False
        else:
            print("❌ GitHub Copilot provider not found in generator.json")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test configuration integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all GitHub Copilot embedder tests."""
    print("🚀 Starting GitHub Copilot Embedder Unit Tests")
    print("=" * 60)
    
    tests = [
        test_github_copilot_client_import,
        test_github_copilot_client_initialization,
        test_model_name_formatting,
        test_embedding_api_kwargs_conversion,
        test_chat_api_kwargs_conversion,
        test_embedding_response_parsing,
        test_chat_response_parsing,
        test_live_embedding_with_logging,
        test_config_integration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED")
            else:
                print("❌ FAILED")
        except Exception as e:
            print(f"❌ FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
        print("-" * 40)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All GitHub Copilot embedder tests passed!")
        return True
    else:
        print("💥 Some GitHub Copilot embedder tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)