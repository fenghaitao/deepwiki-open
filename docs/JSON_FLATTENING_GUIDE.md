# JSON Flattening for GitHub Copilot Responses

## Overview

GitHub Copilot models often return responses that are not properly formatted JSON, causing parsing errors in applications. This guide explains how to use the JSON flattening utilities to handle these malformed responses.

## Problem

GitHub Copilot responses frequently contain formatting issues such as:

- ✗ Trailing commas: `{"content": "Hello",}`
- ✗ Markdown wrappers: ````json\n{"token": "abc"}\n````
- ✗ Streaming artifacts: `data: {"choices": [...]}`
- ✗ Mixed quote types: `{"model": 'gpt-4o', "content": "test"}`
- ✗ Line breaks in JSON: `"content": "Hello\nworld"`
- ✗ Control characters and encoding issues

## Solution

The `json_flatten_utils.py` module provides utilities to automatically detect and fix these issues:

### Basic Usage

```python
from api.json_flatten_utils import flatten_github_copilot_json

# Malformed response from GitHub Copilot
malformed_response = '{"choices": [{"message": {"content": "Hello",}}]}'

# Flatten and fix the response
fixed_response = flatten_github_copilot_json(malformed_response)

# Now you can access the content normally
content = fixed_response["choices"][0]["message"]["content"]
print(content)  # "Hello"
```

### Advanced Usage

```python
from api.json_flatten_utils import (
    flatten_github_copilot_json,
    validate_github_copilot_response,
    repair_github_copilot_streaming_chunk
)

def handle_copilot_response(response_text):
    """Handle GitHub Copilot response with error checking."""
    
    # Flatten the response
    flattened = flatten_github_copilot_json(response_text)
    
    # Validate it's properly structured
    if validate_github_copilot_response(flattened):
        print("✅ Valid response structure")
        return flattened
    else:
        print("⚠️ Response may have issues but attempting to use anyway")
        return flattened

# Example with streaming chunks
def handle_streaming_chunk(chunk_text):
    """Handle individual streaming chunks."""
    
    repaired_chunk = repair_github_copilot_streaming_chunk(chunk_text)
    
    if repaired_chunk:
        # Extract content from chunk
        if "choices" in repaired_chunk:
            choices = repaired_chunk["choices"]
            if choices and "delta" in choices[0]:
                return choices[0]["delta"].get("content", "")
    
    return None
```

## Enhanced GitHub Copilot Client

The `GitHubCopilotClient` has been enhanced to automatically use JSON flattening:

```python
from api.github_copilot_client import GitHubCopilotClient
from adalflow.core import Generator

# Client automatically handles malformed responses
client = GitHubCopilotClient()

generator = Generator(
    model_client=client,
    model_kwargs={
        "model": "gpt-4o",
        "temperature": 0.7
    }
)

# Even if GitHub Copilot returns malformed JSON, this will work
response = generator("What is the capital of France?")
print(response)
```

## Common Malformed Response Patterns

### 1. Trailing Commas

**Problem:**
```json
{
  "choices": [
    {
      "message": {
        "content": "Hello world",
      }
    },
  ]
}
```

**Solution:** Automatically removes trailing commas from objects and arrays.

### 2. Markdown Code Blocks

**Problem:**
```
```json
{"token": "abc123"}
```
```

**Solution:** Strips markdown code block markers.

### 3. Streaming Artifacts

**Problem:**
```
data: {"choices": [{"delta": {"content": "Hi"}}]}
```

**Solution:** Removes `data:` prefixes common in streaming responses.

### 4. Mixed Quote Types

**Problem:**
```json
{"model": 'gpt-4o', "content": "test"}
```

**Solution:** Normalizes quote usage throughout the JSON.

### 5. Completely Malformed

**Problem:**
```
This is not JSON but contains "token": "secret123" somewhere in the text
```

**Solution:** Uses regex patterns to extract key-value pairs manually.

## Testing

Run the JSON flattening tests to verify functionality:

```bash
python tests/unit/test_json_flatten.py
```

Example test cases:

