"""
Unit tests for metadata extraction from headers.
"""
import pytest
from litellm.config.metadata_extractor import (
    extract_metadata_from_headers,
    validate_metadata_headers,
    MetadataExtractionError,
)


class TestMetadataExtraction:
    """Test metadata extraction from HTTP headers."""
    
    def test_extract_all_required_headers(self):
        """Extract all required metadata headers."""
        headers = {
            "X-Team-Id": "acme-corp",
            "X-User-Id": "user-42",
            "X-Api-Key": "sk-xxx-yyy-zzz",
            "X-Correlation-Id": "550e8400-e29b-41d4-a716-446655440000",
            "X-Use-Case": "email-generation",
        }
        
        metadata = extract_metadata_from_headers(headers)
        
        assert metadata["team_id"] == "acme-corp"
        assert metadata["user_id"] == "user-42"
        assert metadata["api_key"] == "sk-xxx-yyy-zzz"
        assert metadata["correlation_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert metadata["use_case"] == "email-generation"
    
    def test_extract_required_headers_only(self):
        """Extract with only required headers (no optional)."""
        headers = {
            "X-Team-Id": "acme-corp",
            "X-User-Id": "user-42",
            "X-Api-Key": "sk-xxx-yyy-zzz",
        }
        
        metadata = extract_metadata_from_headers(headers)
        
        assert metadata["team_id"] == "acme-corp"
        assert metadata["correlation_id"] is None
        assert metadata["use_case"] is None
    
    def test_missing_required_team_id(self):
        """Missing X-Team-Id raises error."""
        headers = {
            "X-User-Id": "user-42",
            "X-Api-Key": "sk-xxx-yyy-zzz",
        }
        
        with pytest.raises(MetadataExtractionError) as exc_info:
            extract_metadata_from_headers(headers)
        
        assert "X-Team-Id" in str(exc_info.value)
    
    def test_missing_required_user_id(self):
        """Missing X-User-Id raises error."""
        headers = {
            "X-Team-Id": "acme-corp",
            "X-Api-Key": "sk-xxx-yyy-zzz",
        }
        
        with pytest.raises(MetadataExtractionError) as exc_info:
            extract_metadata_from_headers(headers)
        
        assert "X-User-Id" in str(exc_info.value)
    
    def test_missing_required_api_key(self):
        """Missing X-Api-Key raises error."""
        headers = {
            "X-Team-Id": "acme-corp",
            "X-User-Id": "user-42",
        }
        
        with pytest.raises(MetadataExtractionError) as exc_info:
            extract_metadata_from_headers(headers)
        
        assert "X-Api-Key" in str(exc_info.value)
    
    def test_case_insensitive_header_lookup(self):
        """Header lookup is case-insensitive."""
        headers = {
            "x-team-id": "acme-corp",
            "X-USER-ID": "user-42",
            "x-api-key": "sk-xxx-yyy-zzz",
        }
        
        metadata = extract_metadata_from_headers(headers)
        assert metadata["team_id"] == "acme-corp"
    
    def test_invalid_team_id_format(self):
        """Invalid team_id format raises error."""
        headers = {
            "X-Team-Id": "invalid@team#id",  # Contains invalid characters
            "X-User-Id": "user-42",
            "X-Api-Key": "sk-xxx-yyy-zzz",
        }
        
        with pytest.raises(MetadataExtractionError) as exc_info:
            extract_metadata_from_headers(headers)
        
        assert "format" in str(exc_info.value).lower()


class TestMetadataValidation:
    """Test metadata header validation."""
    
    def test_validate_valid_headers(self):
        """Validate returns True for valid headers."""
        headers = {
            "X-Team-Id": "acme-corp",
            "X-User-Id": "user-42",
            "X-Api-Key": "sk-xxx-yyy-zzz",
        }
        
        is_valid, error = validate_metadata_headers(headers)
        assert is_valid is True
        assert error is None
    
    def test_validate_invalid_headers(self):
        """Validate returns False and error message for invalid headers."""
        headers = {
            "X-Team-Id": "acme-corp",
            # Missing required headers
        }
        
        is_valid, error = validate_metadata_headers(headers)
        assert is_valid is False
        assert error is not None
