"""
Unit tests for correlation ID generation and validation.
"""
import pytest
import uuid as uuid_module
from litellm.config.correlation_id import (
    generate_correlation_id,
    validate_correlation_id,
    ensure_correlation_id,
)


class TestCorrelationIDGeneration:
    """Test correlation ID generation."""
    
    def test_generate_correlation_id_returns_uuid(self):
        """Generated correlation ID is valid UUID v4."""
        correlation_id = generate_correlation_id()
        
        # Should be parseable as UUID
        parsed = uuid_module.UUID(correlation_id)
        assert str(parsed) == correlation_id
    
    def test_generated_ids_are_unique(self):
        """Generated correlation IDs are unique."""
        id1 = generate_correlation_id()
        id2 = generate_correlation_id()
        
        assert id1 != id2
    
    def test_generated_ids_are_strings(self):
        """Generated correlation IDs are strings."""
        correlation_id = generate_correlation_id()
        assert isinstance(correlation_id, str)


class TestCorrelationIDValidation:
    """Test correlation ID validation."""
    
    def test_validate_valid_uuid(self):
        """Valid UUID passes validation."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        
        result = validate_correlation_id(valid_uuid)
        assert result == valid_uuid
    
    def test_validate_none_generates_new_id(self):
        """None generates a new correlation ID."""
        result = validate_correlation_id(None)
        
        # Should be a valid UUID
        uuid_module.UUID(result)
    
    def test_validate_empty_string_generates_new_id(self):
        """Empty string generates a new correlation ID."""
        result = validate_correlation_id("")
        
        # Should be a valid UUID
        uuid_module.UUID(result)
    
    def test_validate_invalid_uuid_raises_error(self):
        """Invalid UUID raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_correlation_id("not-a-uuid")
        
        assert "Invalid correlation ID format" in str(exc_info.value)


class TestCorrelationIDEnsure:
    """Test ensure_correlation_id (permissive variant)."""
    
    def test_ensure_valid_uuid(self):
        """Valid UUID is returned unchanged."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        
        result = ensure_correlation_id(valid_uuid)
        assert result == valid_uuid
    
    def test_ensure_none_generates_id(self):
        """None generates new ID instead of raising."""
        result = ensure_correlation_id(None)
        
        # Should be a valid UUID
        uuid_module.UUID(result)
    
    def test_ensure_invalid_uuid_generates_new_id(self):
        """Invalid UUID generates new ID instead of raising."""
        result = ensure_correlation_id("not-a-uuid")
        
        # Should be a valid UUID (not the invalid input)
        uuid_module.UUID(result)
        assert result != "not-a-uuid"
