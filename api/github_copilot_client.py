"""GitHub Copilot ModelClient integration using LiteLLM."""

import os
import logging
from typing import Dict, Any, Optional, Union, Generator
import asyncio

# LiteLLM imports
import litellm
from litellm import completion, acompletion

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
    A ModelClient wrapper for GitHub Copilot using LiteLLM in direct mode.
    
    This client provides access to GitHub Copilot models through LiteLLM's unified interface.
    GitHub Copilot uses OAuth2 authentication, which is handled automatically by LiteLLM.
    
    Args:
        api_key (Optional[str]): GitHub token for API access. If not provided, will use GITHUB_TOKEN environment variable.
                                Note: This can be a personal access token or OAuth token.
        base_url (Optional[str]): Base URL for the GitHub Copilot API. Defaults to GitHub's inference endpoint.
        env_api_key_name (str): Environment variable name for the API key. Defaults to "GITHUB_TOKEN".
    
    Example:
        ```python
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core import Generator
        
        # GitHub Copilot will use OAuth2 authentication automatically
        client = GitHubCopilotClient()
        generator = Generator(
            model_client=client,
            model_kwargs={"model": "gpt-4o", "temperature": 0.7}
        )
        ```
    
    Note:
        - GitHub Copilot uses OAuth2 authentication handled by LiteLLM
        - Supported models include: gpt-4o, gpt-4o-mini, o1-preview, o1-mini
        - No manual token configuration required for OAuth2 flow
        - Personal access tokens can still be used via GITHUB_TOKEN environment variable
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        env_api_key_name: str = "GITHUB_TOKEN",
    ):
        super().__init__()
        self._api_key = api_key
        self._env_api_key_name = env_api_key_name
        self.base_url = base_url or "https://models.inference.ai.azure.com"
        
        # GitHub Copilot uses OAuth2, but we still need a token for API access
        # This can be a GitHub personal access token or OAuth token
        self.api_key = self._api_key or os.getenv(self._env_api_key_name)
        
        # Configure LiteLLM for GitHub Copilot
        # GitHub Copilot uses the format: github/<model_name>
        self._setup_litellm()
    
    def _setup_litellm(self):
        """Configure LiteLLM settings for GitHub Copilot."""
        # Set the API key for GitHub provider if available
        if self.api_key:
            os.environ["GITHUB_TOKEN"] = self.api_key
        
        # Configure LiteLLM logging
        litellm.set_verbose = False  # Set to True for debugging
        
        # Set custom base URL if provided
        if self.base_url:
            os.environ["GITHUB_API_BASE"] = self.base_url
        
        # GitHub Copilot specific configuration for OAuth2
        # LiteLLM will handle OAuth2 flow automatically when using github/ prefix
    
    def _format_model_name(self, model: str) -> str:
        """Format model name for GitHub Copilot provider."""
        if not model.startswith("github/"):
            return f"github/{model}"
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
        final_model_kwargs = model_kwargs.copy()
        
        if model_type == ModelType.LLM:
            # Format model name for GitHub provider
            if "model" in final_model_kwargs:
                final_model_kwargs["model"] = self._format_model_name(final_model_kwargs["model"])
            
            # Convert input to messages format
            if isinstance(input, str):
                final_model_kwargs["messages"] = [{"role": "user", "content": input}]
            elif isinstance(input, list):
                final_model_kwargs["messages"] = input
            else:
                raise ValueError("Input must be a string or list of messages")
            
            # Set default parameters if not provided
            final_model_kwargs.setdefault("temperature", 0.7)
            final_model_kwargs.setdefault("max_tokens", 4096)
            
        elif model_type == ModelType.EMBEDDER:
            raise ValueError("GitHub Copilot does not support embedding models through this client")
        
        else:
            raise ValueError(f"Model type {model_type} is not supported")
        
        return final_model_kwargs
    
    def parse_chat_completion(self, completion) -> GeneratorOutput:
        """Parse LiteLLM completion response."""
        try:
            if hasattr(completion, 'choices') and len(completion.choices) > 0:
                content = completion.choices[0].message.content
                
                # Extract usage information if available
                usage = None
                if hasattr(completion, 'usage') and completion.usage:
                    usage = CompletionUsage(
                        completion_tokens=getattr(completion.usage, 'completion_tokens', None),
                        prompt_tokens=getattr(completion.usage, 'prompt_tokens', None),
                        total_tokens=getattr(completion.usage, 'total_tokens', None),
                    )
                
                return GeneratorOutput(
                    data=content,
                    error=None,
                    raw_response=str(completion),
                    usage=usage
                )
            else:
                return GeneratorOutput(
                    data=None,
                    error="No choices in completion response",
                    raw_response=str(completion)
                )
        except Exception as e:
            log.error(f"Error parsing completion: {e}")
            return GeneratorOutput(
                data=None,
                error=str(e),
                raw_response=str(completion)
            )
    
    def call(self, api_kwargs: Dict = {}, model_type: ModelType = ModelType.UNDEFINED):
        """
        Synchronous call to GitHub Copilot via LiteLLM.
        
        Args:
            api_kwargs: API parameters
            model_type: Type of model call
        
        Returns:
            LiteLLM completion response
        """
        if model_type == ModelType.LLM:
            try:
                # Use LiteLLM's completion function
                response = completion(**api_kwargs)
                return response
            except Exception as e:
                log.error(f"Error in GitHub Copilot API call: {e}")
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
            LiteLLM completion response or async generator for streaming
        """
        if model_type == ModelType.LLM:
            try:
                # Check if streaming is requested
                if api_kwargs.get("stream", False):
                    # Return async generator for streaming
                    return self._handle_streaming_response(api_kwargs)
                else:
                    # Use LiteLLM's async completion function
                    response = await acompletion(**api_kwargs)
                    return response
            except Exception as e:
                log.error(f"Error in async GitHub Copilot API call: {e}")
                raise
        else:
            raise ValueError(f"Model type {model_type} is not supported")
    
    async def _handle_streaming_response(self, api_kwargs: Dict):
        """Handle streaming response from LiteLLM."""
        try:
            # Create streaming completion
            stream = await acompletion(**api_kwargs)
            
            async for chunk in stream:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield delta.content
        except Exception as e:
            log.error(f"Error in streaming response: {e}")
            yield f"Error: {str(e)}"
    
    def parse_embedding_response(self, response) -> EmbedderOutput:
        """Parse embedding response (not supported for GitHub Copilot)."""
        raise NotImplementedError("GitHub Copilot does not support embeddings through this client")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create client from dictionary."""
        return cls(
            api_key=data.get("api_key"),
            base_url=data.get("base_url"),
            env_api_key_name=data.get("env_api_key_name", "GITHUB_TOKEN"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert client to dictionary."""
        return {
            "api_key": self._api_key,
            "base_url": self.base_url,
            "env_api_key_name": self._env_api_key_name,
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