"""Base LLM provider abstraction."""

from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, messages: list[dict], temperature: float = 0.1) -> str:
        """Generate a response from the LLM using chat-style messages."""
        raise NotImplementedError
