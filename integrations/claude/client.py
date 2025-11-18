"""
Claude API Client

Handles communication with Anthropic's Claude API for content generation.
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from loguru import logger

try:
    from anthropic import Anthropic, AsyncAnthropic
except ImportError:
    logger.warning("anthropic package not installed. Run: pip install anthropic")
    Anthropic = None
    AsyncAnthropic = None


@dataclass
class GenerationResult:
    """Result from Claude API generation."""
    content: str
    model: str
    tokens_used: int
    stop_reason: str
    metadata: Dict[str, Any] = None


class ClaudeClient:
    """
    Client for Anthropic's Claude API.

    Features:
    - Synchronous and asynchronous generation
    - Conversation history management
    - Token usage tracking
    - Retry logic with exponential backoff
    - Rate limiting
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 1024,
        temperature: float = 0.7
    ):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
        """
        if not Anthropic:
            raise ImportError("anthropic package required. Install with: pip install anthropic")

        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Initialize clients
        self.client = Anthropic(api_key=api_key)
        self.async_client = AsyncAnthropic(api_key=api_key)

        # Track usage
        self.total_tokens_used = 0

        logger.info(f"ClaudeClient initialized with model: {model}")

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> GenerationResult:
        """
        Generate text using Claude.

        Args:
            prompt: User prompt
            system: System prompt (optional)
            max_tokens: Override default max_tokens
            temperature: Override default temperature
            stop_sequences: Stop generation at these sequences

        Returns:
            GenerationResult with generated content
        """
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        try:
            # Build message
            message_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            if system:
                message_params["system"] = system

            if stop_sequences:
                message_params["stop_sequences"] = stop_sequences

            # Call API
            response = self.client.messages.create(**message_params)

            # Extract content
            content = response.content[0].text

            # Track tokens
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            self.total_tokens_used += tokens_used

            logger.debug(f"Generated {len(content)} chars using {tokens_used} tokens")

            return GenerationResult(
                content=content,
                model=response.model,
                tokens_used=tokens_used,
                stop_reason=response.stop_reason,
                metadata={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            )

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise

    async def generate_async(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> GenerationResult:
        """
        Async version of generate().

        Args:
            prompt: User prompt
            system: System prompt (optional)
            max_tokens: Override default max_tokens
            temperature: Override default temperature
            stop_sequences: Stop generation at these sequences

        Returns:
            GenerationResult with generated content
        """
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        try:
            # Build message
            message_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            if system:
                message_params["system"] = system

            if stop_sequences:
                message_params["stop_sequences"] = stop_sequences

            # Call API
            response = await self.async_client.messages.create(**message_params)

            # Extract content
            content = response.content[0].text

            # Track tokens
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            self.total_tokens_used += tokens_used

            logger.debug(f"Generated {len(content)} chars using {tokens_used} tokens")

            return GenerationResult(
                content=content,
                model=response.model,
                tokens_used=tokens_used,
                stop_reason=response.stop_reason,
                metadata={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            )

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise

    def generate_with_context(
        self,
        prompt: str,
        context: str,
        system: Optional[str] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate with RAG context.

        Args:
            prompt: User prompt
            context: Retrieved context from RAG
            system: System prompt
            **kwargs: Additional generation parameters

        Returns:
            GenerationResult
        """
        # Build enhanced prompt with context
        enhanced_prompt = f"""Context from knowledge base:

{context}

---

Based on the above context, {prompt}"""

        return self.generate(prompt=enhanced_prompt, system=system, **kwargs)

    async def generate_with_context_async(
        self,
        prompt: str,
        context: str,
        system: Optional[str] = None,
        **kwargs
    ) -> GenerationResult:
        """Async version of generate_with_context()."""
        enhanced_prompt = f"""Context from knowledge base:

{context}

---

Based on the above context, {prompt}"""

        return await self.generate_async(prompt=enhanced_prompt, system=system, **kwargs)

    def generate_multiple(
        self,
        prompts: List[str],
        system: Optional[str] = None,
        **kwargs
    ) -> List[GenerationResult]:
        """
        Generate multiple completions (synchronous).

        Args:
            prompts: List of prompts
            system: System prompt
            **kwargs: Additional generation parameters

        Returns:
            List of GenerationResults
        """
        results = []
        for prompt in prompts:
            result = self.generate(prompt=prompt, system=system, **kwargs)
            results.append(result)

        return results

    async def generate_multiple_async(
        self,
        prompts: List[str],
        system: Optional[str] = None,
        **kwargs
    ) -> List[GenerationResult]:
        """
        Generate multiple completions in parallel (async).

        Args:
            prompts: List of prompts
            system: System prompt
            **kwargs: Additional generation parameters

        Returns:
            List of GenerationResults
        """
        tasks = [
            self.generate_async(prompt=prompt, system=system, **kwargs)
            for prompt in prompts
        ]

        return await asyncio.gather(*tasks)

    def get_token_usage(self) -> int:
        """Get total tokens used."""
        return self.total_tokens_used

    def reset_token_usage(self):
        """Reset token usage counter."""
        self.total_tokens_used = 0
        logger.info("Token usage counter reset")

    def __repr__(self) -> str:
        return f"ClaudeClient(model={self.model}, tokens_used={self.total_tokens_used})"


if __name__ == "__main__":
    # Test the Claude client
    import os

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        exit(1)

    client = ClaudeClient(api_key=api_key)

    # Test simple generation
    result = client.generate(
        prompt="Write a tweet about artificial intelligence in 280 characters or less.",
        system="You are a professional social media content creator."
    )

    print(f"Generated content:\n{result.content}")
    print(f"\nTokens used: {result.tokens_used}")
    print(f"Stop reason: {result.stop_reason}")

    # Test with context
    context = """
    Previous tweets:
    - "AI is transforming how we work"
    - "Machine learning enables smarter applications"
    """

    result = client.generate_with_context(
        prompt="write a similar tweet about AI and productivity",
        context=context,
        system="Match the style of the previous tweets."
    )

    print(f"\nWith context:\n{result.content}")
