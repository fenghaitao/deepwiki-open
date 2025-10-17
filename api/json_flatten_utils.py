"""
JSON Flattening Utilities for GitHub Copilot Response Handling

This module provides utilities to handle malformed JSON responses from GitHub Copilot models,
which often don't return the expected JSON format. The flattening logic helps parse and
clean these responses to make them usable.
"""

import json
import re
import logging
from typing import Dict, Any, Union, Optional

log = logging.getLogger(__name__)

def flatten_github_copilot_json(response_text: str) -> Dict[str, Any]:
    """
    Flatten and fix malformed JSON responses from GitHub Copilot.
    
    GitHub Copilot models often return responses that are not properly formatted JSON,
    containing issues like:
    - Trailing commas
    - Unescaped quotes
    - Mixed quote types
    - Embedded markdown
    - Streaming artifacts
    - Control characters
    
    Args:
        response_text: Raw response text from GitHub Copilot
        
    Returns:
        Dict containing parsed JSON or error information
        
    Example:
        >>> malformed = '{"choices": [{"message": {"content": "Hello",}}]}'
        >>> result = flatten_github_copilot_json(malformed)
        >>> print(result['choices'][0]['message']['content'])
        "Hello"
    """
    log.info("🔧 Starting GitHub Copilot JSON flattening...")
    
    if not response_text or not isinstance(response_text, str):
        log.warning("Empty or invalid response text")
        return {"error": "Empty response", "raw": str(response_text)}
    
    try:
        # First attempt: try standard JSON parsing
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        log.info(f"Standard JSON parsing failed: {e}")
        log.info("Attempting JSON flattening and repair...")
        
        # Apply flattening fixes
        fixed_text = _apply_flattening_fixes(response_text)
        
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError as e2:
            log.warning(f"Flattened JSON parsing failed: {e2}")
            
            # Last resort: manual extraction
            return _extract_json_manually(response_text)

