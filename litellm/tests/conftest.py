"""Pytest configuration and fixtures."""
import pytest
import sys
from pathlib import Path

# Add litellm package to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_headers():
    """Sample HTTP headers for testing."""
    return {
        "X-Team-Id": "acme-corp",
        "X-User-Id": "user-42",
        "X-Api-Key": "sk-test-key",
        "X-Correlation-Id": "550e8400-e29b-41d4-a716-446655440000",
        "X-Use-Case": "testing",
    }


@pytest.fixture
def sample_vllm_response():
    """Sample vLLM response for testing."""
    return {
        "id": "request-123",
        "object": "text_completion",
        "created": 1234567890,
        "model": "mistral-7b-instruct",
        "choices": [
            {
                "index": 0,
                "text": "This is the response.",
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 42,
            "completion_tokens": 18,
            "total_tokens": 60,
        },
    }


@pytest.fixture
def sample_langfuse_trace():
    """Sample Langfuse trace for testing."""
    return {
        "trace_id": "550e8400-e29b-41d4-a716-446655440000",
        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "acme-corp|user-42",
        "name": "llm_request",
        "input": {
            "prompt": "What is the capital of France?",
        },
        "output": {
            "response": "Paris is the capital of France.",
            "tokens": {
                "input": 11,
                "output": 8,
                "total": 19,
            },
        },
        "tokens": {
            "input": 11,
            "output": 8,
            "total": 19,
        },
        "metadata": {
            "team_id": "acme-corp",
            "user_id": "user-42",
            "api_key_hash": "sha256:abc123",
            "model": "mistral-7b-instruct",
        },
        "latency": {
            "queue_ms": 10,
            "inference_ms": 850,
            "total_ms": 860,
        },
        "start_time": "2026-04-18T10:30:00Z",
        "end_time": "2026-04-18T10:30:00.860Z",
        "status": "success",
    }
