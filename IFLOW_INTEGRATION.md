# iFlow Provider Integration

This document describes the integration of the iFlow provider into the codebase. iFlow is an Alibaba Cloud service that provides access to various AI models through an OpenAI-compatible API.

## Overview

The iFlow integration includes:

1. **OpenAI Client Configuration** - Configures OpenAIClient to work with iFlow's OpenAI-compatible API
2. **Configuration** - Provider configuration for LLM models  
3. **Environment Setup** - API key management and authentication
4. **Comprehensive Logging** - Detailed logging to track iFlow usage

## Files Added/Modified

### New Files Created

- `api/config/generator.iflow.json` - iFlow-specific generator configuration
- `tests/unit/test_iflow_integration.py` - Integration test script
- `IFLOW_INTEGRATION.md` - This documentation file

### Modified Files

- `api/config.py` - Added IFLOW_API_KEY environment variable handling
- `api/config/generator.json` - Added iFlow provider configuration using OpenAIClient
- `api/main.py` - Added IFLOW_API_KEY to environment variable checks

## Configuration

### Environment Variables

Set the following environment variable to use iFlow:

```bash
export IFLOW_API_KEY="your-iflow-api-key"
```

### Provider Configuration

The iFlow provider is configured in `api/config/generator.json` using OpenAIClient with the following models:

- `iflow/Qwen3-Coder` (default)
- `iflow/qwen-plus`
- `iflow/qwen-turbo`
- `iflow/qwen-max`
- `iflow/qwen-long`

Configuration includes:
- Client Class: OpenAIClient
- Base URL: https://apis.iflow.cn/v1
- API Key Environment Variable: IFLOW_API_KEY
- Temperature: 0.1
- Top-p: 0.8
- Max tokens: 4000

## Usage

### Using iFlow with the API

The iFlow provider can be selected in the web interface or via API calls by specifying `"provider": "iflow"` in your requests.


### Using OpenAI Client for iFlow

```python
from api.openai_client import OpenAIClient
import os

# Set up environment
os.environ["IFLOW_API_KEY"] = "your-api-key"

# Create client configured for iFlow
client = OpenAIClient(
    api_key=os.getenv("IFLOW_API_KEY"),
    base_url="https://apis.iflow.cn/v1"
)

# The client will automatically work with iFlow models through the web interface
```

## Architecture

### Simplified Integration

The iFlow integration uses a simplified approach:

1. **OpenAI Client Configuration** - Reuses existing OpenAIClient with iFlow-specific settings
2. **Configuration-Based** - All iFlow settings are in configuration files, no custom client needed
3. **Comprehensive Logging** - Detailed logging throughout the request pipeline

### Key Components

- **OpenAIClient** - Configured with iFlow base URL and API key
- **Configuration** - Provider settings in JSON files
- **Logging** - Comprehensive logging to track iFlow usage

### Base URL

The iFlow API base URL is `https://apis.iflow.cn/v1`, configured in the provider configuration `base_url` setting.

## Testing

Run the integration test to verify everything is working:

```bash
python tests/unit/test_iflow_integration.py
```

The test script verifies:
1. iFlow configuration validation
2. OpenAI client configured for iFlow
3. Configuration integration

## Advantages of OpenAI Client Approach

Using the OpenAI client configuration provides several benefits:

- **Simplicity** - No custom client implementation needed
- **Maintenance** - Leverages existing, well-tested code
- **Compatibility** - Full OpenAI API compatibility
- **Flexibility** - Easy to add new models or change configuration
- **Logging** - Comprehensive logging throughout the system

## Troubleshooting

### Common Issues

1. **API Key Not Set**
   ```
   ValueError: Environment variable IFLOW_API_KEY must be set
   ```
   Solution: Set the IFLOW_API_KEY environment variable

2. **Configuration Errors**
   ```
   Provider 'iflow' not found in configuration
   ```
   Solution: Ensure the configuration files have been updated properly

3. **Model Not Found**
   ```
   Provider 'iflow' not found in configuration
   ```
   Solution: Ensure the configuration files have been updated properly

### Logging

The iFlow client uses detailed logging with emoji indicators:
- 🔍 Debug information
- ✅ Success messages
- ❌ Error messages
- 😭 Warning messages

Set logging level to DEBUG to see detailed API interactions:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Endpoints

The iFlow service provides these endpoints:
- `/v1/chat/completions` - For LLM text generation
- `/v1/embeddings` - For text embeddings

All endpoints follow OpenAI API specifications.

## Rate Limiting

iFlow may have rate limits. The client includes exponential backoff retry logic for handling:
- API timeout errors
- Rate limit errors
- Internal server errors
- Bad request errors

## Security

- API keys are loaded from environment variables
- No API keys are logged or stored in code
- HTTPS is used for all API communications
- Client objects exclude API keys during serialization