def _apply_flattening_fixes(text: str) -> str:
    """
    Apply a series of fixes to flatten and clean malformed JSON.
    
    This function addresses common GitHub Copilot JSON formatting issues:
    1. Trailing commas in objects and arrays
    2. Quote escaping issues
    3. Line breaks in strings
    4. Markdown code block artifacts
    5. Streaming response artifacts
    6. Control characters
    """
    log.debug("Applying JSON flattening fixes...")
    
    # Store original for debugging
    original_length = len(text)
    
    # Fix 1: Remove markdown code blocks that GitHub Copilot sometimes includes
    text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*```\s*', '', text, flags=re.IGNORECASE)
    
    # Fix 2: Remove streaming artifacts (common in GitHub Copilot responses)
    text = re.sub(r'^data:\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\ndata:\s*', '\n', text)
    text = re.sub(r'}\s*data:\s*{', '}, {', text)
    
    # Fix 3: Fix trailing commas in objects and arrays
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)
    
    # Fix 4: Fix quote issues that GitHub Copilot sometimes introduces
    # Handle cases where quotes are inconsistent
    text = re.sub(r'"\s*"', '""', text)  # Empty strings
    text = re.sub(r"'\s*'", "''", text)  # Empty single quotes
    
    # Fix 5: Remove line breaks within JSON strings (GitHub Copilot issue)
    # This is tricky - we need to preserve intentional line breaks but fix broken JSON
    text = re.sub(r'"\s*\n\s*"', '""', text)  # Remove line breaks between empty quotes
    text = re.sub(r':\s*\n\s*(["\'])', r': \1', text)  # Fix broken key-value pairs
    
    # Fix 6: Fix nested quote escaping issues
    text = re.sub(r'\\"\s*\\"', '\\"', text)
    
    # Fix 7: Remove control characters that might break JSON parsing
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Fix 8: Fix common GitHub Copilot response patterns
    # Sometimes it returns responses wrapped in extra content
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match and json_match.group(0) != text:
        log.debug("Extracted JSON from wrapped content")
        text = json_match.group(0)
    
    # Fix 9: Handle cases where GitHub Copilot returns array instead of object
    text = text.strip()
    if text.startswith('[') and text.endswith(']'):
        # Wrap array in object if it looks like a response array
        if '"choices"' in text or '"data"' in text:
            text = f'{{"items": {text}}}'
    
    # Fix 10: Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    log.debug(f"Flattening fixes applied: {original_length} -> {len(text)} chars")
    return text

def _extract_json_manually(text: str) -> Dict[str, Any]:
    """
    Manual JSON extraction for severely malformed GitHub Copilot responses.
    
    When all JSON parsing attempts fail, this function tries to extract
    key-value pairs manually using regex patterns.
    """
    log.warning("Attempting manual JSON extraction...")
    
    result = {}
    
    # Common GitHub Copilot response patterns
    patterns = [
        # Extract token (for authentication responses)
        (r'"token":\s*"([^"]+)"', "token"),
        
        # Extract model name
        (r'"model":\s*"([^"]+)"', "model"),
        
        # Extract content from choices
        (r'"content":\s*"([^"]*)"', "content"),
        
        # Extract message content (nested)
        (r'"message":\s*\{\s*"content":\s*"([^"]*)"', "message_content"),
        
        # Extract choices array (simplified)
        (r'"choices":\s*(\[[^\]]*\])', "choices"),
        
        # Extract data array (for embeddings)
        (r'"data":\s*(\[[^\]]*\])', "data"),
        
        # Extract usage information
        (r'"usage":\s*(\{[^}]*\})', "usage"),
        
        # Extract error information
        (r'"error":\s*"([^"]*)"', "error"),
        
        # Extract any other string values
        (r'"([^"]+)":\s*"([^"]*)"', "generic_string"),
    ]
    
    # Apply patterns
    for pattern, key_type in patterns:
        matches = re.findall(pattern, text)
        if matches:
            if key_type == "generic_string":
                # Handle generic key-value pairs
                for match in matches:
                    if len(match) == 2:
                        key, value = match
                        result[key] = value
            elif key_type == "choices" or key_type == "data" or key_type == "usage":
                # Handle JSON objects/arrays
                try:
                    result[key_type] = json.loads(matches[0])
                except:
                    result[key_type] = matches[0]  # Store as string if can't parse
            else:
                # Handle simple values
                result[key_type] = matches[0]
            
            log.debug(f"Extracted {key_type}: {matches[0][:100]}...")
    
    # If we extracted message_content, structure it properly
    if "message_content" in result:
        result["choices"] = [{
            "message": {
                "content": result.pop("message_content")
            }
        }]
    
    # If we got content but no choices, structure it
    elif "content" in result and "choices" not in result:
        result["choices"] = [{
            "message": {
                "content": result.pop("content")
            }
        }]
    
    # If we couldn't extract anything useful, return error
    if not result:
        result = {
            "error": "Could not parse GitHub Copilot response",
            "raw": text[:200] + "..." if len(text) > 200 else text
        }
        log.error("Manual extraction failed")
    else:
        log.info(f"Manual extraction successful: {list(result.keys())}")
    
    return result

def validate_github_copilot_response(response: Dict[str, Any]) -> bool:
    """
    Validate if a GitHub Copilot response has the expected structure.
    
    Args:
        response: Parsed response dictionary
        
    Returns:
        True if response appears valid, False otherwise
    """
    if not isinstance(response, dict):
        return False
    
    # Check for error conditions
    if "error" in response:
        return False
    
    # For chat completions, expect choices
    if "choices" in response:
        choices = response["choices"]
        if not isinstance(choices, list) or len(choices) == 0:
            return False
        
        # Check first choice has message content
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return False
            
        if "message" in first_choice:
            message = first_choice["message"]
            if isinstance(message, dict) and "content" in message:
                return True
    
    # For embeddings, expect data
    if "data" in response:
        data = response["data"]
        if isinstance(data, list) and len(data) > 0:
            return True
    
    # For authentication, expect token
    if "token" in response:
        return True
    
    return False

def repair_github_copilot_streaming_chunk(chunk_text: str) -> Optional[Dict[str, Any]]:
    """
    Repair individual streaming chunks from GitHub Copilot.
    
    GitHub Copilot streaming responses often have malformed individual chunks.
    This function attempts to repair them.
    
    Args:
        chunk_text: Raw chunk text from streaming response
        
    Returns:
        Parsed chunk dictionary or None if unrepairable
    """
    if not chunk_text or chunk_text.strip() == "[DONE]":
        return None
    
    # Remove common streaming prefixes
    chunk_text = re.sub(r'^data:\s*', '', chunk_text.strip())
    
    if not chunk_text:
        return None
    
    try:
        return flatten_github_copilot_json(chunk_text)
    except:
        log.debug(f"Could not repair streaming chunk: {chunk_text[:100]}...")
        return None

# Convenience function for backwards compatibility
def fix_malformed_json(json_text: str) -> Dict[str, Any]:
    """
    Alias for flatten_github_copilot_json for backwards compatibility.
    """
    return flatten_github_copilot_json(json_text)

# Example usage and testing
if __name__ == "__main__":
    # Test with common GitHub Copilot malformed responses
    test_cases = [
        # Trailing comma
        '{"choices": [{"message": {"content": "Hello",}}]}',
        
        # Markdown wrapper
        '```json\n{"token": "abc123"}\n```',
        
        # Streaming artifacts
        'data: {"choices": [{"delta": {"content": "Hi"}}]}',
        
        # Mixed quotes
        '{"model": \'gpt-4o\', "content": "test"}',
        
        # Completely malformed
        'This is not JSON but contains "token": "secret123" somewhere',
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest case {i}: {test_case[:50]}...")
        result = flatten_github_copilot_json(test_case)
        print(f"Result: {result}")
        print(f"Valid: {validate_github_copilot_response(result)}")