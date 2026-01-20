# DeepWiki CLI Documentation

## Overview

The DeepWiki CLI is a command-line tool for automatically generating comprehensive wiki documentation for code repositories. It uses RAG (Retrieval-Augmented Generation) and large language models to analyze repository structure and create detailed, well-organized wiki pages.

## Installation

Ensure you have the required dependencies installed:

```bash
pip install -r api/requirements.txt
```

Make sure you have a `.env` file with necessary API keys and configuration:

```bash
# Example .env configuration
DEEPWIKI_EMBEDDER_TYPE=your_embedder_type
# Add other required API keys based on your model provider
```

## Usage

### Basic Command Structure

```bash
python api/cli.py generate <REPO_PATH> [OPTIONS]
```

### Arguments

- **REPO_PATH** (required): Repository URL or local path to process
  - Remote repository: `https://github.com/owner/repo`
  - Local repository: `/path/to/local/repo`

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--repo-type` | Choice | `github` | Type of repository: `github`, `gitlab`, or `bitbucket` |
| `--access-token` | String | None | Access token for private repositories |
| `--model-provider` | String | `google` | Model provider for wiki generation (google, openai, openrouter, ollama, dashscope, etc.) |
| `--model` | String | `qwen3-coder-plus` | Model name for wiki generation |
| `--output` | Path | `./.deepwiki` | Output directory for generated wiki markdown files |

## Examples

### 1. Generate Wiki for a Public GitHub Repository

```bash
python api/cli.py generate https://github.com/owner/repo
```

### 2. Generate Wiki for a Local Repository

```bash
python api/cli.py generate /path/to/local/repo
```

### 3. Generate Wiki for a Private Repository

```bash
python api/cli.py generate https://github.com/owner/repo \
  --access-token YOUR_GITHUB_TOKEN
```

### 4. Generate Wiki for a GitLab Repository

```bash
python api/cli.py generate https://gitlab.com/owner/repo \
  --repo-type gitlab \
  --access-token YOUR_GITLAB_TOKEN
```

### 5. Generate Wiki with Custom Model Provider

```bash
python api/cli.py generate https://github.com/owner/repo \
  --model-provider dashscope \
  --model qwen3-coder-plus
```

### 6. Generate Wiki with Custom Output Directory

```bash
python api/cli.py generate https://github.com/owner/repo \
  --output ./wiki_output \
  --model-provider google
```

### 7. Full Example with All Options

```bash
python api/cli.py generate /nfs/site/disks/ssm_lwang85_002/AI/repo-wiki/AdalFlow \
  --repo-type github \
  --output /nfs/site/disks/ssm_lwang85_002/AI/repo-wiki/AdalFlow/.deepwiki \
  --model-provider dashscope \
  --model qwen3-coder-plus
```

## How It Works

### Process Flow

1. **Repository Parsing**: The CLI parses the repository information from the provided URL or local path
2. **Output Directory Setup**: Creates the output directory (default: `./.deepwiki`)
3. **RAG Instance Creation**: Initializes the RAG system with the specified model provider
4. **Retriever Preparation**: Creates or loads embeddings database (.pkl file) for the repository
5. **Wiki Structure Generation**: Analyzes the repository and generates a hierarchical wiki structure
6. **Content Generation**: Generates detailed content for each wiki page using the LLM
7. **Markdown File Creation**: Writes each wiki page as a separate markdown file
8. **Index Creation**: Creates a README.md file with links to all generated pages

### Output Structure

The generated wiki will be organized in the output directory as follows:

```
.deepwiki/
├── README.md                    # Index page with links to all wiki pages
├── Project_Overview.md          # Example generated page
├── Architecture_Design.md       # Example generated page
├── API_Documentation.md         # Example generated page
└── ... (other generated pages)
```

## Supported Repository Types

- **GitHub**: Public and private repositories (requires access token for private)
- **GitLab**: Public and private repositories (requires access token for private)
- **Bitbucket**: Public and private repositories (requires access token for private)
- **Local**: Any local directory containing code

## Supported Model Providers

The CLI supports multiple model providers for wiki generation:

- **Google** (google)
- **OpenAI** (openai)
- **OpenRouter** (openrouter)
- **Ollama** (ollama) - for local models
- **DashScope** (dashscope) - Alibaba Cloud
- **GitHub Copilot** (github_copilot)
- And more...

Configure your preferred provider's API keys in your `.env` file.

## Environment Variables

Key environment variables that may be needed:

```bash
# Embedder configuration
DEEPWIKI_EMBEDDER_TYPE=your_embedder_type

# Model provider API keys (depending on provider used)
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
DASHSCOPE_API_KEY=your_dashscope_key
# ... other provider keys as needed
```

## Error Handling

The CLI includes comprehensive error handling:

- Invalid repository URLs or paths
- Failed API calls to model providers
- Missing or invalid access tokens
- File system errors

All errors are logged with detailed information and displayed to the user with clear error messages.

## Logging

The CLI uses structured logging to track the generation process:

- **INFO**: Progress updates and successful operations
- **WARNING**: Non-critical issues that don't stop execution
- **ERROR**: Critical errors with full stack traces

Logs help debug issues and understand the generation process.

## Tips for Best Results

1. **Use Appropriate Models**: Choose models suited for code analysis (e.g., `qwen3-coder-plus`)
2. **Private Repositories**: Always provide an access token for private repos
3. **Local Repositories**: Ensure the path is absolute and the directory is readable
4. **Output Directory**: Use dedicated directories to avoid conflicts
5. **Model Provider**: Select a provider based on your API access and cost considerations

## Troubleshooting

### Common Issues

**Issue**: "Invalid repository URL format"
- **Solution**: Ensure the URL is complete: `https://github.com/owner/repo`

**Issue**: "Directory not found"
- **Solution**: Verify the local path exists and is accessible

**Issue**: "Authentication failed"
- **Solution**: Check that your access token is valid and has necessary permissions

**Issue**: "Failed to parse wiki structure XML"
- **Solution**: This may indicate an issue with the LLM response; try a different model or provider

## Advanced Usage

### Using with Python Virtual Environment

```bash
# Activate your virtual environment
source .venv/bin/activate

# Run the CLI
python api/cli.py generate /path/to/repo --model-provider dashscope
```

### Running as a Module

```bash
python -m api.cli generate https://github.com/owner/repo
```

## Contributing

When modifying the CLI:

1. Maintain backward compatibility with existing options
2. Add appropriate logging for new features
3. Update this documentation with new examples
4. Follow the existing code structure and error handling patterns

## License

See the main repository LICENSE file for license information.
