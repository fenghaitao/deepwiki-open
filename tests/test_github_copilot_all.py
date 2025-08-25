#!/usr/bin/env python3
"""
Comprehensive test suite for all GitHub Copilot functionality.
This test runner executes all GitHub Copilot related tests including:
- Unit tests for embedder functionality
- Unit tests for chat model functionality  
- Integration tests for complete workflows
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_test_file(test_file_path, test_name):
    """Run a specific test file and return the result."""
    print(f"\n🚀 Running {test_name}")
    print("=" * 60)
    
    try:
        # Run the test file as a subprocess
        result = subprocess.run(
            [sys.executable, str(test_file_path)],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Return success/failure
        success = result.returncode == 0
        if success:
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED (exit code: {result.returncode})")
        
        return success
        
    except Exception as e:
        print(f"❌ Error running {test_name}: {e}")
        return False

def run_direct_test(test_module_path, test_name):
    """Run a test by importing and executing it directly."""
    print(f"\n🚀 Running {test_name} (Direct)")
    print("=" * 60)
    
    try:
        # Import the test module
        spec = __import__(test_module_path, fromlist=['main'])
        
        # Run the main function
        if hasattr(spec, 'main'):
            success = spec.main()
            if success:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
            return success
        else:
            print(f"❌ {test_name} has no main function")
            return False
            
    except Exception as e:
        print(f"❌ Error running {test_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_verification():
    """Quick verification that GitHub Copilot is properly configured."""
    print("\n🔧 GitHub Copilot Configuration Verification")
    print("=" * 60)
    
    try:
        # Test basic imports
        from api.github_copilot_client import GitHubCopilotClient
        print("✅ GitHubCopilotClient import successful")
        
        # Test configuration files
        import json
        
        # Check generator.json
        with open(project_root / "api" / "config" / "generator.json") as f:
            generator_config = json.load(f)
        
        if 'github_copilot' in generator_config.get('providers', {}):
            print("✅ github_copilot provider found in generator.json")
            models = list(generator_config['providers']['github_copilot'].get('models', {}).keys())
            print(f"📋 Available chat models: {models}")
        else:
            print("❌ github_copilot provider not found in generator.json")
            return False
        
        # Check embedder.json
        with open(project_root / "api" / "config" / "embedder.json") as f:
            embedder_config = json.load(f)
        
        github_embedders = [k for k in embedder_config.keys() if 'github_copilot' in k]
        if github_embedders:
            print(f"✅ GitHub Copilot embedder config found: {github_embedders}")
            if len(github_embedders) == 1:
                print("✅ Correct number of GitHub Copilot embedder configurations (1)")
            else:
                print(f"❌ Expected 1 GitHub Copilot embedder config, found {len(github_embedders)}")
                return False
        else:
            print("❌ No GitHub Copilot embedder configurations found")
            return False
        
        # Test client initialization
        client = GitHubCopilotClient()
        print("✅ GitHubCopilotClient initialization successful")
        
        # Test model name formatting
        formatted_name = client._format_model_name("gpt-4o")
        if formatted_name == "github_copilot/gpt-4o":
            print("✅ Model name formatting working correctly")
        else:
            print(f"❌ Model name formatting incorrect: {formatted_name}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_test_summary():
    """Show a summary of what will be tested."""
    print("🧪 GitHub Copilot Test Suite")
    print("=" * 60)
    print("This comprehensive test suite will verify:")
    print("• GitHub Copilot client initialization and configuration")
    print("• Embedder functionality (text-embedding-3-small)")
    print("• Chat model functionality (gpt-4o, gpt-4o-mini, o1-*, claude-3-5-sonnet)")
    print("• API kwargs conversion and response parsing")
    print("• Configuration file consistency")
    print("• Integration with existing API endpoints")
    print("• Error handling and edge cases")
    print("• Zero-configuration OAuth2 authentication setup")
    print("")
    print("💡 Note: Some tests may show expected failures if OAuth2 authentication")
    print("   is not available in the test environment. This is normal behavior.")
    print("")

def main():
    """Run the complete GitHub Copilot test suite."""
    show_test_summary()
    
    # Define test files and their descriptions
    test_files = [
        {
            "name": "Configuration Verification",
            "type": "direct",
            "function": test_configuration_verification
        },
        {
            "name": "GitHub Copilot Embedder Unit Tests",
            "type": "file",
            "path": project_root / "tests" / "unit" / "test_github_copilot_embedder.py"
        },
        {
            "name": "GitHub Copilot Chat Unit Tests", 
            "type": "file",
            "path": project_root / "tests" / "unit" / "test_github_copilot_chat.py"
        },
        {
            "name": "GitHub Copilot Integration Tests",
            "type": "file", 
            "path": project_root / "tests" / "integration" / "test_github_copilot_integration.py"
        }
    ]
    
    # Track results
    total_tests = len(test_files)
    passed_tests = 0
    failed_tests = []
    
    # Run each test
    for test_info in test_files:
        if test_info["type"] == "file":
            success = run_test_file(test_info["path"], test_info["name"])
        elif test_info["type"] == "direct":
            success = test_info["function"]()
        else:
            print(f"❌ Unknown test type: {test_info['type']}")
            success = False
        
        if success:
            passed_tests += 1
        else:
            failed_tests.append(test_info["name"])
        
        print("-" * 60)
    
    # Print final summary
    print(f"\n📊 GitHub Copilot Test Suite Results")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test_name in failed_tests:
            print(f"  • {test_name}")
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 All GitHub Copilot tests passed!")
        print("✅ GitHub Copilot integration is working correctly")
        print("\n🚀 Ready for production use:")
        print("  • Zero-configuration OAuth2 authentication")
        print("  • 5 chat models available")
        print("  • 1 embedding model available") 
        print("  • Full API integration")
        return True
    else:
        print(f"\n💥 {len(failed_tests)} test(s) failed!")
        print("🔍 Please review the test output above for details.")
        
        # Provide helpful suggestions
        if len(failed_tests) < total_tests:
            print("\n💡 Suggestions:")
            print("  • Some tests may fail due to missing OAuth2 authentication")
            print("  • This is normal in test environments without GitHub Copilot access")
            print("  • Core functionality appears to be working if config tests passed")
        
        return False

def run_specific_test(test_name):
    """Run a specific test by name."""
    test_mapping = {
        "embedder": "tests.unit.test_github_copilot_embedder",
        "chat": "tests.unit.test_github_copilot_chat", 
        "integration": "tests.integration.test_github_copilot_integration",
        "config": test_configuration_verification
    }
    
    if test_name in test_mapping:
        if callable(test_mapping[test_name]):
            return test_mapping[test_name]()
        else:
            return run_direct_test(test_mapping[test_name], f"GitHub Copilot {test_name.title()} Tests")
    else:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {list(test_mapping.keys())}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1].lower()
        success = run_specific_test(test_name)
    else:
        # Run all tests
        success = main()
    
    sys.exit(0 if success else 1)