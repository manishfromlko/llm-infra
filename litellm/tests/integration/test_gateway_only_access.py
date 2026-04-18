"""
Integration tests for gateway-only access control.

Verifies direct vLLM access is blocked and routing enforced.
"""
import pytest


class TestGatewayOnlyAccess:
    """Test gateway-only access enforcement."""
    
    def test_direct_vllm_access_blocked(self):
        """Direct vLLM requests are rejected."""
        pytest.skip("Implementation pending")
    
    def test_requests_require_api_key(self):
        """Requests without API key are rejected."""
        pytest.skip("Implementation pending")
    
    def test_invalid_api_key_rejected(self):
        """Requests with invalid API key are rejected."""
        pytest.skip("Implementation pending")
    
    def test_litellm_routing_enforced(self):
        """All requests must route through LiteLLM."""
        pytest.skip("Implementation pending")
