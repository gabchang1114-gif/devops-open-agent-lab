"""LLM provider exceptions."""


class LLMProviderError(Exception):
    """Base exception for LLM provider failures."""


class LLMAuthenticationError(LLMProviderError):
    """Raised when API authentication fails."""


class LLMRateLimitError(LLMProviderError):
    """Raised when the provider rate limit is exceeded."""


class LLMTimeoutError(LLMProviderError):
    """Raised when an LLM request times out."""


class LLMMalformedResponseError(LLMProviderError):
    """Raised when the provider returns an unexpected response."""
