"""
Contract tests for API key validation.

Tests verify API key authentication contract.
"""
import pytest
from litellm.config.api_key_validator import APIKeyValidator, create_sample_api_keys


class TestAPIKeyValidator:
    """Test API key validation contract."""
    
    def test_valid_api_key(self):
        """Valid API key passes validation."""
        sample_keys = create_sample_api_keys()
        
        # Create validator with sample keys
        validator = APIKeyValidator()
        validator.api_keys_cache = sample_keys
        
        # Use the first sample key
        test_key = "sk-test-key-team1-user1-12345"
        is_valid, error, key_info = validator.validate_api_key(test_key)
        
        assert is_valid is True
        assert error is None
        assert key_info is not None
        assert key_info["team_id"] == "team-1"
    
    def test_invalid_api_key(self):
        """Invalid API key fails validation."""
        validator = APIKeyValidator()
        validator.api_keys_cache = {}
        
        is_valid, error, key_info = validator.validate_api_key("invalid-key")
        
        assert is_valid is False
        assert error is not None
        assert key_info is None
    
    def test_empty_api_key(self):
        """Empty API key fails validation."""
        validator = APIKeyValidator()
        
        is_valid, error, key_info = validator.validate_api_key("")
        
        assert is_valid is False
        assert "Invalid API key format" in error
    
    def test_api_key_hashing_consistency(self):
        """API key hashing is consistent."""
        test_key = "sk-test-key-123"
        hash1 = APIKeyValidator.hash_api_key(test_key)
        hash2 = APIKeyValidator.hash_api_key(test_key)
        
        assert hash1 == hash2
    
    def test_sample_api_keys_creation(self):
        """Sample API keys created with required fields."""
        sample_keys = create_sample_api_keys()
        
        assert len(sample_keys) >= 2
        
        for key_hash, key_info in sample_keys.items():
            assert "team_id" in key_info
            assert "user_id" in key_info
            assert "status" in key_info
            assert key_info["status"] == "active"
