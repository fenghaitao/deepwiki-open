#!/bin/bash

# DashScope Configuration Setup Script for DeepWiki-Open
echo "🚀 Setting up DashScope configuration for DeepWiki-Open..."

# Check if DashScope API key is provided
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "❌ Error: DASHSCOPE_API_KEY environment variable is not set!"
    echo "Please set your DashScope API key:"
    echo "export DASHSCOPE_API_KEY='your_api_key_here'"
    echo ""
    echo "You can get your API key from: https://dashscope.console.aliyun.com/"
    exit 1
fi

# Backup current configurations
echo "📦 Backing up current configurations..."
if [ -f "api/config/generator.json" ]; then
    cp api/config/generator.json api/config/generator.json.backup
    echo "✅ Backed up generator.json"
fi

if [ -f "api/config/embedder.json" ]; then
    cp api/config/embedder.json api/config/embedder.json.backup
    echo "✅ Backed up embedder.json"
fi

# Apply DashScope configurations
echo "🔧 Applying DashScope configurations..."
cp api/config/generator.dashscope.json api/config/generator.json
cp api/config/embedder.dashscope.json api/config/embedder.json

echo "✅ DashScope configuration applied successfully!"
echo ""
echo "📋 Configuration Summary:"
echo "- Generator: DashScope with qwen-plus model"
echo "- Embedder: DashScope with text-embedding-v1 model"
echo "- Batch size: 25 (DashScope limit)"
echo "- Chunk size: 350 words with 100 word overlap"
echo ""
echo "🚀 You can now start the application:"
echo "python api/main.py"
echo ""
echo "🔄 To restore previous configuration:"
echo "cp api/config/generator.json.backup api/config/generator.json"
echo "cp api/config/embedder.json.backup api/config/embedder.json"