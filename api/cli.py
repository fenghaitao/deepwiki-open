#!/usr/bin/env python3
"""
CLI tool for DeepWiki repository processing.

Usage:
    Generate embeddings for a GitHub repository:
        python api/cli.py generate https://github.com/owner/repo
    
    Generate embeddings for a local repository:
        python api/cli.py generate /path/to/local/repo
    
    Generate embeddings for a private repository:
        python api/cli.py generate https://github.com/owner/repo --access-token TOKEN
    
    Generate embeddings for a GitLab repository:
        python api/cli.py generate https://gitlab.com/owner/repo --repo-type gitlab
    
    Generate wiki with custom output:
        python api/cli.py generate https://github.com/owner/repo --output ./wiki_output --model-provider google
"""
# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import re
import click
import logging
import sys
import os
from urllib.parse import urlparse
from api.data_pipeline import DatabaseManager, count_tokens, get_file_content
from api.logging_config import setup_logging
from api.rag import RAG
from api.repo_wiki_gen import RepoInfo, WikiGenerationHelper
from adalflow.core.types import ModelType

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def extract_repo_info(repo_path: str) -> tuple[str, str]:
    """Extract owner and repo name from local git repository."""
    try:
        import subprocess
        result = subprocess.run(['git', 'remote', '-v'], cwd=repo_path, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            # Parse first remote URL
            remote_url = result.stdout.split()[1]
            if remote_url.startswith('http://') or remote_url.startswith('https://'):
                parsed = urlparse(remote_url)
                path_parts = parsed.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    owner = path_parts[-2]
                    repo = path_parts[-1].replace('.git', '')
                    return owner, repo
            else:
                # SSH format like git@github.com:owner/repo.git
                if ':' in remote_url and '/' in remote_url:
                    path_part = remote_url.split(':')[1]
                    owner, repo = path_part.replace('.git', '').split('/')
                    return owner, repo
    except Exception:
        pass
    
    # Fallback to directory basename
    basename = os.path.basename(repo_path)
    return basename, basename


def get_repo_structure(repo_path: str) -> tuple[str, str]:
    """
    Get the file tree and README content for a local repository.
    
    Args:
        repo_path: Path to the local repository
        
    Returns:
        Tuple of (file_tree_str, readme_content)
    """
    if not os.path.isdir(repo_path):
        logger.error(f"Directory not found: {repo_path}")
        return "", ""
    
    try:
        logger.info(f"Processing local repository at: {repo_path}")
        file_tree_lines = []
        readme_content = ""
        
        for root, dirs, files in os.walk(repo_path):
            # Exclude hidden dirs/files and virtual envs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__' and d != 'node_modules' and d != '.venv']
            for file in files:
                if file.startswith('.') or file == '__init__.py' or file == '.DS_Store':
                    continue
                rel_dir = os.path.relpath(root, repo_path)
                rel_file = os.path.join(rel_dir, file) if rel_dir != '.' else file
                file_tree_lines.append(rel_file)
                # Find README.md only in top folder (case-insensitive)
                if file.lower() == 'readme.md' and not readme_content and rel_dir == '.':
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            readme_content = f.read()
                    except Exception as e:
                        logger.warning(f"Could not read README.md: {str(e)}")
                        readme_content = ""
        
        file_tree_str = '\n'.join(sorted(file_tree_lines))
        logger.info(f"Generated file tree with {len(file_tree_lines)} files")
        return file_tree_str, readme_content
    except Exception as e:
        logger.error(f"Error processing local repository: {str(e)}")
        return "", ""


@click.group()
def cli():
    """DeepWiki CLI - Repository processing and embedding generation."""
    pass

# .venv/bin/python -m api.cli generate /nfs/site/disks/ssm_lwang85_002/AI/repo-wiki/AdalFlow --repo-type "github" --output /nfs/site/disks/ssm_lwang85_002/AI/repo-wiki/AdalFlow/.deepwiki --model-provider "dashscope" --model "qwen3-coder-plus"

@cli.command()
@click.argument('repo_path')
@click.option(
    '--repo-type',
    type=click.Choice(['github', 'gitlab', 'bitbucket'], case_sensitive=False),
    default='github',
    help='Type of repository (default: github)'
)
def remove(repo_path, repo_type):
    """
    Remove existing database and repository files.
    
    REPO_PATH: Repository URL or local path to remove
    """
    try:
        from adalflow.utils import get_adalflow_default_root_path
        from adalflow.core.db import LocalDB
        import shutil
        import glob
        
        # Parse repository information
        if repo_path.startswith('http://') or repo_path.startswith('https://'):
            parsed = urlparse(repo_path)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                owner = path_parts[-2]
                repo = path_parts[-1].replace('.git', '')
                repo_name = f"{owner}_{repo}"
            else:
                raise ValueError("Invalid repository URL format")
        else:
            # Local path - extract from git remote
            owner, repo = extract_repo_info(repo_path)
            repo_name = f"{owner}_{repo}"
        
        root_path = get_adalflow_default_root_path()
        
        # Remove database using LocalDB operations
        db_file = os.path.join(root_path, "databases", f"{repo_name}.pkl")
        if os.path.exists(db_file):
            try:
                # Load and clear the database
                db = LocalDB.load_state(db_file)
                db.reset_index()  # Clear the database content
                db.save_state(db_file)  # Save empty state
                # Then remove the file
                os.remove(db_file)
                click.echo(click.style(f"✓ Removed database: {db_file}", fg='green'))
            except Exception as e:
                # Fallback to direct file removal
                os.remove(db_file)
                click.echo(click.style(f"✓ Removed database file: {db_file}", fg='green'))
        else:
            click.echo(f"Database file not found: {db_file}")
        
        # Remove all related repositories under ~/.adalflow/repos/
        repos_dir = os.path.join(root_path, "repos")
        if os.path.exists(repos_dir):
            repo_pattern = os.path.join(repos_dir, f"*{repo_name}*")
            matching_repos = glob.glob(repo_pattern)
            for repo_dir in matching_repos:
                if os.path.isdir(repo_dir):
                    shutil.rmtree(repo_dir)
                    click.echo(click.style(f"✓ Removed repository: {repo_dir}", fg='green'))
        
        # Remove wiki cache
        wikicache_dir = os.path.join(root_path, "wikicache")
        if os.path.exists(wikicache_dir):
            cache_pattern = os.path.join(wikicache_dir, f"*{repo_name}*")
            matching_caches = glob.glob(cache_pattern)
            for cache_file in matching_caches:
                if os.path.isfile(cache_file):
                    os.remove(cache_file)
                    click.echo(click.style(f"✓ Removed cache: {cache_file}", fg='green'))
                elif os.path.isdir(cache_file):
                    shutil.rmtree(cache_file)
                    click.echo(click.style(f"✓ Removed cache directory: {cache_file}", fg='green'))
        
        click.echo(click.style("✓ Cleanup completed", fg='green', bold=True))
        
    except Exception as e:
        logger.error(f"Error during removal: {e}", exc_info=True)
        click.echo(click.style(f"✗ Error: {e}", fg='red'), err=True)
        sys.exit(1)


@cli.command()
@click.argument('repo_path')
@click.option(
    '--repo-type',
    type=click.Choice(['github', 'gitlab', 'bitbucket'], case_sensitive=False),
    default='github',
    help='Type of repository (default: github)'
)
@click.option(
    '--access-token',
    help='Access token for private repositories'
)
@click.option(
    '--model-provider',
    default='google',
    help='Model provider for wiki generation (google, openai, openrouter, ollama, etc.)'
)
@click.option(
    '--model',
    default='qwen3-coder-plus',
    help='Model name for wiki generation (default: qwen3-coder-plus)'
)
@click.option(
    '--output',
    type=click.Path(),
    help='Output directory for generated wiki markdown files'
)
@click.option(
    '--exclude-dir',
    multiple=True,
    help='Directory to exclude from processing (can be specified multiple times)'
)
def generate(repo_path, repo_type, access_token, model_provider, model, output, exclude_dir):
    """
    Generate embeddings database and wiki for a repository.
    
    REPO_PATH: Repository URL or local path to process
    """
    try:
        logger.info(f"Starting generation for repository: {repo_path}")
        print(f"======== embedder type: {os.environ.get('DEEPWIKI_EMBEDDER_TYPE')} ========")
        
        # Parse repository information
        repo_url = repo_path
        if repo_path.startswith('http://') or repo_path.startswith('https://'):
            parsed = urlparse(repo_path)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                owner = path_parts[-2]
                repo = path_parts[-1].replace('.git', '')
            else:
                raise ValueError("Invalid repository URL format")
            local_path = None
        else:
            # Local path - extract from git remote
            owner, repo = extract_repo_info(repo_path)
            local_path = repo_path
            repo_url = None
        
        # Create RepoInfo object
        repo_info = RepoInfo(
            owner=owner,
            repo=repo,
            type=repo_type,
            token=access_token,
            local_path=local_path,
            repo_url=repo_url
        )
        
        logger.info(f"Repository: {owner}/{repo} (type: {repo_type})")
        
        # Step 1: Create output directory
        if output:
            output_dir = output
        else:
            output_dir = f"./.deepwiki"
        
        os.makedirs(output_dir, exist_ok=True)
        click.echo(f"Output directory: {output_dir}")
        
        # Step 2: Create RAG instance
        click.echo("Creating RAG instance...")
        request_rag = RAG(provider=model_provider, model=model)
        
        # Step 3: Prepare retriever (this creates/loads the .pkl database)
        click.echo("Preparing retriever and embeddings...")
        
        # Convert exclude_dir tuple to list (or None if empty)
        excluded_dirs = list(exclude_dir) if exclude_dir else None
        
        request_rag.prepare_retriever(
            repo_url_or_path=repo_path,
            type=repo_type,
            access_token=access_token,
            excluded_dirs=excluded_dirs,
            excluded_files=None,
            included_dirs=None,
            included_files=None
        )
        logger.info(f"Retriever prepared for {repo_path}")
        click.echo(click.style("✓ Retriever prepared successfully", fg='green'))
        
        # Step 4: Create WikiGenerationHelper
        click.echo("Creating wiki generation helper...")
        wiki_helper = WikiGenerationHelper(
            repo_info=repo_info,
            language='en',
            provider=model_provider,
            model=model,
            is_comprehensive=True
        )
        
        # Step 5: Generate wiki structure
        click.echo("Generating wiki structure...")
        
        # Get file tree and README from the repository
        if local_path:
            file_tree, readme = get_repo_structure(repo_path)
            if not file_tree:
                click.echo(click.style("⚠ Warning: Could not read repository structure", fg='yellow'))
                file_tree = "Repository file tree will be analyzed by RAG"
                readme = "README content will be analyzed by RAG"
        else:
            # For remote repositories, let RAG analyze the structure
            file_tree = "Repository file tree will be analyzed by RAG"
            readme = "README content will be analyzed by RAG"
        
        # Create the wiki structure prompt using WikiGenerationHelper
        structure_prompt_content = wiki_helper.create_wiki_structure_prompt(file_tree, readme)
        input_too_large = False
        tokens = count_tokens(structure_prompt_content)
        if tokens > 8000:
            logger.info(f"Request size: {tokens} tokens, exceeds recommended token limit")
            click.echo(f"Request size: {tokens} tokens, exceeds recommended token limit")
            input_too_large = True
        
        context_text = ""
        retrieved_docs = None
        if not input_too_large:
            # Query RAG for context (retrieve relevant documents) - aligned with web implementation
            logger.info("Querying RAG for wiki structure")
            try:
                retrieved_docs = request_rag(structure_prompt_content, language='en')  # Use direct call like web
            except Exception as e:
                logger.warning(f"RAG call failed: {e}, proceeding without context")
                retrieved_docs = None
        
            # Format context from retrieved documents
            if (retrieved_docs and
                isinstance(retrieved_docs, list) and
                len(retrieved_docs) > 0 and
                hasattr(retrieved_docs[0], 'documents') and
                retrieved_docs[0].documents):
                documents = retrieved_docs[0].documents
                logger.info(f"Retrieved {len(documents)} documents for structure")
                click.echo(f"  Retrieved {len(documents)} documents:")        
                # Group documents by file path
                docs_by_file = {}
                for doc in documents:
                    file_path = doc.meta_data.get('file_path', 'unknown')
                    if file_path not in docs_by_file:
                        docs_by_file[file_path] = []
                    docs_by_file[file_path].append(doc)

                # Format context text with file path grouping
                context_parts = []
                for file_path, docs in docs_by_file.items():
                    # Add file header with metadata
                    header = f"## File Path: {file_path}\n\n"
                    # Add document content
                    content = "\n\n".join([doc.text for doc in docs])

                    context_parts.append(f"{header}{content}")

                # Join all parts with clear separation
                context_text = "\n\n" + "-" * 10 + "\n\n".join(context_parts)

        # Generate structure using the LLM with context
        from api.config import get_model_config
        model_config = get_model_config(model_provider, model)
        print(f"======== model_config: {model_provider} -- {model_config} ========")
        
        # Create system prompt
        system_prompt = f"""<role>
You are an expert code analyst examining the {repo_type} repository: {repo_url or repo_path} ({repo}).
You provide direct, concise, and accurate information about code repositories.
You NEVER start responses with markdown headers or code fences.
IMPORTANT: You MUST respond in English language.
</role>

<guidelines>
- Answer the user's question directly without ANY preamble or filler phrases
- DO NOT include any rationale, explanation, or extra comments.
- Strictly base answers ONLY on existing code or documents
- DO NOT speculate or invent citations.
- DO NOT start with preambles like "Okay, here's a breakdown" or "Here's an explanation"
- DO NOT start with markdown headers like "## Analysis of..." or any file path references
- DO NOT start with ```markdown code fences
- DO NOT end your response with ``` closing fences
- DO NOT start by repeating or acknowledging the question
- JUST START with the direct answer to the question

<example_of_what_not_to_do>
```markdown
## Analysis of `adalflow/adalflow/datasets/gsm8k.py`

This file contains...
```
</example_of_what_not_to_do>

- Format your response with proper markdown including headings, lists, and code blocks WITHIN your answer
- For code analysis, organize your response with clear sections
- Think step by step and structure your answer logically
- Start with the most relevant information that directly addresses the user's query
- Be precise and technical when discussing code
- Your response language should be in the same language as the user's query
</guidelines>

<style>
- Use concise, direct language
- Prioritize accuracy over verbosity
- When showing code, include line numbers and file paths when relevant
- Use markdown formatting to improve readability
</style>"""
        
        # Create prompt with context
        prompt = f"/no_think {system_prompt}\n\n"
        
        # Only include context if it's not empty
        CONTEXT_START = "<START_OF_CONTEXT>"
        CONTEXT_END = "<END_OF_CONTEXT>"
        if context_text.strip():
            prompt += f"{CONTEXT_START}\n{context_text}\n{CONTEXT_END}\n\n"
        else:
            logger.info("No context available from RAG")
            prompt += "<note>Answering without retrieval augmentation.</note>\n\n"

        prompt += f"<query>\n{structure_prompt_content}\n</query>\n\nAssistant: "
        
        # Call the generator
        from adalflow.core.types import ModelType
        generator_client = model_config["model_client"]()
        
        if model_provider == "ollama":
            prompt += " /no_think"
            model_kwargs = {
                "model": model_config["model_kwargs"]["model"],
                "stream": False,  # CLI doesn't need streaming
                "options": {
                    "temperature": model_config["model_kwargs"]["temperature"],
                    "top_p": model_config["model_kwargs"]["top_p"],
                    "num_ctx": model_config["model_kwargs"]["num_ctx"]
                }
            }
            api_kwargs = generator_client.convert_inputs_to_api_kwargs(
                input=prompt,
                model_kwargs=model_kwargs,
                model_type=ModelType.LLM
            )
        else:
            # For other providers, use messages format
            model_kwargs = model_config["model_kwargs"].copy()
            model_kwargs["model"] = model
            model_kwargs["stream"] = False
            api_kwargs = generator_client.convert_inputs_to_api_kwargs(
                input=prompt,
                model_kwargs=model_kwargs,
                model_type=ModelType.LLM
            )
        
        logger.info("Generating wiki structure with LLM")
        structure_response = generator_client.call(api_kwargs=api_kwargs, model_type=ModelType.LLM)
        
        # Extract response text
        if hasattr(structure_response, 'choices') and len(structure_response.choices) > 0:
            structure_xml = structure_response.choices[0].message.content
        elif hasattr(structure_response, 'content'):
            structure_xml = structure_response.content
        else:
            structure_xml = str(structure_response)
        
        logger.info(f"Received wiki structure XML (length: {len(structure_xml)})")
        
        # Write structure XML to file for debugging/inspection
        structure_xml_file = os.path.join(output_dir, "wiki_structure.xml")
        os.makedirs(os.path.dirname(structure_xml_file), exist_ok=True)
        with open(structure_xml_file, 'w', encoding='utf-8') as f:
            f.write(structure_xml)
        logger.info(f"Written wiki structure XML to: {structure_xml_file}")

        # Parse wiki structure using WikiGenerationHelper
        wiki_structure = wiki_helper.parse_wiki_structure_xml(structure_xml)
        
        if not wiki_structure:
            raise ValueError("Failed to parse wiki structure XML")
                
        click.echo(click.style(f"✓ Wiki structure created with {len(wiki_structure.pages)} pages", fg='green'))
        logger.info(f"Wiki structure: {wiki_structure.title}")
        
        # Step 6: Generate content for each page (aligned with web implementation)
        click.echo(f"\nGenerating content for {len(wiki_structure.pages)} pages...")
        
        for idx, page in enumerate(wiki_structure.pages, 1):
            click.echo(f"\n[{idx}/{len(wiki_structure.pages)}] Generating: {page.title}")
            logger.info(f"Generating page: {page.id} - {page.title}")
            
            # Create page content prompt using WikiGenerationHelper
            content_prompt = wiki_helper.create_page_content_prompt(page)
            input_too_large = False
            tokens = count_tokens(structure_prompt_content)
            if tokens > 8000:
                logger.info(f"Request size: {tokens} tokens, exceeds recommended token limit")
                click.echo(f"Request size: {tokens} tokens, exceeds recommended token limit")
                input_too_large = True
            
            context_text = ""
            retrieved_docs = None
            if not input_too_large:
                # Query RAG for context (aligned with web implementation)
                logger.info(f"Querying RAG for page content: {page.title}")
                try:
                    retrieved_docs = request_rag(content_prompt, language='en')  # Use direct call like web
                except Exception as e:
                    logger.warning(f"RAG call failed for page {page.title}: {e}, proceeding without context")
                    retrieved_docs = None
                
                # Format context from retrieved documents (aligned with web implementation)
                if retrieved_docs and retrieved_docs[0].documents:
                    documents = retrieved_docs[0].documents
                    logger.info(f"Retrieved {len(documents)} documents for page")
                    
                    # Group documents by file path (same as web implementation)
                    docs_by_file = {}
                    for doc in documents:
                        file_path = doc.meta_data.get('file_path', 'unknown')
                        if file_path not in docs_by_file:
                            docs_by_file[file_path] = []
                        docs_by_file[file_path].append(doc)

                    # Format context text with file path grouping (same as web implementation)
                    context_parts = []
                    for file_path, docs in docs_by_file.items():  
                        # Add file header with metadata
                        header = f"## File Path: {file_path}\n\n"
                        # Add document content
                        content = "\n\n".join([doc.text for doc in docs])
                        context_parts.append(f"{header}{content}")

                    # Join all parts with clear separation
                    context_text = "\n\n" + "-" * 10 + "\n\n".join(context_parts)
            
            # Create system prompt (aligned with web implementation)
            system_prompt_for_page = f"""<role>
You are an expert code analyst examining the {repo_type} repository: {repo_url or repo_path} ({repo}).
You provide direct, concise, and accurate information about code repositories.
You NEVER start responses with markdown headers or code fences.
IMPORTANT: You MUST respond in English language.
</role>

<guidelines>
- Answer the user's question directly without ANY preamble or filler phrases
- DO NOT include any rationale, explanation, or extra comments.
- Strictly base answers ONLY on existing code or documents
- DO NOT speculate or invent citations.
- DO NOT start with preambles like "Okay, here's a breakdown" or "Here's an explanation"
- DO NOT start with markdown headers like "## Analysis of..." or any file path references
- DO NOT start with ```markdown code fences
- DO NOT end your response with ``` closing fences
- DO NOT start by repeating or acknowledging the question
- JUST START with the direct answer to the question

<example_of_what_not_to_do>
```markdown
## Analysis of `adalflow/adalflow/datasets/gsm8k.py`

This file contains...
```
</example_of_what_not_to_do>

- Format your response with proper markdown including headings, lists, and code blocks WITHIN your answer
- For code analysis, organize your response with clear sections
- Think step by step and structure your answer logically
- Start with the most relevant information that directly addresses the user's query
- Be precise and technical when discussing code
- Your response language should be in the same language as the user's query
</guidelines>

<style>
- Use concise, direct language
- Prioritize accuracy over verbosity
- When showing code, include line numbers and file paths when relevant
- Use markdown formatting to improve readability
</style>"""
            
            # Create prompt with context (aligned with web implementation)
            CONTEXT_START = "<START_OF_CONTEXT>"
            CONTEXT_END = "<END_OF_CONTEXT>"
            
            prompt = f"/no_think {system_prompt_for_page}\n\n"
            
            # Only include context if it's not empty
            if context_text.strip():
                prompt += f"{CONTEXT_START}\n{context_text}\n{CONTEXT_END}\n\n"
            else:
                logger.info("No context available from RAG")
                prompt += "<note>Answering without retrieval augmentation.</note>\n\n"

            prompt += f"<query>\n{content_prompt}\n</query>\n\nAssistant: "
            
            # Call the generator using the same pattern as web implementation
            if model_provider == "ollama":
                prompt += " /no_think"
                model_kwargs = {
                    "model": model,
                    "stream": False,  # CLI doesn't need streaming
                    "options": {
                        "temperature": model_config["model_kwargs"]["temperature"],
                        "top_p": model_config["model_kwargs"]["top_p"],
                        "num_ctx": model_config["model_kwargs"]["num_ctx"]
                    }
                }
                api_kwargs = generator_client.convert_inputs_to_api_kwargs(
                    input=prompt,
                    model_kwargs=model_kwargs,
                    model_type=ModelType.LLM
                )
            else:
                # For other providers, use messages format
                model_kwargs = model_config["model_kwargs"].copy()
                model_kwargs["model"] = model
                model_kwargs["stream"] = False
                api_kwargs = generator_client.convert_inputs_to_api_kwargs(
                    input=prompt,
                    model_kwargs=model_kwargs,
                    model_type=ModelType.LLM
                )
            
            content_response = generator_client.call(api_kwargs=api_kwargs, model_type=ModelType.LLM)
            
            # Extract response text (aligned with web implementation)
            if hasattr(content_response, 'choices') and len(content_response.choices) > 0:
                page_content = content_response.choices[0].message.content
            elif hasattr(content_response, 'content'):
                page_content = content_response.content
            elif hasattr(content_response, 'data'):
                page_content = content_response.data
            else:
                page_content = str(content_response)
            
            if not page_content:
                logger.warning(f"Failed to generate content for page: {page.title}")
                click.echo(click.style(f"  ⚠ Warning: No content generated", fg='yellow'))
                continue
            
            # Clean up markdown delimiters (aligned with web implementation)
            #page_content = page_content.replace('```markdown', '').replace('```', '')
            page_content = re.sub(r'^```markdown\s*', '', page_content, flags=re.IGNORECASE).rstrip('```').strip()
            
            # Write to markdown file
            # Sanitize filename
            safe_filename = "".join(c for c in page.title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_filename = safe_filename.replace(' ', '_')
            markdown_file = os.path.join(output_dir, f"{safe_filename}.md")
            
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(page_content)
            
            click.echo(click.style(f"  ✓ Written to: {markdown_file}", fg='green'))
            logger.info(f"Written page to: {markdown_file}")
        
        # # Step 7: Create index file
        # index_file = os.path.join(output_dir, "README.md")
        # with open(index_file, 'w', encoding='utf-8') as f:
        #     f.write(f"# {wiki_structure.title}\n\n")
        #     f.write(f"{wiki_structure.description}\n\n")
        #     f.write("## Pages\n\n")
        #     for page in wiki_structure.pages:
        #         safe_filename = "".join(c for c in page.title if c.isalnum() or c in (' ', '-', '_')).strip()
        #         safe_filename = safe_filename.replace(' ', '_')
        #         f.write(f"- [{page.title}](./{safe_filename}.md)\n")
        
        click.echo(click.style(f"\n✓ Wiki generation completed successfully!", fg='green', bold=True))
        click.echo(f"✓ Generated {len(wiki_structure.pages)} wiki pages")
        click.echo(f"✓ Output directory: {output_dir}")
        
    except Exception as e:
        logger.error(f"Error during generation: {e}", exc_info=True)
        click.echo(click.style(f"✗ Error: {e}", fg='red'), err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