```python
def test_real_world_examples():
    """Test with real GitHub Copilot response patterns."""
    
    # Example 1: Authentication response
    auth_response = '```json\n{"token": "ghs_abc123xyz",}\n```'
    result = flatten_github_copilot_json(auth_response)
    assert result["token"] == "ghs_abc123xyz"
    
    # Example 2: Chat completion with trailing comma
    chat_response = '{"choices": [{"message": {"content": "Hello!",}}]}'
    result = flatten_github_copilot_json(chat_response)
    assert result["choices"][0]["message"]["content"] == "Hello!"
    
    # Example 3: Streaming chunk
    chunk = 'data: {"choices": [{"delta": {"content": "Hi"}}]}'
    result = repair_github_copilot_streaming_chunk(chunk)
    assert result["choices"][0]["delta"]["content"] == "Hi"
```

## Configuration

You can configure the enhanced GitHub Copilot client:

```json
{
  "enhanced_github_copilot": {
    "model_kwargs": {
      "model": "gpt-4o",
      "temperature": 0.7,
      "max_tokens": 4096
    },
    "enable_json_flattening": true,
    "log_malformed_responses": true
  }
}
```

## Logging

The flattening utilities provide detailed logging:

```
🔧 Starting GitHub Copilot JSON flattening...
   Response length: 156 characters
   Response preview: {"choices": [{"message": {"content": "Hello",}}]}
🔧 Applying JSON flattening fixes...
   Applied fix: ,\s*} -> }
✅ Successfully flattened malformed response
```

## Performance

The JSON flattening is designed to be efficient:

- **Fast path:** Valid JSON passes through with minimal overhead
- **Repair path:** Malformed JSON is fixed using optimized regex patterns
- **Fallback path:** Manual extraction only when absolutely necessary

## Best Practices

1. **Always validate responses** after flattening
2. **Log malformed responses** to understand patterns
3. **Test with real GitHub Copilot responses** in your environment
4. **Monitor success rates** of flattening operations
5. **Use streaming chunk repair** for real-time applications

## Troubleshooting

### Common Issues

**Issue:** `JSONDecodeError` still occurs after flattening
**Solution:** Check the raw response text, it might be completely non-JSON

**Issue:** Flattened response has wrong structure
**Solution:** Use `validate_github_copilot_response()` to check structure

**Issue:** Performance is slow
**Solution:** Most responses should use the fast path; check if many responses are malformed

### Debug Mode

Enable detailed logging to troubleshoot:

```python
import logging
logging.getLogger('api.json_flatten_utils').setLevel(logging.DEBUG)
logging.getLogger('api.github_copilot_client').setLevel(logging.DEBUG)
```

## Examples from Real Usage

Here are some real malformed responses we've seen from GitHub Copilot:

```python
# Example 1: Extra commas and markdown
malformed_1 = '''```json
{
  "choices": [
    {
      "message": {
        "content": "The capital of France is Paris.",
      },
    },
  ],
  "model": "gpt-4o",
}
```'''

# Example 2: Streaming format mixed in
malformed_2 = 'data: {"choices": [{"delta": {"content": "Hello"}}]}'

# Example 3: Mixed quotes and line breaks
malformed_3 = '''{
  "token": 'ghs_1234567890abcdef',
  "expires_at": "2024-12-31T23:59:59Z",
}'''

# All of these are handled automatically
for example in [malformed_1, malformed_2, malformed_3]:
    result = flatten_github_copilot_json(example)
    print(f"✅ Successfully parsed: {type(result)}")
```

## Contributing

To add new flattening patterns:

1. Add the pattern to `_apply_flattening_fixes()`
2. Add a test case to `test_json_flatten.py`
3. Update this documentation with the new pattern

## Migration Guide

If you're currently handling GitHub Copilot JSON parsing manually:

**Before:**
```python
try:
    response = json.loads(copilot_response)
except json.JSONDecodeError:
    # Manual error handling
    response = {"error": "Failed to parse response"}
```

**After:**
```python
from api.json_flatten_utils import flatten_github_copilot_json

response = flatten_github_copilot_json(copilot_response)
# Automatically handles malformed JSON
```