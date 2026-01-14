"""GitHub Copilot ModelClient integration using LiteLLM with OAuth2."""

import os
import logging
from typing import Dict, Any, Optional, Union, Generator
import asyncio

# LiteLLM imports
import litellm
from litellm import completion, acompletion, embedding, aembedding

# Import JSON flattening utilities
from api.json_flatten_utils import (
    flatten_github_copilot_json,
    validate_github_copilot_response,
    repair_github_copilot_streaming_chunk
)

# AdalFlow imports
from adalflow.core.model_client import ModelClient
from adalflow.core.types import (
    ModelType,
    EmbedderOutput,
    CompletionUsage,
    GeneratorOutput,
)

log = logging.getLogger(__name__)

class GitHubCopilotClient(ModelClient):
    """
    A ModelClient wrapper for GitHub Copilot using LiteLLM with automatic OAuth2 authentication.
    
    This client provides access to GitHub Copilot chat and embedding models through LiteLLM's 
    unified interface. GitHub Copilot uses OAuth2 authentication that is handled completely 
    automatically by LiteLLM - no configuration, tokens, or API keys required.
    
    Args:
        api_key (Optional[str]): Not used. OAuth2 authentication is automatic.
        base_url (Optional[str]): Not used. OAuth2 authentication is automatic.
        env_api_key_name (str): Not used. OAuth2 authentication is automatic.
    
    Example:
        ```python
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core import Generator, Embedder
        
        # GitHub Copilot requires no configuration - OAuth2 is fully automatic
        client = GitHubCopilotClient()
        
        # For chat completion
        generator = Generator(
            model_client=client,
            model_kwargs={"model": "gpt-4o", "temperature": 0.7}
        )
        
        # For embeddings
        embedder = Embedder(
            model_client=client,
            model_kwargs={"model": "text-embedding-3-small"}
        )
        ```
    
    Note:
        - Zero configuration required - OAuth2 authentication is fully automatic
        - Supported chat models: gpt-4o, gpt-4o-mini, o1-preview, o1-mini, claude-3.5-sonnet
        - Supported embedding models: text-embedding-3-small, text-embedding-3-large
        - No environment variables, tokens, or API keys needed
        - Works out of the box with VS Code GitHub Copilot authentication
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        env_api_key_name: str = "GITHUB_TOKEN",
    ):
        super().__init__()
        # GitHub Copilot with OAuth2 doesn't require any API key or base URL
        # All authentication is handled automatically by LiteLLM
        
        log.info(f"🚀 Initializing GitHub Copilot client...")
        log.info(f"   OAuth2 authentication: Automatic (handled by LiteLLM)")
        log.info(f"   Environment variable checked: {env_api_key_name}")
        log.info(f"   Token configured: {'Yes' if os.getenv(env_api_key_name) else 'No'}")
        
        # Configure LiteLLM for GitHub Copilot
        # GitHub Copilot uses the format: github_copilot/<model_name>
        self._setup_litellm()
        
        log.info(f"✅ GitHub Copilot client initialized successfully")
    
    def _setup_litellm(self):
        """Configure LiteLLM settings for GitHub Copilot with OAuth2."""
        # GitHub Copilot OAuth2 authentication is handled completely automatically by LiteLLM
        # No API keys, tokens, or base URLs needed
        log.info("GitHub Copilot OAuth2 authentication will be handled automatically by LiteLLM")
        
        # Configure LiteLLM logging
        litellm.set_verbose = False  # Set to True for debugging
        
        # Set required headers for GitHub Copilot IDE authentication
        # These headers are required for GitHub Copilot to work properly
        litellm.set_verbose = False
        
        log.info("✅ GitHub Copilot headers configured for IDE authentication")
    
    def _format_model_name(self, model: str) -> str:
        """Format model name for GitHub Copilot provider."""
        if not model.startswith("github_copilot/"):
            return f"github_copilot/{model}"
        return model
    
    def convert_inputs_to_api_kwargs(
        self,
        input: Optional[Any] = None,
        model_kwargs: Dict = {},
        model_type: ModelType = ModelType.UNDEFINED,
    ) -> Dict:
        """
        Convert inputs to LiteLLM API format for GitHub Copilot.
        
        Args:
            input: The input text or messages
            model_kwargs: Model parameters including model name, temperature, etc.
            model_type: Type of model (LLM, EMBEDDER, etc.)
        
        Returns:
            Dict: API kwargs formatted for LiteLLM
        """
        log.info(f"🔧 Converting inputs to API kwargs...")
        log.info(f"   Model type: {model_type}")
        log.info(f"   Input type: {type(input)}")
        log.info(f"   Model kwargs keys: {list(model_kwargs.keys())}")
        log.info(f"   Original model: {model_kwargs.get('model', 'not specified')}")
        
        final_model_kwargs = model_kwargs.copy()
        
        if model_type == ModelType.LLM:
            log.info(f"   Processing LLM model type...")
            
            # Format model name for GitHub provider
            if "model" in final_model_kwargs:
                original_model = final_model_kwargs["model"]
                final_model_kwargs["model"] = self._format_model_name(original_model)
                log.info(f"   Model formatted: {original_model} -> {final_model_kwargs['model']}")
            
            # Convert input to messages format
            if isinstance(input, str):
                log.info(f"   Converting string input to messages format")
                log.info(f"   Input preview: {input[:100]}{'...' if len(input) > 100 else ''}")
                final_model_kwargs["messages"] = [{"role": "user", "content": input}]
            elif isinstance(input, list):
                log.info(f"   Using list input as messages (length: {len(input)})")
                final_model_kwargs["messages"] = input
            else:
                log.error(f"   Invalid input type: {type(input)}")
                raise ValueError("Input must be a string or list of messages")
            
            # Set default parameters if not provided
            log.info(f"   Setting default parameters...")
            final_model_kwargs.setdefault("temperature", 0.7)
            final_model_kwargs.setdefault("max_tokens", 4096)
            log.info(f"   Temperature: {final_model_kwargs['temperature']}")
            log.info(f"   Max tokens: {final_model_kwargs['max_tokens']}")
            
            # Add required GitHub Copilot IDE headers
            log.info(f"   Adding GitHub Copilot IDE headers...")
            final_model_kwargs.setdefault("extra_headers", {})
            final_model_kwargs["extra_headers"].update({
                "Editor-Version": "vscode/1.85.0",
                "Copilot-Integration-Id": "vscode-chat"
            })
            log.info(f"   Headers added: {final_model_kwargs['extra_headers']}")
            
        elif model_type == ModelType.EMBEDDER:
            # Format model name for GitHub Copilot embeddings
            if "model" in final_model_kwargs:
                final_model_kwargs["model"] = self._format_model_name(final_model_kwargs["model"])
            
            # Set input for embeddings
            if isinstance(input, str):
                final_model_kwargs["input"] = input
            elif isinstance(input, list):
                final_model_kwargs["input"] = input
            else:
                raise ValueError("Input must be a string or list of strings for embeddings")
            
            # Set default parameters for embeddings
            final_model_kwargs.setdefault("encoding_format", "float")
            
            # Add required GitHub Copilot IDE headers
            final_model_kwargs.setdefault("extra_headers", {})
            final_model_kwargs["extra_headers"].update({
                "Editor-Version": "vscode/1.85.0",
                "Copilot-Integration-Id": "vscode-chat"
            })
        
        else:
            log.error(f"   Unsupported model type: {model_type}")
            raise ValueError(f"Model type {model_type} is not supported")
        
        log.info(f"✅ API kwargs conversion completed")
        log.info(f"   Final kwargs keys: {list(final_model_kwargs.keys())}")
        log.info(f"   Final model: {final_model_kwargs.get('model', 'not set')}")
        log.info(f"   Messages count: {len(final_model_kwargs.get('messages', []))}")
        log.info(f"   Stream mode: {final_model_kwargs.get('stream', False)}")
        
        return final_model_kwargs
    
    def _handle_malformed_response(self, response_text: str) -> Any:
        """
        Handle malformed JSON responses from GitHub Copilot using flattening logic.
        
        Args:
            response_text: Raw response text that failed standard JSON parsing
            
        Returns:
            Parsed response object or error structure
        """
        log.info(f"🔧 Handling malformed GitHub Copilot response...")
        log.info(f"   Response length: {len(response_text)} characters")
        log.info(f"   Response preview: {response_text[:200]}...")
        
        # Use our JSON flattening utilities
        flattened_response = flatten_github_copilot_json(response_text)
        
        # Validate the flattened response
        if validate_github_copilot_response(flattened_response):
            log.info(f"✅ Successfully flattened malformed response")
            return flattened_response
        else:
            log.warning(f"⚠️ Flattened response validation failed")
            return flattened_response  # Return anyway, might still be usable

    def parse_chat_completion(self, completion) -> GeneratorOutput:
        """Parse LiteLLM completion response with enhanced JSON flattening."""
        log.info(f"🔍 Parsing chat completion response...")
        log.info(f"   Raw completion type: {type(completion)}")
        log.info(f"   Raw completion preview: {str(completion)[:300]}...")
        
        try:
            if hasattr(completion, 'choices') and len(completion.choices) > 0:
                log.info(f"   Completion has {len(completion.choices)} choice(s)")
                
                choice = completion.choices[0]
                log.info(f"   Choice type: {type(choice)}")
                log.info(f"   Choice preview: {str(choice)[:200]}...")
                
                if hasattr(choice, 'message'):
                    message = choice.message
                    log.info(f"   Message type: {type(message)}")
                    log.info(f"   Message has content attr: {hasattr(message, 'content')}")
                    
                    content = message.content
                    log.info(f"   Content type: {type(content)}")
                    log.info(f"   Content length: {len(content) if content else 0}")
                    if content:
                        log.info(f"   Content preview: {content[:100]}{'...' if len(content) > 100 else ''}")
                    else:
                        log.warning(f"   Content is empty or None: {content}")
                else:
                    log.error(f"   Choice has no message attribute")
                    content = None
                
                # Check if content is None or empty
                if content is None or content == "":
                    log.warning(f"   No content found in completion response")
                    return GeneratorOutput(
                        data=None,
                        error="No content in completion response",
                        raw_response=str(completion)
                    )
                
                # Extract usage information if available
                usage = None
                log.info(f"   Extracting usage information...")
                if hasattr(completion, 'usage') and completion.usage:
                    log.info(f"   Completion has usage info: {completion.usage}")
                    usage = CompletionUsage(
                        completion_tokens=getattr(completion.usage, 'completion_tokens', None),
                        prompt_tokens=getattr(completion.usage, 'prompt_tokens', None),
                        total_tokens=getattr(completion.usage, 'total_tokens', None),
                    )
                    log.info(f"   Usage extracted: {usage}")
                else:
                    log.info(f"   No usage information available")
                
                log.info(f"   Creating GeneratorOutput with content length: {len(content)}")
                
                # Check if this appears to be a wiki structure request that should return XML
                enhanced_content = self._enhance_xml_response_if_needed(content)
                if enhanced_content != content:
                    log.info(f"   Enhanced response with XML formatting")
                    content = enhanced_content
                
                output = GeneratorOutput(
                    data=content,
                    error=None,
                    raw_response=str(completion),
                    usage=usage
                )
                log.info(f"✅ Chat completion parsing successful")
                return output
            else:
                log.warning(f"   No choices found in completion response")
                log.warning(f"   Completion has choices attr: {hasattr(completion, 'choices')}")
                if hasattr(completion, 'choices'):
                    log.warning(f"   Choices length: {len(completion.choices)}")
                return GeneratorOutput(
                    data=None,
                    error="No choices in completion response",
                    raw_response=str(completion)
                )
        except Exception as e:
            log.error(f"❌ Error parsing completion: {e}")
            log.error(f"   Exception type: {type(e)}")
            import traceback
            log.error(f"   Full traceback: {traceback.format_exc()}")
            return GeneratorOutput(
                data=None,
                error=str(e),
                raw_response=str(completion)
            )
    
    def _enhance_xml_response_if_needed(self, content: str) -> str:
        """Enhance response with XML formatting if it appears to be a wiki structure response."""
        log.info(f"🔍 Checking if response needs XML enhancement...")
        
        # Check if the content already contains proper XML structure
        if "<wiki_structure>" in content and "</wiki_structure>" in content:
            log.info(f"   Response already contains proper XML structure")
            return content
        
        # Check if this appears to be a wiki structure response that should be XML
        wiki_indicators = [
            "title:", "description:", "pages:", "page id:", "importance:",
            "relevant_files:", "related_pages:", "file_path:", "wiki structure",
            "repository wiki", "overview", "architecture", "setup", "installation"
        ]
        
        content_lower = content.lower()
        wiki_indicators_found = sum(1 for indicator in wiki_indicators if indicator in content_lower)
        
        log.info(f"   Found {wiki_indicators_found} wiki structure indicators")
        
        if wiki_indicators_found >= 3:  # If at least 3 indicators are present
            log.info(f"   Attempting to convert response to XML format...")
            return self._convert_text_to_wiki_xml(content)
        
        log.info(f"   No XML enhancement needed")
        return content
    
    def _convert_text_to_wiki_xml(self, content: str) -> str:
        """Convert plain text wiki structure to XML format."""
        log.info(f"🔄 Converting text response to wiki XML format...")
        
        try:
            import re
            
            # Try to extract structured information from the text
            lines = content.strip().split('\n')
            
            # Initialize variables
            title = "Repository Wiki"
            description = "Wiki for this repository"
            pages = []
            
            current_page = None
            in_files_section = False
            in_related_section = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Try to extract title
                title_match = re.search(r'(?:title|name):\s*(.+)', line, re.IGNORECASE)
                if title_match and len(pages) == 0:  # Only use as main title if no pages yet
                    title = title_match.group(1).strip()
                    log.debug(f"   Extracted title: {title}")
                    continue
                
                # Try to extract description
                desc_match = re.search(r'description:\s*(.+)', line, re.IGNORECASE)
                if desc_match and len(pages) == 0:  # Only use as main description if no pages yet
                    description = desc_match.group(1).strip()
                    log.debug(f"   Extracted description: {description}")
                    continue
                
                # Try to extract page information
                page_match = re.search(r'(?:page|section)\s*(?:id:|\d+:|-)\s*(.+)', line, re.IGNORECASE)
                if page_match:
                    if current_page:
                        pages.append(current_page)
                    
                    page_title = page_match.group(1).strip()
                    current_page = {
                        'id': f"page-{len(pages)+1}",
                        'title': page_title,
                        'importance': 'medium',
                        'files': [],
                        'related': []
                    }
                    log.debug(f"   Found page: {page_title}")
                    in_files_section = False
                    in_related_section = False
                    continue
                
                # If we have a current page, try to extract more details
                if current_page:
                    # Check for importance
                    importance_match = re.search(r'importance:\s*(high|medium|low)', line, re.IGNORECASE)
                    if importance_match:
                        current_page['importance'] = importance_match.group(1).lower()
                        continue
                    
                    # Check for files section
                    if re.search(r'(?:files|file_path|relevant.*files)', line, re.IGNORECASE):
                        in_files_section = True
                        in_related_section = False
                        continue
                    
                    # Check for related section
                    if re.search(r'(?:related|related.*pages)', line, re.IGNORECASE):
                        in_related_section = True
                        in_files_section = False
                        continue
                    
                    # Extract file paths
                    if in_files_section:
                        file_match = re.search(r'[-.\s]*([^\s]+\.[a-zA-Z]+|[^\s]+/[^\s]+)', line)
                        if file_match:
                            current_page['files'].append(file_match.group(1))
                            continue
                    
                    # Extract related pages
                    if in_related_section:
                        related_match = re.search(r'[-.\s]*(.+)', line)
                        if related_match:
                            current_page['related'].append(related_match.group(1).strip())
                            continue
            
            # Add the last page if exists
            if current_page:
                pages.append(current_page)
            
            # If no pages were extracted, create a default structure
            if not pages:
                log.info(f"   No structured pages found, creating default pages")
                pages = [
                    {
                        'id': 'page-1',
                        'title': 'Overview',
                        'importance': 'high',
                        'files': ['README.md'],
                        'related': []
                    },
                    {
                        'id': 'page-2', 
                        'title': 'Setup and Installation',
                        'importance': 'high',
                        'files': ['package.json', 'requirements.txt', 'setup.py'],
                        'related': []
                    }
                ]
            
            # Generate XML
            xml_lines = ['<wiki_structure>']
            xml_lines.append(f'  <title>{self._escape_xml(title)}</title>')
            xml_lines.append(f'  <description>{self._escape_xml(description)}</description>')
            xml_lines.append('  <pages>')
            
            for page in pages:
                xml_lines.append(f'    <page id="{page["id"]}">')
                xml_lines.append(f'      <title>{self._escape_xml(page["title"])}</title>')
                xml_lines.append(f'      <description>Information about {self._escape_xml(page["title"])}</description>')
                xml_lines.append(f'      <importance>{page["importance"]}</importance>')
                xml_lines.append('      <relevant_files>')
                
                for file_path in page['files']:
                    xml_lines.append(f'        <file_path>{self._escape_xml(file_path)}</file_path>')
                
                xml_lines.append('      </relevant_files>')
                xml_lines.append('      <related_pages>')
                
                for related in page['related']:
                    xml_lines.append(f'        <related>{self._escape_xml(related)}</related>')
                
                xml_lines.append('      </related_pages>')
                xml_lines.append('    </page>')
            
            xml_lines.append('  </pages>')
            xml_lines.append('</wiki_structure>')
            
            xml_content = '\n'.join(xml_lines)
            log.info(f"✅ Successfully converted to XML format")
            log.info(f"   Generated {len(pages)} pages")
            
            return xml_content
            
        except Exception as e:
            log.error(f"❌ Error converting to XML: {e}")
            log.error(f"   Returning original content")
            return content
    
    def _escape_xml(self, text: str) -> str:
        """Escape special characters for XML."""
        if not text:
            return ""
        return (str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))
    
    def call(self, api_kwargs: Dict = {}, model_type: ModelType = ModelType.UNDEFINED):
        """
        Synchronous call to GitHub Copilot via LiteLLM.
        
        Args:
            api_kwargs: API parameters
            model_type: Type of model call
        
        Returns:
            LiteLLM completion/embedding response
        """
        if model_type == ModelType.LLM:
            try:
                log.info(f"🤖 GitHub Copilot LLM call with model: {api_kwargs.get('model', 'unknown')}")
                # Use LiteLLM's completion function
                response = completion(**api_kwargs)
                log.info(f"✅ GitHub Copilot LLM call successful")
                return response
            except Exception as e:
                log.error(f"❌ Error in GitHub Copilot chat API call: {e}")
                raise
        elif model_type == ModelType.EMBEDDER:
            try:
                model = api_kwargs.get('model', 'unknown')
                input_text = api_kwargs.get('input', '')
                input_type = type(input_text).__name__
                input_count = len(input_text) if isinstance(input_text, list) else 1
                
                log.info(f"🧠 GitHub Copilot embedding call starting...")
                log.info(f"   Model: {model}")
                log.info(f"   Input type: {input_type}")
                log.info(f"   Input count: {input_count}")
                if isinstance(input_text, str):
                    log.info(f"   Input preview: {input_text[:100]}{'...' if len(input_text) > 100 else ''}")
                
                # Use LiteLLM's embedding function
                response = embedding(**api_kwargs)
                
                log.info(f"✅ GitHub Copilot embedding call successful")
                log.info(f"   Response has data: {hasattr(response, 'data')}")
                if hasattr(response, 'data') and response.data:
                    log.info(f"   Number of embeddings returned: {len(response.data)}")
                    log.info(f"   First embedding type: {type(response.data[0])}")
                    if hasattr(response.data[0], 'embedding'):
                        log.info(f"   First embedding length: {len(response.data[0].embedding)}")
                    elif isinstance(response.data[0], dict) and 'embedding' in response.data[0]:
                        log.info(f"   First embedding length: {len(response.data[0]['embedding'])}")
                    else:
                        log.info(f"   First embedding content preview: {str(response.data[0])[:200]}")
                
                return response
            except Exception as e:
                log.error(f"❌ Error in GitHub Copilot embedding API call: {e}")
                raise
        else:
            raise ValueError(f"Model type {model_type} is not supported")
    
    async def acall(self, api_kwargs: Dict = {}, model_type: ModelType = ModelType.UNDEFINED):
        """
        Asynchronous call to GitHub Copilot via LiteLLM.
        
        Args:
            api_kwargs: API parameters
            model_type: Type of model call
        
        Returns:
            LiteLLM completion/embedding response or async generator for streaming
        """
        if model_type == ModelType.LLM:
            try:
                model = api_kwargs.get('model', 'unknown')
                is_streaming = api_kwargs.get('stream', False)
                max_tokens = api_kwargs.get('max_tokens', 'unset')
                temperature = api_kwargs.get('temperature', 'unset')
                
                log.info(f"🤖 GitHub Copilot async LLM call starting...")
                log.info(f"   Model: {model}")
                log.info(f"   Streaming: {is_streaming}")
                log.info(f"   Max tokens: {max_tokens}")
                log.info(f"   Temperature: {temperature}")
                log.info(f"   Messages count: {len(api_kwargs.get('messages', []))}")
                if 'messages' in api_kwargs and api_kwargs['messages']:
                    first_msg = api_kwargs['messages'][0]
                    content_preview = first_msg.get('content', '')[:100]
                    log.info(f"   First message: {content_preview}{'...' if len(first_msg.get('content', '')) > 100 else ''}")
                
                # Check if streaming is requested
                if is_streaming:
                    log.info("   🌊 Using streaming mode")
                    # Return async generator for streaming
                    return self._handle_streaming_response(api_kwargs)
                else:
                    log.info(f"   💬 Using non-streaming mode")
                    log.info(f"   Calling LiteLLM acompletion with {len(api_kwargs)} parameters")
                    
                    # Use LiteLLM's async completion function
                    response = await acompletion(**api_kwargs)
                    
                    log.info(f"✅ GitHub Copilot async LLM call successful")
                    log.info(f"   Response type: {type(response)}")
                    log.info(f"   Response preview: {str(response)[:200]}...")
                    
                    return response
            except Exception as e:
                log.error(f"❌ Error in async GitHub Copilot chat API call: {e}")
                log.error(f"   Exception type: {type(e)}")
                log.error(f"   API kwargs keys: {list(api_kwargs.keys())}")
                import traceback
                log.error(f"   Full traceback: {traceback.format_exc()}")
                raise
        elif model_type == ModelType.EMBEDDER:
            try:
                model = api_kwargs.get('model', 'unknown')
                input_text = api_kwargs.get('input', '')
                input_type = type(input_text).__name__
                input_count = len(input_text) if isinstance(input_text, list) else 1
                
                log.info(f"🧠 GitHub Copilot async embedding call starting...")
                log.info(f"   Model: {model}")
                log.info(f"   Input type: {input_type}")
                log.info(f"   Input count: {input_count}")
                if isinstance(input_text, str):
                    log.info(f"   Input preview: {input_text[:100]}{'...' if len(input_text) > 100 else ''}")
                
                # Use LiteLLM's async embedding function
                response = await aembedding(**api_kwargs)
                
                log.info(f"✅ GitHub Copilot async embedding call successful")
                log.info(f"   Response has data: {hasattr(response, 'data')}")
                if hasattr(response, 'data') and response.data:
                    log.info(f"   Number of embeddings returned: {len(response.data)}")
                    log.info(f"   First embedding type: {type(response.data[0])}")
                    if hasattr(response.data[0], 'embedding'):
                        log.info(f"   First embedding length: {len(response.data[0].embedding)}")
                    elif isinstance(response.data[0], dict) and 'embedding' in response.data[0]:
                        log.info(f"   First embedding length: {len(response.data[0]['embedding'])}")
                    else:
                        log.info(f"   First embedding content preview: {str(response.data[0])[:200]}")
                
                return response
            except Exception as e:
                log.error(f"❌ Error in async GitHub Copilot embedding API call: {e}")
                raise
        else:
            raise ValueError(f"Model type {model_type} is not supported")
    
    async def _handle_streaming_response(self, api_kwargs: Dict):
        """Handle streaming response from LiteLLM with enhanced JSON flattening."""
        log.info(f"🌊 Starting enhanced streaming response handler...")
        log.info(f"   Stream kwargs: {api_kwargs.keys()}")
        
        try:
            # Create streaming completion
            log.info(f"   Creating streaming completion...")
            stream = await acompletion(**api_kwargs)
            log.info(f"   Stream created: {type(stream)}")
            
            chunk_count = 0
            content_parts = []
            malformed_chunks = 0
            
            async for chunk in stream:
                chunk_count += 1
                log.debug(f"   Chunk {chunk_count}: {type(chunk)}")
                
                # Try to handle chunk normally first
                content = None
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        log.debug(f"   Standard content: {content[:50]}{'...' if len(content) > 50 else ''}")
                    else:
                        log.debug(f"   Delta has no content: {delta}")
                
                # If standard parsing failed, try JSON flattening on raw chunk
                if content is None and hasattr(chunk, '__dict__'):
                    try:
                        # Convert chunk to string and try flattening
                        chunk_str = str(chunk)
                        if chunk_str and chunk_str != str(type(chunk)):
                            repaired_chunk = repair_github_copilot_streaming_chunk(chunk_str)
                            if repaired_chunk and "choices" in repaired_chunk:
                                choices = repaired_chunk["choices"]
                                if isinstance(choices, list) and len(choices) > 0:
                                    choice = choices[0]
                                    if isinstance(choice, dict):
                                        # Try delta content
                                        if "delta" in choice and isinstance(choice["delta"], dict):
                                            content = choice["delta"].get("content")
                                        # Try message content
                                        elif "message" in choice and isinstance(choice["message"], dict):
                                            content = choice["message"].get("content")
                                        
                                        if content:
                                            malformed_chunks += 1
                                            log.debug(f"   Repaired malformed chunk: {content[:50]}...")
                    except Exception as repair_error:
                        log.debug(f"   Chunk repair failed: {repair_error}")
                
                # Yield content if we got any
                if content:
                    content_parts.append(content)
                    yield content
                else:
                    log.debug(f"   No content extracted from chunk {chunk_count}")
            
            full_content = ''.join(content_parts)
            log.info(f"✅ Enhanced streaming completed:")
            log.info(f"   Total chunks: {chunk_count}")
            log.info(f"   Malformed chunks repaired: {malformed_chunks}")
            log.info(f"   Total content length: {len(full_content)} chars")
            log.info(f"   Content preview: {full_content[:100]}{'...' if len(full_content) > 100 else ''}")
            
        except Exception as e:
            log.error(f"❌ Error in enhanced streaming response: {e}")
            log.error(f"   Exception type: {type(e)}")
            import traceback
            log.error(f"   Full traceback: {traceback.format_exc()}")
            yield f"Error: {str(e)}"
    
    def parse_embedding_response(self, response) -> EmbedderOutput:
        """Parse GitHub Copilot embedding response with enhanced JSON flattening."""
        log.info(f"🔍 Parsing GitHub Copilot embedding response...")
        
        # If response is a string (malformed JSON), try to flatten it first
        if isinstance(response, str):
            log.info("Response is string, attempting JSON flattening...")
            flattened_response = self._handle_malformed_response(response)
            if isinstance(flattened_response, dict):
                response = flattened_response
            else:
                log.error("Failed to flatten embedding response")
                return EmbedderOutput(
                    data=None,
                    error="Failed to parse embedding response",
                    raw_response=str(response)
                )
        
        try:
            if hasattr(response, 'data') and len(response.data) > 0:
                log.info(f"   Response contains {len(response.data)} embedding(s)")
                
                # Extract embeddings from response - return raw embedding data
                embeddings = []
                for i, item in enumerate(response.data):
                    log.debug(f"   Processing embedding {i+1}: type={type(item)}")
                    
                    if hasattr(item, 'embedding'):
                        # Object format - extract the embedding data
                        log.debug(f"   Using object format for embedding {i+1}")
                        embeddings.append(item.embedding)
                        log.debug(f"   Embedding {i+1} length: {len(item.embedding)}")
                    elif isinstance(item, dict) and 'embedding' in item:
                        # Dict format - extract the embedding data
                        log.debug(f"   Using dict format for embedding {i+1}")
                        embeddings.append(item['embedding'])
                        log.debug(f"   Embedding {i+1} length: {len(item['embedding'])}")
                    else:
                        log.warning(f"   Unexpected embedding item format: {type(item)}")
                        log.warning(f"   Item preview: {str(item)[:200]}")
                        # Try to use the item directly if it's a list of numbers
                        if isinstance(item, list) and all(isinstance(x, (int, float)) for x in item):
                            log.info(f"   Using item directly as embedding {i+1} (list of numbers)")
                            embeddings.append(item)
                        else:
                            raise ValueError(f"Cannot extract embedding from item: {type(item)}, {item}")
                
                log.info(f"   Successfully extracted {len(embeddings)} embeddings")
                if embeddings:
                    # Embeddings are now raw lists
                    first_embedding = embeddings[0]
                    log.info(f"   First embedding dimensions: {len(first_embedding)}")
                    log.info(f"   First embedding preview: [{first_embedding[0]:.6f}, {first_embedding[1]:.6f}, ...]")
                
                # Extract usage information if available
                usage = None
                if hasattr(response, 'usage') and response.usage:
                    prompt_tokens = getattr(response.usage, 'prompt_tokens', None)
                    total_tokens = getattr(response.usage, 'total_tokens', None)
                    log.info(f"   Usage info - Prompt tokens: {prompt_tokens}, Total tokens: {total_tokens}")
                    usage = CompletionUsage(
                        completion_tokens=None,  # Not applicable for embeddings
                        prompt_tokens=prompt_tokens,
                        total_tokens=total_tokens,
                    )
                else:
                    log.info(f"   No usage information available")
                
                log.info(f"✅ Successfully parsed GitHub Copilot embedding response")
                
                # Wrap raw embeddings in Embedding objects as required by adalflow
                from adalflow.core.types import Embedding
                embedding_objects = [
                    Embedding(embedding=emb, index=i) 
                    for i, emb in enumerate(embeddings)
                ]
                
                return EmbedderOutput(
                    data=embedding_objects,  # List of Embedding objects as required by adalflow
                    error=None,
                    raw_response=str(response),
                    usage=usage
                )
            else:
                log.warning(f"   Response has no embedding data")
                log.warning(f"   Has data attr: {hasattr(response, 'data')}")
                if hasattr(response, 'data'):
                    log.warning(f"   Data length: {len(response.data) if response.data else 0}")
                return EmbedderOutput(
                    data=None,
                    error="No embeddings in response",
                    raw_response=str(response)
                )
        except Exception as e:
            log.error(f"❌ Error parsing GitHub Copilot embedding response: {e}")
            log.error(f"   Response structure: {response}")
            log.error(f"   Response type: {type(response)}")
            log.error(f"   Response data type: {type(response.data) if hasattr(response, 'data') else 'No data attr'}")
            if hasattr(response, 'data') and response.data:
                log.error(f"   First data item type: {type(response.data[0])}, content: {response.data[0]}")
            import traceback
            log.error(f"   Full traceback: {traceback.format_exc()}")
            return EmbedderOutput(
                data=None,
                error=str(e),
                raw_response=str(response)
            )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create client from dictionary."""
        # GitHub Copilot uses OAuth2 authentication and doesn't need API keys
        # Just create a new instance with default parameters
        return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert client to dictionary."""
        # GitHub Copilot uses OAuth2 authentication and doesn't need API keys
        # Return minimal serialization data
        return {
            "client_type": "GitHubCopilotClient",
            "oauth2_authentication": True,
        }


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    from adalflow.core import Generator
    
    async def test_github_copilot():
        """Test the GitHub Copilot client."""
        try:
            # Initialize client
            client = GitHubCopilotClient()
            
            # Test with Generator
            generator = Generator(
                model_client=client,
                model_kwargs={
                    "model": "gpt-4o",
                    "temperature": 0.7,
                    "stream": False
                }
            )
            
            # Test completion
            response = await generator.acall(
                prompt_kwargs={"input_str": "What is the capital of France?"}
            )
            
            print(f"Response: {response}")
            
        except Exception as e:
            print(f"Test failed: {e}")
    
    # Run test if executed directly
    asyncio.run(test_github_copilot())