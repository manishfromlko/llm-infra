"""
Token extraction from vLLM responses.

Parses token counts from OpenAI-compatible vLLM response format.
"""
from typing import Dict, Any
from .langfuse_schema import TokenUsage


def extract_tokens_from_response(response: Dict[str, Any]) -> TokenUsage:
    """
    Extract token usage from vLLM response.
    
    Expected vLLM response format (OpenAI-compatible):
    {
        "id": "request-id",
        "object": "text_completion",
        "created": 1234567890,
        "model": "mistral-7b-instruct",
        "choices": [...],
        "usage": {
            "prompt_tokens": 42,
            "completion_tokens": 18,
            "total_tokens": 60
        }
    }
    
    Args:
        response: vLLM response dictionary
    
    Returns:
        TokenUsage object with prompt/completion/total token counts
    
    Raises:
        ValueError: If usage field missing or invalid
    """
    usage = response.get("usage")
    if not usage:
        raise ValueError("vLLM response missing 'usage' field")
    
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)
    
    # Validate counts are non-negative
    if not isinstance(prompt_tokens, int) or prompt_tokens < 0:
        raise ValueError(f"Invalid prompt_tokens: {prompt_tokens}")
    if not isinstance(completion_tokens, int) or completion_tokens < 0:
        raise ValueError(f"Invalid completion_tokens: {completion_tokens}")
    if not isinstance(total_tokens, int) or total_tokens < 0:
        raise ValueError(f"Invalid total_tokens: {total_tokens}")
    
    return TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


def extract_tokens_or_default(response: Dict[str, Any], default_value: int = 0) -> TokenUsage:
    """
    Extract tokens with fallback to default value if not available.
    
    Args:
        response: vLLM response dictionary
        default_value: Default value for missing token counts
    
    Returns:
        TokenUsage object
    """
    try:
        return extract_tokens_from_response(response)
    except (ValueError, KeyError, TypeError):
        # If extraction fails, return zero counts
        return TokenUsage(
            prompt_tokens=default_value,
            completion_tokens=default_value,
            total_tokens=default_value,
        )


__all__ = [
    "extract_tokens_from_response",
    "extract_tokens_or_default",
]
