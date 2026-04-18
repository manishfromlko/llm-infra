"""
API key validation and authentication.

Validates API keys against stored credentials and checks status.
"""
import hashlib
import json
import os
from typing import Dict, Optional, Tuple


class APIKeyValidator:
    """Validates API keys against stored credentials."""
    
    def __init__(self, api_keys_file: Optional[str] = None):
        """
        Initialize validator.
        
        Args:
            api_keys_file: Path to JSON file containing API key hashes
        """
        self.api_keys_file = api_keys_file or os.getenv(
            'API_KEYS_FILE',
            '/app/config/api_keys.json'
        )
        self.api_keys_cache = {}
        self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from file."""
        try:
            if os.path.exists(self.api_keys_file):
                with open(self.api_keys_file, 'r') as f:
                    self.api_keys_cache = json.load(f)
        except Exception as e:
            # Log error but don't fail initialization
            self.api_keys_cache = {}
    
    @staticmethod
    def hash_api_key(api_key: str, salt: str = "") -> str:
        """
        Hash an API key using SHA-256.
        
        Args:
            api_key: Plain text API key
            salt: Optional salt for hashing
        
        Returns:
            Hex string of SHA-256 hash
        """
        message = f"{api_key}{salt}".encode()
        return hashlib.sha256(message).hexdigest()
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Validate an API key.
        
        Args:
            api_key: API key to validate
        
        Returns:
            Tuple of (is_valid, error_message, key_info_dict)
            key_info_dict contains: team_id, user_id, status, rate_limits
        """
        if not api_key or not isinstance(api_key, str):
            return False, "Invalid API key format", None
        
        # Hash the provided key
        key_hash = self.hash_api_key(api_key)
        
        # Check if hash exists in cache
        if key_hash not in self.api_keys_cache:
            return False, "API key not found", None
        
        key_info = self.api_keys_cache[key_hash]
        
        # Check status
        if key_info.get('status') != 'active':
            return False, f"API key status: {key_info.get('status')}", None
        
        return True, None, key_info
    
    def get_key_info(self, api_key: str) -> Optional[Dict]:
        """
        Get information about an API key.
        
        Args:
            api_key: API key
        
        Returns:
            Dictionary with key info or None if invalid
        """
        is_valid, _, key_info = self.validate_api_key(api_key)
        return key_info if is_valid else None


def create_sample_api_keys() -> Dict[str, Dict]:
    """
    Create sample API keys for testing.
    
    Returns:
        Dictionary mapping key hashes to key info
    """
    sample_keys = {}
    
    # Sample key 1
    key1 = "sk-test-key-team1-user1-12345"
    hash1 = APIKeyValidator.hash_api_key(key1)
    sample_keys[hash1] = {
        "key_id": "key-001",
        "team_id": "team-1",
        "user_id": "user-1",
        "status": "active",
        "created_at": "2026-04-18T10:00:00Z",
        "rate_limit_rpm": 1000,
        "rate_limit_tokens_per_day": 1000000,
    }
    
    # Sample key 2
    key2 = "sk-test-key-team2-user1-67890"
    hash2 = APIKeyValidator.hash_api_key(key2)
    sample_keys[hash2] = {
        "key_id": "key-002",
        "team_id": "team-2",
        "user_id": "user-1",
        "status": "active",
        "created_at": "2026-04-18T10:00:00Z",
        "rate_limit_rpm": 500,
        "rate_limit_tokens_per_day": 500000,
    }
    
    return sample_keys


__all__ = [
    "APIKeyValidator",
    "create_sample_api_keys",
]
