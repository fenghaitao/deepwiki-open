# GitHub Copilot Test Suite Documentation

## Overview

This directory contains comprehensive test suites for GitHub Copilot integration in DeepWiki-Open. The tests verify both chat and embedding functionality with zero-configuration OAuth2 authentication.

## Test Files

### Unit Tests

#### `tests/unit/test_github_copilot_embedder.py`
Tests for GitHub Copilot embedding functionality:
- ✅ Client import and initialization
- ✅ Model name formatting (`github_copilot/model-name`)
- ✅ API kwargs conversion for embeddings
- ✅ Response parsing for embeddings
- ✅ Configuration integration
- ✅ Error handling

**Key Test Cases:**
- `text-embedding-3-small` and `text-embedding-3-large` models
- String and list input handling
- Usage information parsing
- Configuration consistency

#### `tests/unit/test_github_copilot_chat.py`
Tests for GitHub Copilot chat model functionality:
- ✅ Chat model configurations
- ✅ Streaming and non-streaming responses
- ✅ Async and sync completion
- ✅ Model parameter validation
- ✅ Error handling
- ✅ Zero-configuration principle

**Key Test Cases:**
- All 5 chat models: `gpt-4o`, `gpt-4o-mini`, `o1-preview`, `o1-mini`, `claude-3-5-sonnet`
- Temperature, max_tokens, top_p parameter handling
- OAuth2 authentication verification
- Unsupported model type handling

### Integration Tests

#### `tests/integration/test_github_copilot_integration.py`
End-to-end integration tests:
- ✅ Configuration loading and consistency
- ✅ Embedder selection mechanisms
- ✅ Complete workflow testing
- ✅ API endpoint integration
- ✅ Environment variable handling
- ✅ Error handling integration

**Key Test Cases:**
- Configuration file consistency across `generator.json` and `embedder.json`
- Environment variable `DEEPWIKI_EMBEDDER_TYPE=github_copilot`
- API endpoint provider validation
- Complete embedding and chat workflows

### Comprehensive Test Runner

#### `tests/test_github_copilot_all.py`
Master test runner that executes all GitHub Copilot tests:
- Runs all unit and integration tests
- Provides detailed reporting
- Shows configuration verification
- Handles expected OAuth2 failures gracefully

## Running Tests

### Run All GitHub Copilot Tests
```bash
# From project root
python tests/test_github_copilot_all.py

# Or using the main test runner
python tests/run_tests.py --github-copilot
```

### Run Specific Test Categories
```bash
# Configuration verification only
python tests/test_github_copilot_all.py config

# Embedder tests only
python tests/test_github_copilot_all.py embedder

# Chat model tests only
python tests/test_github_copilot_all.py chat

# Integration tests only
python tests/test_github_copilot_all.py integration
```

### Run Individual Test Files
```bash
# Unit tests
python tests/unit/test_github_copilot_embedder.py
python tests/unit/test_github_copilot_chat.py

# Integration tests
python tests/integration/test_github_copilot_integration.py
```

## Test Dependencies

### Required Python Packages
```bash
pip install litellm>=1.74.0
pip install adalflow>=0.1.0
pip install fastapi>=0.95.0
pip install pydantic>=2.0.0
```

### Optional Dependencies
- No API keys required (OAuth2 authentication is automatic)
- No environment variables needed for basic functionality

## Expected Behavior

### ✅ **Normal Test Behavior**
- Configuration tests should always pass
- Model formatting tests should always pass
- Response parsing tests should always pass (with mocked responses)
- API kwargs conversion tests should always pass

### ⚠️ **Expected Failures in Test Environment**
Some tests may show expected failures when OAuth2 authentication is not available:
- Actual API calls to GitHub Copilot
- Live embedding generation
- Live chat completions

This is **normal behavior** in test environments and does not indicate broken functionality.

### 🔍 **Test Environment Setup**
The tests are designed to work in multiple environments:
1. **Development Environment**: All tests pass with mocked responses
2. **CI/CD Environment**: Configuration and unit tests pass, API tests may be skipped
3. **Production Environment**: All tests pass with actual OAuth2 authentication

## Test Coverage

### ✅ **What Is Tested**
- Client initialization and configuration
- Model name formatting and validation
- API request parameter conversion
- Response parsing and error handling
- Configuration file consistency
- Integration with existing API endpoints
- Zero-configuration OAuth2 setup
- All 5 chat models and 1 embedding model

### 🚫 **What Is Not Tested**
- Actual OAuth2 authentication flow (handled by LiteLLM)
- Live API responses from GitHub Copilot (requires authentication)
- Network connectivity and rate limiting
- Billing and usage tracking

## Troubleshooting

### Common Issues

#### `ModuleNotFoundError: No module named 'litellm'`
**Solution:** Install litellm dependency
```bash
pip install litellm>=1.74.0
```

#### `❌ OAuth2 authentication not available`
**Expected behavior** in test environments. The tests are designed to handle this gracefully.

#### `❌ Configuration verification failed`
Check that:
1. `api/config/generator.json` contains `github_copilot` provider
2. `api/config/embedder.json` contains `embedder_github_copilot` configurations
3. `api/github_copilot_client.py` file exists and is importable

#### Test failures with actual API calls
If you have OAuth2 authentication set up and tests are still failing:
1. Verify VS Code GitHub Copilot is working
2. Check LiteLLM version compatibility
3. Review GitHub Copilot service status

## Test Results Interpretation

### 📊 **Success Rate Guidelines**
- **100%**: Perfect - all tests pass including mocked API calls
- **80-99%**: Good - core functionality works, some API tests may fail due to authentication
- **60-79%**: Needs attention - configuration or integration issues
- **<60%**: Problem - major functionality broken

### 🎯 **Key Indicators**
- ✅ Configuration verification passes → Setup is correct
- ✅ Model formatting tests pass → Core client functionality works
- ✅ Response parsing tests pass → Integration layer works
- ❌ Live API tests fail → Expected in test environments without OAuth2

## Contributing

When adding new GitHub Copilot functionality:

1. **Add unit tests** for new methods/features
2. **Update integration tests** for new workflows
3. **Test with mocked responses** to avoid authentication dependencies
4. **Document expected behavior** for test environments
5. **Update this README** with new test descriptions

### Test Naming Convention
- Unit tests: `test_github_copilot_[feature].py`
- Integration tests: `test_github_copilot_integration.py`
- Specific features: `test_[specific_feature]_[aspect].py`

### Mock Response Guidelines
- Use realistic response structures
- Include both success and error scenarios
- Mock usage information when available
- Test edge cases (empty responses, malformed data)

## Security Considerations

### ✅ **Safe Test Practices**
- Tests use mocked responses (no real API calls)
- No hardcoded API keys or tokens
- OAuth2 authentication handled by LiteLLM
- No sensitive data in test files

### 🛡️ **Authentication Testing**
- Tests verify zero-configuration setup
- OAuth2 flow is not tested directly (handled by LiteLLM)
- No credential management in test code
- Environment variables are optional

This comprehensive test suite ensures GitHub Copilot integration is robust, secure, and ready for production use! 🚀