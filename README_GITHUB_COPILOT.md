# GitHub Copilot Integration

This document describes how to use GitHub Copilot as a provider in DeepWiki-Open using LiteLLM.

## Overview

GitHub Copilot integration has been added to DeepWiki-Open using LiteLLM in direct mode with **OAuth2 authentication**. This allows you to use GitHub Copilot's models (gpt-4o, gpt-4o-mini, o1-preview, o1-mini) for code analysis and documentation generation without manual token configuration.

## Setup

### 1. Authentication

GitHub Copilot uses **OAuth2 authentication**, which is handled automatically by LiteLLM. No manual token configuration is required for most use cases.

#### Option A: OAuth2 (Recommended)
GitHub Copilot will automatically handle OAuth2 authentication when you make API requests. This is the preferred method.

#### Option B: Personal Access Token (Optional)
If you prefer to use a personal access token, you can set:

```bash
export GITHUB_TOKEN="your_github_token_here"
```

**Requirements for personal access tokens**:
- A GitHub Copilot subscription (individual or business)
- A personal access token with appropriate permissions
- Token must have access to GitHub Copilot features

### 2. Configuration

The GitHub Copilot provider is already configured in `api/config/generator.json`:

```json
{
  "github": {
    "client_class": "GitHubCopilotClient",
    "default_model": "gpt-4o",
    "supportsCustomModel": true,
    "models": {
      "gpt-4o": {
        "temperature": 0.7,
        "top_p": 0.8,
        "max_tokens": 4096
      },
      "gpt-4o-mini": {
        "temperature": 0.7,
        "top_p": 0.8,
        "max_tokens": 4096
      },
      "o1-preview": {
        "temperature": 1.0,
        "max_tokens": 4096
      },
      "o1-mini": {
        "temperature": 1.0,
        "max_tokens": 4096
      }
    }
  }
}
```

## Usage

### API Requests

Use the GitHub Copilot provider by setting `provider: "github"` in your API requests:

```json
{
  "repo_url": "https://github.com/user/repo",
  "messages": [
    {
      "role": "user",
      "content": "Explain this codebase"
    }
  ],
  "provider": "github",
  "model": "gpt-4o"
}
```

### Available Models

- **gpt-4o**: Latest GPT-4 Omni model
- **gpt-4o-mini**: Smaller, faster version of GPT-4 Omni
- **o1-preview**: OpenAI's reasoning model (preview)
- **o1-mini**: Smaller version of the o1 reasoning model

### Frontend Integration

In the web interface, select "GitHub Copilot" as your provider from the model selection dropdown.

## Implementation Details

### LiteLLM Integration

The GitHub Copilot client (`api/github_copilot_client.py`) uses LiteLLM in direct mode:

```python
import litellm
from litellm import completion, acompletion

# For streaming
response = await acompletion(
    model="github/gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    stream=True
)
```

### Features Supported

- ✅ Streaming responses
- ✅ Non-streaming responses
- ✅ Temperature and top_p parameters
- ✅ Custom max_tokens
- ✅ Error handling and fallbacks
- ✅ Token usage tracking
- ❌ Embeddings (not supported by GitHub Copilot)

### Error Handling

The client provides clear error messages for common issues:

- Missing `GITHUB_TOKEN` environment variable
- Invalid or expired GitHub token
- Insufficient Copilot permissions
- Rate limiting
- Model availability issues

## Troubleshooting

### Common Issues

1. **OAuth2 Authentication Issues**
   - GitHub Copilot uses OAuth2 by default - no manual setup required
   - If you see authentication errors, LiteLLM will handle the OAuth2 flow automatically
   - For persistent issues, consider using a personal access token via `GITHUB_TOKEN`

2. **Personal Access Token Issues** (if using Option B)
   - Verify your GitHub token is valid and not expired
   - Ensure the token has appropriate permissions
   - Check that your GitHub account has Copilot access
   - Restart the application after setting the variable

3. **"Model not available"**
   - Some models may not be available in all regions
   - Try using `gpt-4o` or `gpt-4o-mini` as they're most widely available

4. **Rate limiting**
   - GitHub Copilot has usage limits
   - Consider using smaller models or reducing request frequency

### Testing

Test the integration by making an API request:

```bash
curl -X POST "http://localhost:8001/chat/completions/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/microsoft/vscode",
    "messages": [{"role": "user", "content": "What is this repository about?"}],
    "provider": "github",
    "model": "gpt-4o"
  }'
```

This will test:
- OAuth2 authentication flow
- Model availability
- Streaming responses
- Error handling

## Security Considerations

### OAuth2 (Default)
- OAuth2 authentication is handled securely by LiteLLM
- No manual token storage required
- Automatic token refresh and management
- Follows GitHub's security best practices

### Personal Access Tokens (Optional)
- Store your `GITHUB_TOKEN` securely if using this option
- Use environment variables, not hardcoded values
- Consider using GitHub's fine-grained personal access tokens
- Regularly rotate your tokens
- Monitor usage through GitHub's billing dashboard

## Performance

GitHub Copilot models generally offer:
- Fast response times
- High-quality code understanding
- Good streaming performance
- Competitive pricing through GitHub

Choose models based on your needs:
- `gpt-4o-mini`: Fastest, most cost-effective
- `gpt-4o`: Best balance of speed and capability
- `o1-preview`/`o1-mini`: Best for complex reasoning tasks

## Support

For issues specific to GitHub Copilot integration:
1. Check the application logs for detailed error messages
2. Verify your GitHub Copilot subscription status
3. Test with a simple request first
4. Consult GitHub's Copilot documentation for API limits and requirements