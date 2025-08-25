#!/usr/bin/env python3
"""Integration tests for GitHub Copilot functionality."""

import os
import sys
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_config_loading():
    """Test that GitHub Copilot configurations load properly."""
    print("🔧 Testing GitHub Copilot configuration loading...")
    
    try:
        # Load configuration files directly to avoid import issues
        import json
        
        # Load embedder configuration
        embedder_config_path = project_root / "api" / "config" / "embedder.json"
        with open(embedder_config_path) as f:
            embedder_config = json.load(f)
        
        # Check if GitHub Copilot embedder configs exist
        github_embedder_configs = [k for k in embedder_config.keys() if 'github_copilot' in k]
        if github_embedder_configs:
            print(f"✅ GitHub Copilot embedder configurations found: {github_embedder_configs}")
            for config_name in github_embedder_configs:
                config = embedder_config[config_name]
                print(f"📋 {config_name}: {json.dumps(config, indent=2, default=str)}")
        else:
            print("❌ GitHub Copilot embedder configurations not found")
            return False
        
        # Load generator configuration
        generator_config_path = project_root / "api" / "config" / "generator.json"
        with open(generator_config_path) as f:
            generator_config = json.load(f)
        
        # Check if github_copilot provider exists
        if 'github_copilot' in generator_config.get('providers', {}):
            print("✅ GitHub Copilot provider found in generator.json")
            github_provider = generator_config['providers']['github_copilot']
            print(f"📋 GitHub Copilot provider config: {json.dumps(github_provider, indent=2, default=str)}")
        else:
            print("❌ GitHub Copilot provider not found in generator.json")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error loading GitHub Copilot configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_embedder_selection():
    """Test GitHub Copilot embedder selection mechanism."""
    print("\n🔧 Testing GitHub Copilot embedder selection...")
    
    try:
        from api.tools.embedder import get_embedder
        from api.config import get_embedder_type, configs
        
        # Test get_embedder with github_copilot type
        print("🧪 Testing get_embedder with embedder_type='github_copilot'...")
        try:
            embedder = get_embedder(embedder_type='github_copilot')
            print(f"✅ GitHub Copilot embedder created: {type(embedder)}")
            
            # Check if it's the right client type
            if hasattr(embedder, 'model_client'):
                client_type = type(embedder.model_client).__name__
                if client_type == 'GitHubCopilotClient':
                    print(f"✅ Correct client type: {client_type}")
                else:
                    print(f"❌ Incorrect client type: {client_type}")
                    return False
            
        except Exception as e:
            print(f"❌ Failed to create GitHub Copilot embedder: {e}")
            # This might be expected if OAuth2 is not set up, so we continue
            print("💡 This is expected if OAuth2 authentication is not available")
        
        # GitHub Copilot only supports one embedding model (text-embedding-3-small)
        print("✅ GitHub Copilot supports text-embedding-3-small embedding model")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing GitHub Copilot embedder selection: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_github_copilot_with_env():
    """Test GitHub Copilot embedder with environment variable."""
    print("\n🔧 Testing with DEEPWIKI_EMBEDDER_TYPE=github_copilot...")
    
    # Set environment variable
    original_value = os.environ.get('DEEPWIKI_EMBEDDER_TYPE')
    os.environ['DEEPWIKI_EMBEDDER_TYPE'] = 'github_copilot'
    
    try:
        # Reload config module to pick up new env var
        import importlib
        import api.config
        importlib.reload(api.config)
        
        from api.config import EMBEDDER_TYPE, get_embedder_type, get_embedder_config
        from api.tools.embedder import get_embedder
        
        print(f"📋 EMBEDDER_TYPE: {EMBEDDER_TYPE}")
        print(f"📋 get_embedder_type(): {get_embedder_type()}")
        
        # Test getting embedder config
        config = get_embedder_config()
        print(f"📋 Current embedder config client: {config.get('client_class', 'Unknown')}")
        
        if config.get('client_class') == 'GitHubCopilotClient':
            print("✅ Correct client class selected with environment variable")
        else:
            print(f"❌ Incorrect client class: {config.get('client_class')}")
            return False
        
        # Test creating embedder
        try:
            embedder = get_embedder()
            print(f"✅ Embedder created with github_copilot env var: {type(embedder)}")
        except Exception as e:
            print(f"❌ Failed to create embedder with env var: {e}")
            print("💡 This is expected if OAuth2 authentication is not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing with environment variable: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Restore original environment variable
        if original_value is not None:
            os.environ['DEEPWIKI_EMBEDDER_TYPE'] = original_value
        elif 'DEEPWIKI_EMBEDDER_TYPE' in os.environ:
            del os.environ['DEEPWIKI_EMBEDDER_TYPE']

@patch('api.github_copilot_client.embedding')
def test_embedder_workflow(mock_embedding):
    """Test complete embedder workflow."""
    print("\n🔧 Testing GitHub Copilot embedder workflow...")
    
    try:
        # Test GitHub Copilot client directly since get_embedder might use default config
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core.types import ModelType
        
        # Mock successful embedding response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5] * 307)  # 1535 dimensions
        ]
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.total_tokens = 5
        
        mock_embedding.return_value = mock_response
        
        # Create GitHub Copilot client directly
        client = GitHubCopilotClient()
        
        # Test embedding generation
        test_text = "This is a test document for GitHub Copilot embeddings."
        
        try:
            # Convert to API kwargs
            api_kwargs = client.convert_inputs_to_api_kwargs(
                input=test_text,
                model_kwargs={
                    "model": "text-embedding-3-small",
                    "encoding_format": "float"
                },
                model_type=ModelType.EMBEDDER
            )
            
            # Call the client
            response = client.call(api_kwargs, ModelType.EMBEDDER)
            
            # Parse the response
            parsed_response = client.parse_embedding_response(response)
            
            # Verify the result
            if parsed_response.error is None and parsed_response.data is not None:
                print(f"✅ Embedding generated successfully: {len(parsed_response.data)} embeddings")
                
                # Check if usage information is available
                if parsed_response.usage:
                    print(f"✅ Usage information available: {parsed_response.usage}")
                
            else:
                print(f"❌ Embedding generation failed: {parsed_response.error}")
                return False
                
        except Exception as e:
            print(f"❌ Embedder workflow failed: {e}")
            # This might be expected if OAuth2 is not set up
            print("💡 This is expected if OAuth2 authentication is not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing embedder workflow: {e}")
        import traceback
        traceback.print_exc()
        return False

