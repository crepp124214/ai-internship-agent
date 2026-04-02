"""LLM-related exceptions."""


class LLMProviderError(ValueError):
    """Raised when an LLM provider cannot be resolved."""


class LLMConfigurationError(LLMProviderError):
    """Raised when provider configuration is invalid or incomplete."""


class LLMRequestError(RuntimeError):
    """Raised when an LLM request fails."""


class LLMRetryableError(RuntimeError):
    """Raised for transient/retryable LLM errors (temporary failures)."""


class CircuitBreakerOpenError(RuntimeError):
    """Raised when a circuit breaker is OPEN and requests are blocked."""
