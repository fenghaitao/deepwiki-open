#!/bin/bash

# Provider Configuration Setup Script for DeepWiki-Open
# Supports: dashscope, github_copilot

# Function to display usage
show_usage() {
    echo "🚀 DeepWiki-Open Provider Configuration Setup"
    echo ""
    echo "Usage: $0 <provider>"
    echo ""
    echo "Supported providers:"
    echo "  dashscope      - Alibaba Cloud DashScope (Qwen models)"
    echo "  github_copilot - GitHub Copilot (OpenAI models via OAuth2)"
    echo ""
    echo "Examples:"
    echo "  $0 dashscope"
    echo "  $0 github_copilot"
    echo ""
    echo "Environment variables:"
    echo "  DASHSCOPE_API_KEY     - Required for DashScope"
    echo "  (GitHub Copilot uses automatic OAuth2 - no API key needed)"
}

# Function to setup DashScope
setup_dashscope() {
    echo "🚀 Setting up DashScope configuration for DeepWiki-Open..."
    
    # Check if DashScope API key is provided
    if [ -z "$DASHSCOPE_API_KEY" ]; then
        echo "❌ Error: DASHSCOPE_API_KEY environment variable is not set!"
        echo "Please set your DashScope API key:"
        echo "export DASHSCOPE_API_KEY='your_api_key_here'"
        echo ""
        echo "You can get your API key from: https://dashscope.console.aliyun.com/"
        return 1
    fi

    # Apply DashScope configurations
    echo "🔧 Applying DashScope configurations..."
    if [ ! -f "api/config/generator.dashscope.json" ]; then
        echo "❌ Error: api/config/generator.dashscope.json not found!"
        return 1
    fi
    if [ ! -f "api/config/embedder.dashscope.json" ]; then
        echo "❌ Error: api/config/embedder.dashscope.json not found!"
        return 1
    fi

    cp api/config/generator.dashscope.json api/config/generator.json
    cp api/config/embedder.dashscope.json api/config/embedder.json

    echo "✅ DashScope configuration applied successfully!"
    echo ""
    echo "📋 Configuration Summary:"
    echo "- Generator: DashScope with qwen-plus model"
    echo "- Embedder: DashScope with text-embedding-v2 model"
    echo "- Batch size: 25 (DashScope limit)"
    echo "- Chunk size: 350 words with 100 word overlap"
    echo "- API Key: Set via DASHSCOPE_API_KEY environment variable"
}

# Function to setup GitHub Copilot
setup_github_copilot() {
    echo "🚀 Setting up GitHub Copilot configuration for DeepWiki-Open..."
    
    # Apply GitHub Copilot configurations
    echo "🔧 Applying GitHub Copilot configurations..."
    if [ ! -f "api/config/generator.github_copilot.json" ]; then
        echo "❌ Error: api/config/generator.github_copilot.json not found!"
        return 1
    fi
    if [ ! -f "api/config/embedder.github_copilot.json" ]; then
        echo "❌ Error: api/config/embedder.github_copilot.json not found!"
        return 1
    fi

    cp api/config/generator.github_copilot.json api/config/generator.json
    cp api/config/embedder.github_copilot.json api/config/embedder.json

    echo "✅ GitHub Copilot configuration applied successfully!"
    echo ""
    echo "📋 Configuration Summary:"
    echo "- Generator: GitHub Copilot with gpt-4o model (default)"
    echo "- Available chat models: gpt-4o, gpt-4o-mini, o1-preview, o1-mini, claude-3-5-sonnet"
    echo "- Embedder: GitHub Copilot with text-embedding-3-small model"
    echo "- Batch size: 100 (optimized for GitHub Copilot)"
    echo "- Chunk size: 350 words with 100 word overlap"
    echo "- Authentication: Automatic OAuth2 (no API key required)"
    echo ""
    echo "💡 GitHub Copilot uses automatic OAuth2 authentication."
    echo "   No manual API key setup required!"
}

# Function to backup current configurations
backup_configs() {
    echo "📦 Backing up current configurations..."
    
    if [ -f "api/config/generator.json" ]; then
        cp api/config/generator.json "api/config/generator.json.backup.$(date +%Y%m%d_%H%M%S)"
        echo "✅ Backed up generator.json"
    fi

    if [ -f "api/config/embedder.json" ]; then
        cp api/config/embedder.json "api/config/embedder.json.backup.$(date +%Y%m%d_%H%M%S)"
        echo "✅ Backed up embedder.json"
    fi
}

# Function to show post-setup information
show_post_setup() {
    local provider=$1
    echo ""
    echo "🚀 You can now start the application:"
    echo "python api/main.py"
    echo ""
    echo "🔄 To restore previous configuration:"
    echo "ls api/config/*.backup.* | head -2"
    echo ""
    echo "🧪 To test the configuration:"
    echo "python tests/run_tests.py --${provider//_/-}"
    echo ""
    
    if [ "$provider" = "github_copilot" ]; then
        echo "📚 GitHub Copilot specific commands:"
        echo "export DEEPWIKI_EMBEDDER_TYPE=github_copilot  # Use GitHub Copilot embedder"
        echo "python tests/test_github_copilot_all.py        # Run GitHub Copilot tests"
        echo ""
    fi
}

# Main script logic
main() {
    # Check if provider argument is provided
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi

    provider=$1

    # Validate provider
    case $provider in
        dashscope|github_copilot)
            echo "🎯 Selected provider: $provider"
            ;;
        *)
            echo "❌ Error: Unsupported provider '$provider'"
            echo ""
            show_usage
            exit 1
            ;;
    esac

    # Check if we're in the right directory
    if [ ! -d "api/config" ]; then
        echo "❌ Error: api/config directory not found!"
        echo "Please run this script from the DeepWiki-Open root directory."
        exit 1
    fi

    # Backup current configurations
    backup_configs

    # Setup the specified provider
    case $provider in
        dashscope)
            if setup_dashscope; then
                show_post_setup $provider
            else
                echo "❌ DashScope setup failed!"
                exit 1
            fi
            ;;
        github_copilot)
            if setup_github_copilot; then
                show_post_setup $provider
            else
                echo "❌ GitHub Copilot setup failed!"
                exit 1
            fi
            ;;
    esac

    echo "🎉 Setup completed successfully!"
}

# Run main function with all arguments
main "$@"