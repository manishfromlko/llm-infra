"""
Langfuse trace schema definitions using Pydantic for validation.

Defines the complete trace schema that matches Langfuse API contract.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid


class TokenUsage(BaseModel):
    """Token usage information from vLLM response."""
    prompt_tokens: int = Field(..., ge=0, description="Input token count")
    completion_tokens: int = Field(..., ge=0, description="Output token count")
    total_tokens: int = Field(..., ge=0, description="Total token count")

    @validator('total_tokens')
    def validate_total_tokens(cls, v, values):
        """Validate that total equals sum of prompt and completion."""
        if 'prompt_tokens' in values and 'completion_tokens' in values:
            expected = values['prompt_tokens'] + values['completion_tokens']
            if v != expected:
                raise ValueError(f"total_tokens ({v}) must equal prompt_tokens + completion_tokens ({expected})")
        return v


class LatencyBreakdown(BaseModel):
    """Latency measurement breakdown in milliseconds."""
    queue_ms: int = Field(..., ge=0, description="Time in queue before inference")
    inference_ms: int = Field(..., ge=0, description="Model inference time")
    total_ms: int = Field(..., ge=0, description="End-to-end total latency")


class TraceMetadata(BaseModel):
    """Metadata attached to traces for cost attribution and audit."""
    team_id: str = Field(..., description="Team identifier")
    user_id: str = Field(..., description="User identifier")
    api_key_hash: str = Field(..., description="Hashed API key (never plain text)")
    use_case: Optional[str] = Field(None, description="Use case label for analytics")
    model: str = Field(..., description="Model name used for inference")


class LangfuseTraceRequest(BaseModel):
    """Complete trace schema for submission to Langfuse API."""
    trace_id: str = Field(..., description="Unique trace identifier (UUID v4)")
    correlation_id: str = Field(..., description="Client correlation ID (UUID v4)")
    user_id: str = Field(..., description="Langfuse user ID (team_id|user_id format)")
    name: str = Field(default="llm_request", description="Trace name")
    
    # Input and output
    input: Dict[str, Any] = Field(..., description="Request input (prompt)")
    output: Dict[str, Any] = Field(..., description="Response output (response, tokens)")
    
    # Tokens and latency
    tokens: TokenUsage = Field(..., description="Token usage breakdown")
    latency: LatencyBreakdown = Field(..., description="Latency breakdown")
    
    # Metadata and timestamps
    metadata: TraceMetadata = Field(..., description="Attribution and audit metadata")
    start_time: datetime = Field(..., description="Request start timestamp")
    end_time: datetime = Field(..., description="Response end timestamp")
    
    # Status
    status: str = Field(default="success", description="Trace status (success or error)")
    error: Optional[str] = Field(None, description="Error message if status=error")

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VLLMResponse(BaseModel):
    """Schema for vLLM OpenAI-compatible response."""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: TokenUsage


class TracingContext(BaseModel):
    """Context object passed through LiteLLM callback."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = Field(..., description="Correlation ID (UUID v4)")
    team_id: str = Field(..., description="Team identifier")
    user_id: str = Field(..., description="User identifier")
    api_key: str = Field(..., description="API key (will be hashed before tracing)")
    use_case: Optional[str] = Field(None, description="Use case label")
    timestamp_start: datetime = Field(..., description="Request start time")
    timestamp_end: Optional[datetime] = Field(None, description="Request end time")


__all__ = [
    "TokenUsage",
    "LatencyBreakdown",
    "TraceMetadata",
    "LangfuseTraceRequest",
    "VLLMResponse",
    "TracingContext",
]