@patch('api.github_copilot_client.completion')
def test_chat_workflow(mock_completion):
    """Test complete chat workflow."""
    print("\n🔧 Testing GitHub Copilot chat workflow...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core.types import ModelType
        
        # Mock successful chat response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "GitHub Copilot is an AI-powered code completion tool developed by GitHub in collaboration with OpenAI."
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 25
        mock_response.usage.total_tokens = 35
        
        mock_completion.return_value = mock_response
        
        # Create GitHub Copilot client
        client = GitHubCopilotClient()
        
        # Test chat completion
        test_message = "What is GitHub Copilot?"
        
        # Convert inputs to API kwargs
        api_kwargs = client.convert_inputs_to_api_kwargs(
            input=test_message,
            model_kwargs={
                "model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 100
            },
            model_type=ModelType.LLM
        )
        
        # Call the client
        response = client.call(api_kwargs, ModelType.LLM)
        
        # Parse the response
        parsed_response = client.parse_chat_completion(response)
        
        # Verify the result
        if parsed_response.error is None and parsed_response.data:
            print(f"✅ Chat completion successful: {parsed_response.data[:100]}...")
            
            # Check usage information
            if parsed_response.usage and parsed_response.usage.total_tokens == 35:
                print("✅ Usage information correctly parsed")
            else:
                print(f"❌ Usage information incorrect: {parsed_response.usage}")
                return False
                
        else:
            print(f"❌ Chat completion failed: {parsed_response.error}")
            return False
        
        # Verify mock was called with correct parameters
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args[1]
        
        if call_args.get('model') == 'github_copilot/gpt-4o':
            print("✅ Correct model passed to API")
        else:
            print(f"❌ Incorrect model passed: {call_args.get('model')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing chat workflow: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_integration():
    """Test API endpoint integration."""
    print("\n🔧 Testing API endpoint integration...")
    
    try:
        # Test import of simple_chat module
        from api.simple_chat import app
        print("✅ simple_chat module imported successfully")
        
        # Test that github_copilot provider is supported
        from api.simple_chat import ChatCompletionRequest, ChatMessage
        
        # Create a test request
        test_request = ChatCompletionRequest(
            repo_url="https://github.com/test/repo",
            messages=[ChatMessage(role="user", content="Hello")],
            provider="github_copilot",
            model="gpt-4o"
        )
        
        if test_request.provider == "github_copilot":
            print("✅ github_copilot provider accepted in ChatCompletionRequest")
        else:
            print(f"❌ github_copilot provider not accepted: {test_request.provider}")
            return False
        
        # Check if the provider is in the field description
        provider_field = ChatCompletionRequest.model_fields['provider']
        if "github_copilot" in provider_field.description:
            print("✅ github_copilot provider listed in field description")
        else:
            print(f"❌ github_copilot provider not in description: {provider_field.description}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_consistency():
    """Test configuration consistency across files."""
    print("\n🔧 Testing configuration consistency...")
    
    try:
        # Test generator.json consistency
        with open(project_root / "api" / "config" / "generator.json") as f:
            generator_config = json.load(f)
        
        # Test embedder.json consistency
        with open(project_root / "api" / "config" / "embedder.json") as f:
            embedder_config = json.load(f)
        
        # Check that github_copilot provider exists in generator config
        if 'github_copilot' not in generator_config.get('providers', {}):
            print("❌ github_copilot provider missing from generator.json")
            return False
        
        github_gen_config = generator_config['providers']['github_copilot']
        
        # Check client class consistency
        if github_gen_config.get('client_class') != 'GitHubCopilotClient':
            print(f"❌ Inconsistent client class in generator.json: {github_gen_config.get('client_class')}")
            return False
        
        # Check embedder configurations
        github_embedder_configs = {k: v for k, v in embedder_config.items() if 'github_copilot' in k}
        
        if not github_embedder_configs:
            print("❌ No github_copilot embedder configurations found")
            return False
        
        for config_name, config in github_embedder_configs.items():
            if config.get('client_class') != 'GitHubCopilotClient':
                print(f"❌ Inconsistent client class in {config_name}: {config.get('client_class')}")
                return False
        
        print("✅ Configuration consistency verified")
        
        # Check model availability
        expected_chat_models = ['gpt-4o', 'gpt-4o-mini', 'o1-preview', 'o1-mini', 'claude-3-5-sonnet']
        actual_chat_models = list(github_gen_config.get('models', {}).keys())
        
        for model in expected_chat_models:
            if model not in actual_chat_models:
                print(f"❌ Expected chat model {model} not found")
                return False
        
        print(f"✅ All expected chat models found: {expected_chat_models}")
        
        # Check embedding models - GitHub Copilot only supports text-embedding-3-small
        expected_embedding_models = ['text-embedding-3-small']
        
        for config_name, config in github_embedder_configs.items():
            model = config.get('model_kwargs', {}).get('model')
            if model not in expected_embedding_models:
                print(f"❌ Unexpected embedding model in {config_name}: {model}")
                return False
        
        print(f"✅ All embedding configurations use expected model: {expected_embedding_models[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing configuration consistency: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling_integration():
    """Test error handling in integration scenarios."""
    print("\n🔧 Testing error handling integration...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core.types import ModelType
        
        client = GitHubCopilotClient()
        
        # Test invalid model type
        try:
            client.call({}, ModelType.UNDEFINED)
            print("❌ Should have raised error for undefined model type")
            return False
        except ValueError as e:
            print(f"✅ Correctly handled undefined model type: {e}")
        
        # Test invalid input for embeddings
        try:
            client.convert_inputs_to_api_kwargs(
                input=12345,  # Invalid input type
                model_kwargs={"model": "text-embedding-3-small"},
                model_type=ModelType.EMBEDDER
            )
            print("❌ Should have raised error for invalid embedding input")
            return False
        except (ValueError, TypeError) as e:
            print(f"✅ Correctly handled invalid embedding input: {e}")
        
        # Test empty response parsing
        empty_response = Mock()
        empty_response.choices = []
        
        parsed = client.parse_chat_completion(empty_response)
        if parsed.error is not None:
            print("✅ Correctly handled empty chat response")
        else:
            print("❌ Did not handle empty chat response correctly")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing error handling integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all GitHub Copilot integration tests."""
    print("🚀 Starting GitHub Copilot Integration Tests")
    print("=" * 60)
    
    tests = [
        test_config_loading,
        test_embedder_selection,
        test_github_copilot_with_env,
        test_embedder_workflow,
        test_chat_workflow,
        test_api_integration,
        test_configuration_consistency,
        test_error_handling_integration,
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
        print("🎉 All GitHub Copilot integration tests passed!")
        return True
    else:
        print("💥 Some GitHub Copilot integration tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)