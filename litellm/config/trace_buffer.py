"""
Trace buffering with file-based persistence.

Buffers failed traces to disk in JSONL format for async retry.
"""
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import time


class TraceBuffer:
    """Manages buffered traces using JSONL file format."""
    
    def __init__(
        self,
        buffer_dir: str = "/app/data/trace_buffer",
        max_size_mb: int = 100,
    ):
        """
        Initialize trace buffer.
        
        Args:
            buffer_dir: Directory to store buffer files
            max_size_mb: Maximum buffer size in MB before cleanup
        """
        self.buffer_dir = buffer_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.buffer_file = os.path.join(buffer_dir, "trace_buffer.jsonl")
        self._ensure_buffer_dir()
    
    def _ensure_buffer_dir(self):
        """Ensure buffer directory exists."""
        os.makedirs(self.buffer_dir, exist_ok=True)
    
    def buffer_trace(self, trace: Dict[str, Any], retry_count: int = 0) -> bool:
        """
        Buffer a trace to disk.
        
        Args:
            trace: Trace dictionary
            retry_count: Number of previous retry attempts
        
        Returns:
            True if buffered successfully, False if buffer full
        """
        # Check buffer size
        current_size = self._get_buffer_size()
        if current_size >= self.max_size_bytes:
            # Buffer is full, drop oldest entries
            self._cleanup_buffer()
        
        # Create buffer entry
        entry = {
            "buffered_at": datetime.utcnow().isoformat() + "Z",
            "trace": trace,
            "retry_count": retry_count,
            "next_retry_at": (datetime.utcnow() + timedelta(seconds=60 * (2 ** retry_count))).isoformat() + "Z",
        }
        
        # Append to JSONL file
        try:
            with open(self.buffer_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
            return True
        except Exception as e:
            # Log error but don't crash
            print(f"Error writing to trace buffer: {e}")
            return False
    
    def read_buffered_traces(self) -> List[Dict[str, Any]]:
        """
        Read all buffered traces.
        
        Returns:
            List of buffer entry dictionaries
        """
        traces = []
        
        if not os.path.exists(self.buffer_file):
            return traces
        
        try:
            with open(self.buffer_file, 'r') as f:
                for line in f:
                    if line.strip():
                        traces.append(json.loads(line))
        except Exception as e:
            print(f"Error reading trace buffer: {e}")
        
        return traces
    
    def remove_buffered_trace(self, trace_id: str):
        """
        Remove a trace from buffer after successful submission.
        
        Args:
            trace_id: Trace ID to remove
        """
        try:
            traces = self.read_buffered_traces()
            with open(self.buffer_file, 'w') as f:
                for entry in traces:
                    if entry.get('trace', {}).get('trace_id') != trace_id:
                        f.write(json.dumps(entry) + '\n')
        except Exception as e:
            print(f"Error removing trace from buffer: {e}")
    
    def clear_buffer(self):
        """Clear all buffered traces."""
        try:
            if os.path.exists(self.buffer_file):
                os.remove(self.buffer_file)
        except Exception as e:
            print(f"Error clearing buffer: {e}")
    
    def _get_buffer_size(self) -> int:
        """Get current buffer file size in bytes."""
        if not os.path.exists(self.buffer_file):
            return 0
        return os.path.getsize(self.buffer_file)
    
    def _cleanup_buffer(self):
        """Remove oldest entries if buffer exceeds size limit."""
        try:
            traces = self.read_buffered_traces()
            
            # Keep only newest traces
            target_size = self.max_size_bytes // 2
            current_size = 0
            new_traces = []
            
            for entry in reversed(traces):
                entry_str = json.dumps(entry) + '\n'
                if current_size + len(entry_str.encode()) <= target_size:
                    new_traces.append(entry)
                    current_size += len(entry_str.encode())
            
            # Write back kept traces
            new_traces.reverse()
            with open(self.buffer_file, 'w') as f:
                for entry in new_traces:
                    f.write(json.dumps(entry) + '\n')
        
        except Exception as e:
            print(f"Error during buffer cleanup: {e}")


__all__ = [
    "TraceBuffer",
]
