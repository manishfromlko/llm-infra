"""
LiteLLM Langfuse callback executor.

Main async callback invoked after LiteLLM receives response from vLLM.
"""
import asyncio
import json
import hashlib
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .langfuse_schema import (
    TokenUsage,
    LangfuseTraceRequest,
    TraceMetadata,
    LatencyBreakdown,
)
from .token_extractor import extract_tokens_or_default
from .latency_tracker import calculate_latency_breakdown
from .trace_client import TraceClient
from .trace_buffer import TraceBuffer
from .metadata_extractor import extract_metadata_from_headers
from .correlation_id import ensure_correlation_id


logger = logging.getLogger(__name__)


class LiteLLMCallback:
    """Executor for LiteLLM Langfuse tracing callback."""
    
    def __init__(
        self,
        trace_client: TraceClient,
        trace_buffer: TraceBuffer,
        skip_buffer_on_failure: bool = False,
    ):
        """
        Initialize callback executor.
        
        Args:
            trace_client: TraceClient instance
            trace_buffer: TraceBuffer instance
            skip_buffer_on_failure: If True, skip buffering on failure
        """
        self.trace_client = trace_client
        self.trace_buffer = trace_buffer
        self.skip_buffer_on_failure = skip_buffer_on_failure
    
    async def __call__(
        self,
        kwargs: Dict[str, Any],
        response: Dict[str, Any],
        start_time: float,
        end_time: float,
    ) -> None:
        """
        Main callback invoked after vLLM response.
        
        Args:
            kwargs: Original request parameters including metadata
            response: vLLM response dict (OpenAI format)
            start_time: Unix timestamp when request was received
            end_time: Unix timestamp when response was received
        """
        try:
            # Extract trace data
            trace = await self._build_trace(kwargs, response, start_time, end_time)
            
            # Attempt submission
            success, error = await self.trace_client.submit_trace(trace)
            
            if success:
                logger.info(f"Trace submitted: {trace['trace_id']}")
            else:
                logger.warning(f"Trace submission failed: {error}")
                if not self.skip_buffer_on_failure:
                    self.trace_buffer.buffer_trace(trace)
        
        except Exception as e:
            logger.error(f"Callback error: {e}", exc_info=True)
    
    async def _build_trace(
        self,
        kwargs: Dict[str, Any],
        response: Dict[str, Any],
        start_time: float,
        end_time: float,
    ) -> Dict[str, Any]:
        """Build trace dictionary from request/response."""
        
        # Extract metadata
        metadata = kwargs.get('metadata', {})
        team_id = metadata.get('team_id', 'unknown')
        user_id = metadata.get('user_id', 'unknown')
        api_key = metadata.get('api_key', 'unknown')
        correlation_id = metadata.get('correlation_id', '')
        use_case = metadata.get('use_case')
        
        # Ensure correlation ID
        correlation_id = ensure_correlation_id(correlation_id)
        
        # Extract tokens
        tokens = extract_tokens_or_default(response)
        
        # Calculate latency
        latency = calculate_latency_breakdown(start_time, end_time)
        
        # Extract model
        model = kwargs.get('model', response.get('model', 'unknown'))
        
        # Build trace
        trace = {
            'trace_id': correlation_id,
            'correlation_id': correlation_id,
            'user_id': f"{team_id}|{user_id}",
            'name': 'llm_request',
            'input': {
                'prompt': self._extract_prompt(kwargs),
            },
            'output': {
                'response': self._extract_response_text(response),
                'tokens': {
                    'input': tokens.prompt_tokens,
                    'output': tokens.completion_tokens,
                    'total': tokens.total_tokens,
                },
            },
            'tokens': {
                'input': tokens.prompt_tokens,
                'output': tokens.completion_tokens,
                'total': tokens.total_tokens,
            },
            'metadata': {
                'team_id': team_id,
                'user_id': user_id,
                'api_key_hash': self._hash_api_key(api_key),
                'use_case': use_case,
                'model': model,
            },
            'latency': {
                'queue_ms': latency.queue_ms,
                'inference_ms': latency.inference_ms,
                'total_ms': latency.total_ms,
            },
            'start_time': datetime.utcfromtimestamp(start_time).isoformat() + 'Z',
            'end_time': datetime.utcfromtimestamp(end_time).isoformat() + 'Z',
            'status': 'success',
        }
        
        return trace
    
    @staticmethod
    def _extract_prompt(kwargs: Dict[str, Any]) -> str:
        """Extract prompt from request kwargs."""
        messages = kwargs.get('messages', [])
        if isinstance(messages, list) and messages:
            if isinstance(messages[-1], dict):
                return messages[-1].get('content', '')
        return ''
    
    @staticmethod
    def _extract_response_text(response: Dict[str, Any]) -> str:
        """Extract response text from vLLM response."""
        choices = response.get('choices', [])
        if isinstance(choices, list) and choices:
            if isinstance(choices[0], dict):
                return choices[0].get('text', '') or choices[0].get('message', {}).get('content', '')
        return ''
    
    @staticmethod
    def _hash_api_key(api_key: str, salt: str = "") -> str:
        """Hash API key for storage."""
        message = f"{api_key}{salt}".encode()
        return hashlib.sha256(message).hexdigest()


async def create_and_run_callback(
    kwargs: Dict[str, Any],
    response: Dict[str, Any],
    start_time: float,
    end_time: float,
    trace_client: Optional[TraceClient] = None,
    trace_buffer: Optional[TraceBuffer] = None,
) -> None:
    """
    Factory function to create and run callback.
    
    Args:
        kwargs: Request kwargs
        response: vLLM response
        start_time: Request start timestamp
        end_time: Request end timestamp
        trace_client: Optional TraceClient (created if not provided)
        trace_buffer: Optional TraceBuffer (created if not provided)
    """
    if trace_client is None:
        trace_client = TraceClient(
            langfuse_host="http://langfuse:3000",
            public_key="",
        )
    
    if trace_buffer is None:
        trace_buffer = TraceBuffer()
    
    callback = LiteLLMCallback(trace_client, trace_buffer)
    await callback(kwargs, response, start_time, end_time)


__all__ = [
    "LiteLLMCallback",
    "create_and_run_callback",
]
