# DashScope Configuration Guide for DeepWiki-Open

This guide will help you configure DeepWiki-Open to use Alibaba Cloud's DashScope AI services.

## Prerequisites

1. **DashScope Account**: Sign up at [DashScope Console](https://dashscope.console.aliyun.com/)
2. **API Key**: Generate an API key from your DashScope dashboard
3. **Optional**: Workspace ID (if you're using DashScope workspaces)

## Quick Setup

### Method 1: Automated Setup (Recommended)

1. **Set your API key**:
   ```bash
   export DASHSCOPE_API_KEY="your_dashscope_api_key_here"
   ```

2. **Run the setup script**:
   ```bash
   ./setup_dashscope.sh
   ```

3. **Start the application**:
   ```bash
   python api/main.py
   ```

### Method 2: Manual Setup

1. **Create environment file**:
   ```bash
   cp .env.dashscope.example .env
   ```

2. **Edit `.env` file** with your credentials:
   ```env
   DASHSCOPE_API_KEY=your_actual_api_key_here
   DASHSCOPE_WORKSPACE_ID=your_workspace_id_here  # Optional
   ```

3. **Update configuration files**:
   ```bash
   cp api/config/generator.dashscope.json api/config/generator.json
   cp api/config/embedder.dashscope.json api/config/embedder.json
   ```

## Available Models

### Text Generation Models
- **qwen-plus**: Recommended for most use cases (default)
- **qwen-turbo**: Faster responses, lower cost
- **deepseek-r1**: Alternative reasoning model

### Embedding Models
- **text-embedding-v1**: Standard embedding model (1536 dimensions)
- **text-embedding-v2**: Enhanced embedding model (if available)

## Configuration Details

### Generator Configuration (`api/config/generator.json`)
```json
{
  "generator": {
    "client_class": "DashscopeClient",
    "model_kwargs": {
      "model": "qwen-plus",
      "temperature": 0.1,
      "top_p": 0.8,
      "max_tokens": 4000,
      "stream": true
    }
  }
}
```

### Embedder Configuration (`api/config/embedder.json`)
```json
{
  "embedder": {
    "client_class": "DashscopeClient",
    "batch_size": 25,
    "model_kwargs": {
      "model": "text-embedding-v1",
      "dimensions": 1536,
      "encoding_format": "float"
    }
  },
  "retriever": {
    "top_k": 20
  },
  "text_splitter": {
    "split_by": "word",
    "chunk_size": 350,
    "chunk_overlap": 100
  }
}
```

## Customization Options

### Adjusting Model Parameters

You can modify the model parameters in the configuration files:

- **temperature**: Controls randomness (0.0-1.0)
- **top_p**: Controls diversity (0.0-1.0)
- **max_tokens**: Maximum response length
- **batch_size**: Number of texts to embed at once (max 25 for DashScope)

### Switching Models

To use a different model, update the `model` field in the configuration:

```json
{
  "generator": {
    "model_kwargs": {
      "model": "qwen-turbo"  // Change this
    }
  }
}
```

## Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DASHSCOPE_API_KEY` | ✅ Yes | Your DashScope API key | - |
| `DASHSCOPE_WORKSPACE_ID` | ❌ No | Workspace ID (if using workspaces) | - |
| `DASHSCOPE_BASE_URL` | ❌ No | Custom API endpoint | `https://dashscope.aliyuncs.com/compatible-mode/v1` |

## Troubleshooting

### Common Issues

1. **API Key Error**:
   ```
   ValueError: Environment variable DASHSCOPE_API_KEY must be set
   ```
   **Solution**: Ensure your API key is set in the environment or `.env` file.

2. **Model Not Found**:
   ```
   Model 'model-name' not found
   ```
   **Solution**: Check if the model name is correct and available in your DashScope account.

3. **Batch Size Error**:
   ```
   Batch size exceeds limit
   ```
   **Solution**: DashScope has a maximum batch size of 25. The configuration automatically handles this.

4. **Workspace Access Error**:
   ```
   Workspace access denied
   ```
   **Solution**: Verify your workspace ID is correct or remove it if not needed.

### Performance Optimization

1. **Embedding Cache**: The system automatically caches embeddings to improve performance
2. **Batch Processing**: Embeddings are processed in batches of 25 (DashScope limit)
3. **Streaming**: Responses are streamed for better user experience

## Testing Your Setup

1. **Test the API connection**:
   ```bash
   python -c "
   import os
   from api.dashscope_client import DashscopeClient
   client = DashscopeClient()
   print('✅ DashScope client initialized successfully')
   "
   ```

2. **Start the application**:
   ```bash
   python api/main.py
   ```

3. **Open the frontend**:
   ```bash
   npm run dev
   ```

4. **Test with a repository**: Navigate to `http://localhost:3000` and try analyzing a GitHub repository.

## Reverting to Previous Configuration

If you need to switch back to your previous configuration:

```bash
# Restore from backup
cp api/config/generator.json.backup api/config/generator.json
cp api/config/embedder.json.backup api/config/embedder.json
```

## Support

- **DashScope Documentation**: https://help.aliyun.com/zh/dashscope/
- **API Reference**: https://dashscope.aliyuncs.com/api-docs/
- **DeepWiki Issues**: https://github.com/your-repo/issues

## Cost Considerations

- **Text Generation**: Charged per token (input + output)
- **Embeddings**: Charged per text processed
- **Batch Processing**: More cost-effective than individual requests
- **Caching**: Reduces repeated embedding costs

Monitor your usage in the DashScope console to manage costs effectively.