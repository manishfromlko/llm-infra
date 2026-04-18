"""
Integration tests for end-to-end request tracing.

Tests complete flow from client request through LiteLLM to Langfuse trace submission.
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from litellm.config.litellm_langfuse_callback import LiteLLMCallback
from litellm.config.trace_client import TraceClient
from litellm.config.trace_buffer import TraceBuffer
from litellm.config.langfuse_schema import LangfuseTraceRequest


class TestE2ERequestTracing:
    """End-to-end integration tests for request tracing."""
    
    @pytest.fixture
    def mock_trace_client(self):
        """Create a mock trace client."""
        client = AsyncMock(spec=TraceClient)
        client.submit_trace.return_value = (True, None)
        return client
    
    @pytest.fixture
    def mock_trace_buffer(self, tmp_path):
        """Create a trace buffer with temp directory."""
        return TraceBuffer(buffer_dir=str(tmp_path))
    
    @pytest.fixture
    def callback(self, mock_trace_client, mock_trace_buffer):
        """Create callback instance."""
        return LiteLLMCallback(mock_trace_client, mock_trace_buffer)
    
    @pytest.mark.asyncio
    async def test_successful_trace_submission(self, callback, mock_trace_client):
        """Successful trace submission to Langfuse."""
        now = datetime.utcnow()
        start_time = now.timestamp()
        end_time = (now).timestamp() + 1.0
        
        kwargs = {
            "model": "mistral-7b-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": "What is the capital of France?",
                }
            ],
            "temperature": 0.7,
            "metadata": {
                "team_id": "acme-corp",
                "user_id": "user-42",
                "api_key": "sk-test-key",
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
            },
        }
        
        response = {
            "id": "request-123",
            "object": "text_completion",
            "created": int(end_time),
            "model": "mistral-7b-instruct",
            "choices": [
                {
                    "index": 0,
                    "text": "Paris is the capital of France.",
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 11,
                "completion_tokens": 8,
                "total_tokens": 19,
            },
        }
        
        # Execute callback
        await callback(kwargs, response, start_time, end_time)
        
        # Verify trace was submitted
        mock_trace_client.submit_trace.assert_called_once()
        call_args = mock_trace_client.submit_trace.call_args[0]
        trace = call_args[0]
        
        # Verify trace structure
        assert trace["trace_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert trace["metadata"]["team_id"] == "acme-corp"
        assert trace["tokens"]["input"] == 11
        assert trace["tokens"]["output"] == 8
    
    @pytest.mark.asyncio
    async def test_failed_trace_buffers_to_disk(
        self,
        callback,
        mock_trace_client,
        mock_trace_buffer,
    ):
        """Failed trace submission buffers to disk."""
        # Make submission fail
        mock_trace_client.submit_trace.return_value = (False, "Langfuse unavailable")
        
        now = datetime.utcnow()
        start_time = now.timestamp()
        end_time = (now).timestamp() + 1.0
        
        kwargs = {
            "model": "mistral-7b-instruct",
            "messages": [{"role": "user", "content": "test"}],
            "metadata": {
                "team_id": "acme-corp",
                "user_id": "user-42",
                "api_key": "sk-test-key",
            },
        }
        
        response = {
            "id": "request-123",
            "object": "text_completion",
            "created": int(end_time),
            "model": "mistral-7b-instruct",
            "choices": [{"text": "response", "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }
        
        # Execute callback
        await callback(kwargs, response, start_time, end_time)
        
        # Verify trace was buffered
        buffered = mock_trace_buffer.read_buffered_traces()
        assert len(buffered) > 0
    
    @pytest.mark.asyncio
    async def test_callback_extracts_tokens_correctly(self, callback, mock_trace_client):
        """Callback correctly extracts token counts from response."""
        now = datetime.utcnow()
        start_time = now.timestamp()
        end_time = (now).timestamp() + 1.0
        
        kwargs = {
            "model": "mistral-7b",
            "messages": [{"role": "user", "content": "test"}],
            "metadata": {
                "team_id": "team-1",
                "user_id": "user-1",
                "api_key": "sk-key",
            },
        }
        
        response = {
            "id": "req-1",
            "model": "mistral-7b",
            "choices": [{"text": "response"}],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        }
        
        await callback(kwargs, response, start_time, end_time)
        
        # Get submitted trace
        call_args = mock_trace_client.submit_trace.call_args[0]
        trace = call_args[0]
        
        assert trace["tokens"]["input"] == 100
        assert trace["tokens"]["output"] == 50
        assert trace["tokens"]["total"] == 150
    
    @pytest.mark.asyncio
    async def test_callback_generates_correlation_id_if_missing(
        self,
        callback,
        mock_trace_client,
    ):
        """Callback generates correlation ID if missing from request."""
        now = datetime.utcnow()
        start_time = now.timestamp()
        end_time = (now).timestamp() + 1.0
        
        kwargs = {
            "model": "mistral-7b",
            "messages": [{"role": "user", "content": "test"}],
            "metadata": {
                "team_id": "team-1",
                "user_id": "user-1",
                "api_key": "sk-key",
                # No correlation_id
            },
        }
        
        response = {
            "id": "req-1",
            "model": "mistral-7b",
            "choices": [{"text": "response"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
        }
        
        await callback(kwargs, response, start_time, end_time)
        
        # Get submitted trace
        call_args = mock_trace_client.submit_trace.call_args[0]
        trace = call_args[0]
        
        # Should have generated a correlation ID
        assert "trace_id" in trace
        assert trace["trace_id"] != ""
