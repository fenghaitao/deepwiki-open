#!/usr/bin/env python3
"""
Demonstration of JSON flattening for GitHub Copilot responses.

This script shows how the JSON flattening utilities handle various types of
malformed responses that GitHub Copilot models commonly return.
"""

import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from api.json_flatten_utils import (
    flatten_github_copilot_json,
    validate_github_copilot_response,
    repair_github_copilot_streaming_chunk
)

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def demo_case(name, malformed_json, description):
    """Demonstrate a single JSON flattening case."""
    print(f"\n🔧 {name}")
    print(f"Description: {description}")
    print(f"\nOriginal (malformed):")
    print(f"  {repr(malformed_json)}")
    
    try:
        # Try standard JSON parsing first
        json.loads(malformed_json)
        print("✅ Standard JSON parsing: SUCCESS")
    except json.JSONDecodeError as e:
        print(f"❌ Standard JSON parsing: FAILED ({e})")
        
        # Try our flattening logic
        try:
            result = flatten_github_copilot_json(malformed_json)
            print("✅ Flattened JSON parsing: SUCCESS")
            
            # Validate structure
            is_valid = validate_github_copilot_response(result)
            print(f"✅ Response validation: {'PASSED' if is_valid else 'PARTIAL'}")
            
            # Show the result
            print(f"\nFlattened result:")
            print(f"  {json.dumps(result, indent=2)}")
            
            # Extract key content if available
            if "choices" in result and result["choices"]:
                choice = result["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    print(f"\nExtracted content: '{content}'")
                elif "delta" in choice and "content" in choice["delta"]:
                    content = choice["delta"]["content"]
                    print(f"\nExtracted delta content: '{content}'")
            
            if "token" in result:
                print(f"\nExtracted token: '{result['token']}'")
                
        except Exception as e:
            print(f"❌ Flattened JSON parsing: FAILED ({e})")

def main():
    """Run the JSON flattening demonstration."""
    print("🚀 GitHub Copilot JSON Flattening Demonstration")
    print("This demo shows how malformed GitHub Copilot responses are handled.")
    
    # Test cases based on real GitHub Copilot response patterns
    test_cases = [
        (
            "Trailing Comma in Object",
            '{"choices": [{"message": {"content": "Hello world",}}]}',
            "Common issue where GitHub Copilot adds trailing commas"
        ),
        
        (
            "Markdown Code Block Wrapper",
            '```json\n{"token": "ghs_abc123xyz456def789"}\n```',
            "GitHub Copilot sometimes wraps JSON in markdown"
        ),
        
        (
            "Streaming Response Artifact",
            'data: {"choices": [{"delta": {"content": "Hi there!"}}]}',
            "Streaming responses often include 'data:' prefix"
        ),
        
        (
            "Mixed Quote Types",
            '{"model": \'gpt-4o\', "content": "Hello", "temperature": 0.7}',
            "Inconsistent quote usage between single and double quotes"
        ),
        
        (
            "Line Breaks in JSON",
            '''{"choices": [{"message": 
            {"content": "Multi-line
            response"}}]}''',
            "Line breaks that break JSON structure"
        ),
        
        (
            "Multiple Trailing Commas",
            '{"choices": [{"message": {"content": "Hello",},},], "model": "gpt-4o",}',
            "Multiple trailing commas in nested structures"
        ),
        
        (
            "Completely Malformed Text",
            'This is not JSON at all but contains "token": "secret123" somewhere in the text along with other content.',
            "Non-JSON text that contains extractable key-value pairs"
        ),
        
        (
            "Complex Real-World Example",
            '''```json
            data: {
                "choices": [
                    {
                        "message": {
                            "content": "The capital of France is Paris.",
                        },
                        "finish_reason": "stop",
                    },
                ],
                "model": 'gpt-4o',
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 8,
                    "total_tokens": 18,
                },
            }
            ```''',
            "Complex example combining multiple malformation types"
        )
    ]
    
    print_section("Individual Test Cases")
    
    # Run each test case
    for name, malformed_json, description in test_cases:
        demo_case(name, malformed_json, description)
    
    print_section("Streaming Chunk Repair Demo")
    
    # Demonstrate streaming chunk repair
    streaming_chunks = [
        'data: {"choices": [{"delta": {"content": "Hello"}}]}',
        'data: {"choices": [{"delta": {"content": " world"}}]}',
        'data: {"choices": [{"delta": {"content": "!"}}]}',
        'data: [DONE]',
        '{"choices": [{"delta": {"content": " How"}}]}',  # Missing data: prefix
        'malformed chunk with "content": "extracted" in it'
    ]
    
    print("\n🌊 Streaming Response Handling:")
    print("Demonstrating repair of individual streaming chunks...")
    
    full_content = ""
    
    for i, chunk in enumerate(streaming_chunks, 1):
        print(f"\nChunk {i}: {repr(chunk)}")
        
        repaired = repair_github_copilot_streaming_chunk(chunk)
        
        if repaired is None:
            print("  → Skipped (DONE marker or empty)")
        elif isinstance(repaired, dict):
            print("  → Successfully repaired")
            
            # Try to extract content
            content = None
            if "choices" in repaired and repaired["choices"]:
                choice = repaired["choices"][0]
                if "delta" in choice and "content" in choice["delta"]:
                    content = choice["delta"]["content"]
                elif "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
            
            if content:
                print(f"  → Content: '{content}'")
                full_content += content
            else:
                print("  → No content extracted")
        else:
            print("  → Repair failed")
    
    if full_content:
        print(f"\n✅ Full reconstructed message: '{full_content}'")
    
    print_section("Summary")
    
    print("""
🎯 Key Benefits of JSON Flattening:

1. ✅ Handles common GitHub Copilot malformations automatically
2. ✅ Maintains compatibility with valid JSON (fast path)
3. ✅ Provides fallback extraction for severely malformed responses
4. ✅ Works with both regular and streaming responses
5. ✅ Validates response structure after repair
6. ✅ Detailed logging for debugging issues

🔧 Integration:

The enhanced GitHubCopilotClient automatically uses these utilities,
so your existing code will work better without any changes!

📚 For more information, see: docs/JSON_FLATTENING_GUIDE.md
    """)
    
    print("\n🎉 Demo completed successfully!")

if __name__ == "__main__":
    main()