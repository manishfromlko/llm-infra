"""
Trace submission client with retry logic.

Submits traces to Langfuse API with exponential backoff retry strategy.
"""
import httpx
import asyncio
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import random


class TraceSubmissionError(Exception):
    """Raised when trace submission fails."""
    pass


class TraceClient:
    """HTTP client for submitting traces to Langfuse."""
    
    def __init__(
        self,
        langfuse_host: str,
        public_key: str,
        secret_key: str,
        timeout: int = 5,
        max_retries: int = 3,
    ):
        """
        Initialize trace client.
        
        Args:
            langfuse_host: Langfuse API host URL (e.g., http://langfuse:3000)
            public_key: Langfuse public key for authentication
            secret_key: Langfuse secret key (for future use)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.langfuse_host = langfuse_host.rstrip('/')
        self.public_key = public_key
        self.secret_key = secret_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.endpoint = f"{self.langfuse_host}/api/public/traces"
    
    async def submit_trace(self, trace: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Submit a trace to Langfuse with retries.
        
        Args:
            trace: Trace dictionary matching Langfuse schema
        
        Returns:
            Tuple of (success, error_message)
        """
        headers = {
            "Authorization": f"Bearer {self.public_key}",
            "Content-Type": "application/json",
        }
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.endpoint,
                        json=trace,
                        headers=headers,
                    )
                    
                    if response.status_code == 200:
                        return True, None
                    elif response.status_code in (503, 502):
                        # Service unavailable, retry
                        if attempt < self.max_retries - 1:
                            await self._wait_with_backoff(attempt)
                            continue
                        else:
                            return False, f"Langfuse unavailable after {self.max_retries} attempts"
                    elif response.status_code == 400:
                        # Client error, don't retry
                        return False, f"Invalid trace schema: {response.text}"
                    elif response.status_code == 401:
                        # Auth error, don't retry
                        return False, "Invalid Langfuse credentials"
                    else:
                        return False, f"HTTP {response.status_code}: {response.text}"
            
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    await self._wait_with_backoff(attempt)
                    continue
                else:
                    return False, "Request timeout after all retries"
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await self._wait_with_backoff(attempt)
                    continue
                else:
                    return False, f"Request failed: {str(e)}"
        
        return False, "All retry attempts exhausted"
    
    async def _wait_with_backoff(self, attempt: int):
        """
        Wait with exponential backoff + jitter.
        
        Backoff schedule: 100ms, 200ms, 400ms (+ jitter)
        
        Args:
            attempt: Attempt number (0-indexed)
        """
        base_delay_ms = 100 * (2 ** attempt)  # 100ms, 200ms, 400ms
        jitter_ms = random.randint(0, base_delay_ms // 2)  # 0 to 50ms jitter
        total_delay_ms = base_delay_ms + jitter_ms
        await asyncio.sleep(total_delay_ms / 1000.0)
    
    def submit_trace_sync(self, trace: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Synchronous wrapper for trace submission.
        
        Args:
            trace: Trace dictionary
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.submit_trace(trace))


__all__ = [
    "TraceClient",
    "TraceSubmissionError",
]
