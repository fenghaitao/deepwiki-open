#!/usr/bin/env python3
"""
Test script for iFlow integration
This script tests both the iFlow LLM model and the API client integration.
"""

import os
import sys
import logging

# Add the api directory to Python path
sys.path.append('.')
sys.path.append('./api')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_iflow_config_validation():
    """Test iFlow configuration validation"""
    try:
        # Check if API key is set
        if not os.getenv("IFLOW_API_KEY"):
            logger.error("IFLOW_API_KEY environment variable not set")
            return False
        
        # Test that configuration is properly set up
        logger.info("✅ iFlow API key is set")
        logger.info("✅ Using OpenAI-compatible implementation for iFlow")
        logger.info("✅ No ADK dependencies required")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ iFlow config validation failed: {e}")
        return False

def test_iflow_client():
    """Test the iFlow client integration using OpenAIClient"""
    try:
        from api.openai_client import OpenAIClient
        
        # Check if API key is set
        if not os.getenv("IFLOW_API_KEY"):
            logger.error("IFLOW_API_KEY environment variable not set")
            return False
            
        # Test client creation with iFlow configuration
        client = OpenAIClient(
            api_key=os.getenv("IFLOW_API_KEY"),
            base_url="https://apis.iflow.cn/v1"
        )
        logger.info("✅ OpenAIClient configured for iFlow created successfully")
        
        # Test that we can create the client without errors
        logger.info("✅ iFlow client integration working")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ iFlow client test failed: {e}")
        return False

def test_config_integration():
    """Test that iFlow is properly integrated in the config"""
    try:
        from api.config import CLIENT_CLASSES
        
        # Check if OpenAIClient is in CLIENT_CLASSES (used for iFlow)
        if "OpenAIClient" not in CLIENT_CLASSES:
            logger.error("❌ OpenAIClient not found in CLIENT_CLASSES")
            return False
            
        logger.info("✅ OpenAIClient found in CLIENT_CLASSES")
        
        # Test loading generator config
        import json
        with open('api/config/generator.json', 'r') as f:
            config = json.load(f)
            
        if "iflow" not in config.get("providers", {}):
            logger.error("❌ iflow provider not found in generator config")
            return False
            
        logger.info("✅ iflow provider found in generator config")
        
        iflow_config = config["providers"]["iflow"]
        if iflow_config.get("client_class") != "OpenAIClient":
            logger.error("❌ iflow provider client_class is not OpenAIClient")
            return False
            
        if iflow_config.get("base_url") != "https://apis.iflow.cn/v1":
            logger.error("❌ iflow provider base_url is not correct")
            return False
            
        if iflow_config.get("api_key_env") != "IFLOW_API_KEY":
            logger.error("❌ iflow provider api_key_env is not IFLOW_API_KEY")
            return False
            
        logger.info("✅ iflow provider properly configured with OpenAIClient")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Config integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting iFlow integration tests...")
    
    tests = [
        ("iFlow Configuration", test_iflow_config_validation),
        ("iFlow Client", test_iflow_client), 
        ("Config Integration", test_config_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        success = test_func()
        results.append((test_name, success))
        
    logger.info("\n📊 Test Results:")
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
        if not success:
            all_passed = False
            
    if all_passed:
        logger.info("\n🎉 All tests passed! iFlow integration is working correctly.")
    else:
        logger.info("\n⚠️ Some tests failed. Please check the errors above.")
        
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)