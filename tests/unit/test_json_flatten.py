#!/usr/bin/env python3
"""
Tests for JSON flattening utilities for GitHub Copilot response handling.
"""
import sys
import os
import unittest
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from api.json_flatten_utils import (
    flatten_github_copilot_json,
    validate_github_copilot_response,
    repair_github_copilot_streaming_chunk,
    _apply_flattening_fixes
)

class TestJSONFlattening(unittest.TestCase):
    """Test cases for JSON flattening functionality."""
    
    def test_valid_json_passthrough(self):
        """Test that valid JSON passes through unchanged."""
        valid_json = '{"choices": [{"message": {"content": "Hello"}}]}'
        result = flatten_github_copilot_json(valid_json)
        
        self.assertIsInstance(result, dict)
        self.assertIn("choices", result)
        self.assertEqual(result["choices"][0]["message"]["content"], "Hello")
    
    def test_trailing_comma_fix(self):
        """Test fixing trailing commas in JSON."""
        malformed_json = '{"choices": [{"message": {"content": "Hello",}}]}'
        result = flatten_github_copilot_json(malformed_json)
        
        self.assertIsInstance(result, dict)
        self.assertIn("choices", result)
        self.assertEqual(result["choices"][0]["message"]["content"], "Hello")
    
    def test_markdown_wrapper_removal(self):
        """Test removing markdown code block wrappers."""
        wrapped_json = '```json\n{"token": "abc123"}\n```'
        result = flatten_github_copilot_json(wrapped_json)
        
        self.assertIsInstance(result, dict)
        self.assertIn("token", result)
        self.assertEqual(result["token"], "abc123")
    
    def test_streaming_artifacts_removal(self):
        """Test removing streaming response artifacts."""
        streaming_json = 'data: {"choices": [{"delta": {"content": "Hi"}}]}'
        result = flatten_github_copilot_json(streaming_json)
        
        self.assertIsInstance(result, dict)
        self.assertIn("choices", result)
        self.assertEqual(result["choices"][0]["delta"]["content"], "Hi")
    
    def test_manual_extraction_fallback(self):
        """Test manual extraction when JSON is completely malformed."""
        malformed_text = 'This is not JSON but contains "token": "secret123" in the text'
        result = flatten_github_copilot_json(malformed_text)
        
        self.assertIsInstance(result, dict)
        self.assertIn("token", result)
        self.assertEqual(result["token"], "secret123")
    
    def test_empty_response_handling(self):
        """Test handling of empty or None responses."""
        result = flatten_github_copilot_json("")
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        
        result = flatten_github_copilot_json(None)
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
    
    def test_response_validation_valid(self):
        """Test validation of valid GitHub Copilot responses."""
        valid_chat_response = {
            "choices": [
                {"message": {"content": "Hello world"}}
            ]
        }
        self.assertTrue(validate_github_copilot_response(valid_chat_response))
        
        valid_embedding_response = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]}
            ]
        }
        self.assertTrue(validate_github_copilot_response(valid_embedding_response))
        
        valid_auth_response = {
            "token": "abc123"
        }
        self.assertTrue(validate_github_copilot_response(valid_auth_response))
    
    def test_response_validation_invalid(self):
        """Test validation of invalid responses."""
        invalid_responses = [
            {"error": "Something went wrong"},
            {"choices": []},
            {"choices": [{"message": {}}]},
            {},
            None,
            "not a dict"
        ]
        
        for invalid_response in invalid_responses:
            self.assertFalse(validate_github_copilot_response(invalid_response))
    
    def test_streaming_chunk_repair(self):
        """Test repairing individual streaming chunks."""
        # Valid chunk
        chunk_text = 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
        result = repair_github_copilot_streaming_chunk(chunk_text)
        
        self.assertIsInstance(result, dict)
        self.assertIn("choices", result)
        
        # DONE marker
        result = repair_github_copilot_streaming_chunk("[DONE]")
        self.assertIsNone(result)
        
        # Empty chunk
        result = repair_github_copilot_streaming_chunk("")
        self.assertIsNone(result)
    
    def test_flattening_fixes_application(self):
        """Test individual flattening fixes."""
        # Test markdown removal
        text_with_markdown = '```json\n{"test": "value"}\n```'
        fixed = _apply_flattening_fixes(text_with_markdown)
        self.assertNotIn("```", fixed)
        
        # Test trailing comma removal
        text_with_comma = '{"test": "value",}'
        fixed = _apply_flattening_fixes(text_with_comma)
        self.assertNotIn(",}", fixed)
        
        # Test streaming artifact removal
        text_with_data = 'data: {"test": "value"}'
        fixed = _apply_flattening_fixes(text_with_data)
        self.assertNotIn("data:", fixed)
    
    def test_complex_malformed_response(self):
        """Test handling of complex malformed GitHub Copilot response."""
        complex_malformed = '''```json
        data: {
            "choices": [
                {
                    "message": {
                        "content": "This is a response
                        with line breaks",
                    }
                },
            ],
            "model": 'gpt-4o',
        }
        ```'''
        
        result = flatten_github_copilot_json(complex_malformed)
        
        self.assertIsInstance(result, dict)
        self.assertIn("choices", result)
        # Should handle the mixed content somehow
        self.assertTrue(len(str(result)) > 0)

def run_tests():
    """Run all JSON flattening tests."""
    print("🧪 Running JSON Flattening Tests...")
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestJSONFlattening)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    if result.wasSuccessful():
        print("\n✅ All JSON flattening tests passed!")
        return True
    else:
        print(f"\n❌ {len(result.failures + result.errors)} test(s) failed")
        for test, error in result.failures + result.errors:
            print(f"   Failed: {test}")
            print(f"   Error: {error}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)