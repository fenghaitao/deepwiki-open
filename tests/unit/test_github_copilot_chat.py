#!/usr/bin/env python3
"""Unit tests for GitHub Copilot chat model functionality."""

import os
import sys
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_github_copilot_chat_models():
    """Test GitHub Copilot chat model configurations."""
    print("🔧 Testing GitHub Copilot chat model configurations...")
    
    try:
        import json
        with open(project_root / "api" / "config" / "generator.json") as f:
            config = json.load(f)
        
        # Check if github_copilot provider exists
        if 'github_copilot' not in config.get('providers', {}):
            print("❌ github_copilot provider not found in generator.json")
            return False
        
        github_config = config['providers']['github_copilot']
        
        # Check expected models
        expected_models = ['gpt-4o', 'gpt-4o-mini', 'o1-preview', 'o1-mini', 'claude-3-5-sonnet']
        actual_models = list(github_config.get('models', {}).keys())
        
        for model in expected_models:
            if model in actual_models:
                print(f"✅ Model {model} found in configuration")
            else:
                print(f"❌ Model {model} not found in configuration")
                return False
        
        # Check client class
        if github_config.get('client_class') == 'GitHubCopilotClient':
            print("✅ Correct client class configured")
        else:
            print(f"❌ Incorrect client class: {github_config.get('client_class')}")
            return False
        
        # Check default model
        if github_config.get('default_model') == 'gpt-4o':
            print("✅ Correct default model configured")
        else:
            print(f"❌ Incorrect default model: {github_config.get('default_model')}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test chat model configurations: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_streaming_response_handling():
    """Test streaming response handling for chat models."""
    print("\n🔧 Testing chat streaming response handling...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core.types import ModelType
        
        client = GitHubCopilotClient()
        
        # Test streaming API kwargs generation
        api_kwargs = client.convert_inputs_to_api_kwargs(
            input="Tell me about Python programming",
            model_kwargs={
                "model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 200,
                "stream": True
            },
            model_type=ModelType.LLM
        )
        
        # Check streaming is enabled
        if api_kwargs.get("stream") is True:
            print("✅ Streaming correctly enabled in API kwargs")
        else:
            print(f"❌ Streaming not enabled: {api_kwargs.get('stream')}")
            return False
        
        # Check model formatting
        if api_kwargs.get("model") == "github_copilot/gpt-4o":
            print("✅ Model correctly formatted for streaming")
        else:
            print(f"❌ Model incorrectly formatted: {api_kwargs.get('model')}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test streaming response handling: {e}")
        import traceback
        traceback.print_exc()
        return False

@patch('api.github_copilot_client.acompletion')
async def test_async_chat_completion(mock_acompletion):
    """Test asynchronous chat completion."""
    print("\n🔧 Testing async chat completion...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core.types import ModelType
        
        client = GitHubCopilotClient()
        
        # Mock successful async response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Python is a versatile programming language."
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 8
        mock_response.usage.completion_tokens = 15
        mock_response.usage.total_tokens = 23
        
        mock_acompletion.return_value = mock_response
        
        # Prepare API kwargs
        api_kwargs = {
            "model": "github_copilot/gpt-4o",
            "messages": [{"role": "user", "content": "What is Python?"}],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        # Call async method
        response = await client.acall(api_kwargs, ModelType.LLM)
        
        # Verify mock was called
        mock_acompletion.assert_called_once_with(**api_kwargs)
        
        # Verify response
        if response == mock_response:
            print("✅ Async completion returned correct response")
        else:
            print(f"❌ Async completion returned incorrect response: {response}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test async chat completion: {e}")
        import traceback
        traceback.print_exc()
        return False

@patch('api.github_copilot_client.completion')
def test_sync_chat_completion(mock_completion):
    """Test synchronous chat completion."""
    print("\n🔧 Testing sync chat completion...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core.types import ModelType
        
        client = GitHubCopilotClient()
        
        # Mock successful sync response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Machine learning is a subset of AI."
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        
        mock_completion.return_value = mock_response
        
        # Prepare API kwargs
        api_kwargs = {
            "model": "github_copilot/claude-3-5-sonnet",
            "messages": [{"role": "user", "content": "Explain machine learning"}],
            "temperature": 0.5,
            "max_tokens": 150
        }
        
        # Call sync method
        response = client.call(api_kwargs, ModelType.LLM)
        
        # Verify mock was called
        mock_completion.assert_called_once_with(**api_kwargs)
        
        # Verify response
        if response == mock_response:
            print("✅ Sync completion returned correct response")
        else:
            print(f"❌ Sync completion returned incorrect response: {response}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test sync chat completion: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_error_handling():
    """Test error handling in chat completion."""
    print("\n🔧 Testing chat error handling...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        
        client = GitHubCopilotClient()
        
        # Test parsing response with error
        mock_error_response = Mock()
        mock_error_response.choices = []  # Empty choices should trigger error handling
        
        parsed = client.parse_chat_completion(mock_error_response)
        
        if parsed.error is not None:
            print("✅ Error correctly detected in empty response")
        else:
            print("❌ Error not detected in empty response")
            return False
        
        if parsed.data is None:
            print("✅ Data correctly set to None on error")
        else:
            print(f"❌ Data not set to None on error: {parsed.data}")
            return False
        
        # Test parsing response with no message content
        mock_no_content_response = Mock()
        mock_no_content_response.choices = [Mock()]
        mock_no_content_response.choices[0].message = Mock()
        mock_no_content_response.choices[0].message.content = None
        
        parsed_no_content = client.parse_chat_completion(mock_no_content_response)
        
        if parsed_no_content.error is not None:
            print("✅ Error correctly detected in response with no content")
        else:
            print("❌ Error not detected in response with no content")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test chat error handling: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_parameter_validation():
    """Test model parameter validation for different chat models."""
    print("\n🔧 Testing model parameter validation...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core.types import ModelType
        
        client = GitHubCopilotClient()
        
        # Test different models with their parameters
        test_cases = [
            {
                "model": "gpt-4o",
                "params": {"temperature": 0.7, "max_tokens": 1000, "top_p": 0.9}
            },
            {
                "model": "gpt-4o-mini",
                "params": {"temperature": 0.5, "max_tokens": 500}
            },
            {
                "model": "o1-preview",
                "params": {"temperature": 1.0, "max_tokens": 4000}  # o1 models have specific constraints
            },
            {
                "model": "claude-3-5-sonnet",
                "params": {"temperature": 0.8, "max_tokens": 2000, "top_p": 0.95}
            }
        ]
        
        for test_case in test_cases:
            api_kwargs = client.convert_inputs_to_api_kwargs(
                input="Test message",
                model_kwargs={
                    "model": test_case["model"],
                    **test_case["params"]
                },
                model_type=ModelType.LLM
            )
            
            expected_model = f"github_copilot/{test_case['model']}"
            if api_kwargs.get("model") == expected_model:
                print(f"✅ Model {test_case['model']} correctly formatted")
            else:
                print(f"❌ Model {test_case['model']} incorrectly formatted: {api_kwargs.get('model')}")
                return False
            
            # Check that parameters are preserved
            for param, value in test_case["params"].items():
                if api_kwargs.get(param) == value:
                    print(f"✅ Parameter {param} correctly set for {test_case['model']}")
                else:
                    print(f"❌ Parameter {param} incorrectly set for {test_case['model']}: {api_kwargs.get(param)} (expected {value})")
                    return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test model parameter validation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unsupported_model_type():
    """Test handling of unsupported model types."""
    print("\n🔧 Testing unsupported model type handling...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core.types import ModelType
        
        client = GitHubCopilotClient()
        
        # Test with undefined model type
        try:
            api_kwargs = client.convert_inputs_to_api_kwargs(
                input="Test",
                model_kwargs={"model": "gpt-4o"},
                model_type=ModelType.UNDEFINED
            )
            print("❌ Should have raised error for UNDEFINED model type")
            return False
        except ValueError as e:
            if "not supported" in str(e).lower():
                print("✅ Correctly raised error for UNDEFINED model type")
            else:
                print(f"❌ Unexpected error message: {e}")
                return False
        
        # Test call with unsupported model type
        try:
            response = client.call({}, ModelType.UNDEFINED)
            print("❌ Should have raised error for UNDEFINED model type in call")
            return False
        except ValueError as e:
            if "not supported" in str(e).lower():
                print("✅ Correctly raised error for UNDEFINED model type in call")
            else:
                print(f"❌ Unexpected error message in call: {e}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test unsupported model type handling: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_zero_configuration_principle():
    """Test that the client truly requires zero configuration."""
    print("\n🔧 Testing zero configuration principle...")
    
    try:
        from api.github_copilot_client import GitHubCopilotClient
        
        # Test that client can be created without any parameters
        client = GitHubCopilotClient()
        print("✅ Client created without any parameters")
        
        # Test that setup doesn't require environment variables
        # Save current environment state
        env_backup = {}
        github_env_vars = ['GITHUB_TOKEN', 'GITHUB_API_BASE', 'GITHUB_API_KEY']
        
        for var in github_env_vars:
            if var in os.environ:
                env_backup[var] = os.environ[var]
                del os.environ[var]
        
        try:
            # Create client with clean environment
            clean_client = GitHubCopilotClient()
            print("✅ Client created successfully with no GitHub environment variables")
            
            # Test that setup method doesn't fail
            clean_client._setup_litellm()
            print("✅ Setup completed without environment variables")
            
        finally:
            # Restore environment
            for var, value in env_backup.items():
                os.environ[var] = value
        
        return True
    except Exception as e:
        print(f"❌ Failed to test zero configuration principle: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all GitHub Copilot chat model tests."""
    print("🚀 Starting GitHub Copilot Chat Model Unit Tests")
    print("=" * 60)
    
    tests = [
        test_github_copilot_chat_models,
        test_chat_streaming_response_handling,
        test_sync_chat_completion,
        test_chat_error_handling,
        test_model_parameter_validation,
        test_unsupported_model_type,
        test_zero_configuration_principle,
    ]
    
    # Add async test
    async_tests = [
        test_async_chat_completion,
    ]
    
    passed = 0
    total = len(tests) + len(async_tests)
    
    # Run sync tests
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
    
    # Run async tests
    for async_test in async_tests:
        try:
            result = asyncio.run(async_test())
            if result:
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
        print("🎉 All GitHub Copilot chat model tests passed!")
        return True
    else:
        print("💥 Some GitHub Copilot chat model tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)