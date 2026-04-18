"""
Contract tests for Langfuse trace schema validation.

Tests verify that traces conform to Langfuse API contract.
"""
import pytest
from datetime import datetime
from litellm.config.langfuse_schema import (
    TokenUsage,
    LatencyBreakdown,
    TraceMetadata,
    LangfuseTraceRequest,
)


class TestTokenUsageSchema:
    """Test TokenUsage validation."""
    
    def test_valid_token_usage(self):
        """Valid token usage object."""
        usage = TokenUsage(
            prompt_tokens=42,
            completion_tokens=18,
            total_tokens=60,
        )
        assert usage.prompt_tokens == 42
        assert usage.completion_tokens == 18
        assert usage.total_tokens == 60
    
    def test_invalid_total_tokens_sum(self):
        """Total tokens must equal prompt + completion."""
        with pytest.raises(ValueError):
            TokenUsage(
                prompt_tokens=42,
                completion_tokens=18,
                total_tokens=99,  # Should be 60
            )
    
    def test_negative_tokens_rejected(self):
        """Token counts must be non-negative."""
        with pytest.raises(ValueError):
            TokenUsage(
                prompt_tokens=-1,
                completion_tokens=18,
                total_tokens=17,
            )


class TestLatencyBreakdownSchema:
    """Test LatencyBreakdown validation."""
    
    def test_valid_latency(self):
        """Valid latency breakdown."""
        latency = LatencyBreakdown(
            queue_ms=10,
            inference_ms=850,
            total_ms=860,
        )
        assert latency.queue_ms == 10
        assert latency.inference_ms == 850
        assert latency.total_ms == 860
    
    def test_negative_latency_rejected(self):
        """Latency values must be non-negative."""
        with pytest.raises(ValueError):
            LatencyBreakdown(
                queue_ms=-10,
                inference_ms=850,
                total_ms=840,
            )


class TestTraceMetadataSchema:
    """Test TraceMetadata validation."""
    
    def test_valid_metadata_with_use_case(self):
        """Valid metadata with optional use_case."""
        metadata = TraceMetadata(
            team_id="acme-corp",
            user_id="user-42",
            api_key_hash="sha256:abc123",
            use_case="email-generation",
            model="mistral-7b-instruct",
        )
        assert metadata.team_id == "acme-corp"
        assert metadata.use_case == "email-generation"
    
    def test_valid_metadata_without_use_case(self):
        """Valid metadata without optional use_case."""
        metadata = TraceMetadata(
            team_id="acme-corp",
            user_id="user-42",
            api_key_hash="sha256:abc123",
            model="mistral-7b-instruct",
        )
        assert metadata.use_case is None


class TestLangfuseTraceSchema:
    """Test complete LangfuseTraceRequest schema."""
    
    def test_valid_complete_trace(self):
        """Valid complete trace object."""
        now = datetime.utcnow()
        trace = LangfuseTraceRequest(
            trace_id="550e8400-e29b-41d4-a716-446655440000",
            correlation_id="550e8400-e29b-41d4-a716-446655440000",
            user_id="acme-corp|user-42",
            name="llm_request",
            input={"prompt": "What is the capital of France?"},
            output={
                "response": "Paris",
                "tokens": {"input": 11, "output": 1, "total": 12},
            },
            tokens=TokenUsage(
                prompt_tokens=11,
                completion_tokens=1,
                total_tokens=12,
            ),
            latency=LatencyBreakdown(
                queue_ms=10,
                inference_ms=100,
                total_ms=110,
            ),
            metadata=TraceMetadata(
                team_id="acme-corp",
                user_id="user-42",
                api_key_hash="sha256:abc123",
                model="mistral-7b-instruct",
            ),
            start_time=now,
            end_time=now,
        )
        assert trace.trace_id == "550e8400-e29b-41d4-a716-446655440000"
        assert trace.status == "success"
    
    def test_trace_with_error_status(self):
        """Trace with error status."""
        now = datetime.utcnow()
        trace = LangfuseTraceRequest(
            trace_id="550e8400-e29b-41d4-a716-446655440000",
            correlation_id="550e8400-e29b-41d4-a716-446655440000",
            user_id="acme-corp|user-42",
            input={"prompt": "test"},
            output={},
            tokens=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            latency=LatencyBreakdown(queue_ms=0, inference_ms=0, total_ms=0),
            metadata=TraceMetadata(
                team_id="acme-corp",
                user_id="user-42",
                api_key_hash="sha256:abc123",
                model="mistral-7b-instruct",
            ),
            start_time=now,
            end_time=now,
            status="error",
            error="Model inference timeout",
        )
        assert trace.status == "error"
        assert trace.error == "Model inference timeout"
    
    def test_trace_json_serialization(self):
        """Trace can be serialized to JSON."""
        now = datetime.utcnow()
        trace = LangfuseTraceRequest(
            trace_id="550e8400-e29b-41d4-a716-446655440000",
            correlation_id="550e8400-e29b-41d4-a716-446655440000",
            user_id="acme-corp|user-42",
            input={"prompt": "test"},
            output={"response": "success"},
            tokens=TokenUsage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
            latency=LatencyBreakdown(queue_ms=10, inference_ms=100, total_ms=110),
            metadata=TraceMetadata(
                team_id="acme-corp",
                user_id="user-42",
                api_key_hash="sha256:abc123",
                model="mistral-7b-instruct",
            ),
            start_time=now,
            end_time=now,
        )
        
        # Should serialize to JSON without errors
        json_str = trace.json()
        assert isinstance(json_str, str)
        assert "acme-corp" in json_str
