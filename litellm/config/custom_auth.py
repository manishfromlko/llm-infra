"""
Custom authentication for LiteLLM using file-based API key validation.
"""
import os
from typing import Optional
from fastapi import Request
from litellm.proxy._types import UserAPIKeyAuth
from .api_key_validator import APIKeyValidator


class CustomAuth:
    """Custom authentication handler for LiteLLM."""

    def __init__(self):
        self.validator = APIKeyValidator()

    async def __call__(self, request: Request, api_key: str) -> UserAPIKeyAuth:
        """
        Authenticate the API key using file-based validation.

        Args:
            request: FastAPI request object
            api_key: The API key to validate

        Returns:
            UserAPIKeyAuth object if valid, raises exception if invalid
        """
        # Validate the API key
        is_valid, error_message, key_info = self.validator.validate_api_key(api_key)

        if not is_valid:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail=f"Authentication Error, Invalid proxy server token passed. {error_message}"
            )

        # Extract headers for additional metadata
        team_id = request.headers.get("X-Team-Id")
        user_id = request.headers.get("X-User-Id")

        # Return UserAPIKeyAuth object
        return UserAPIKeyAuth(
            api_key=api_key,
            token=api_key,  # Use the plain key as token
            user_id=user_id or key_info.get("user_id"),
            team_id=team_id or key_info.get("team_id"),
            user_role="internal_user",  # Default role
            spend=0.0,
            max_budget=key_info.get("rate_limit_tokens_per_day", 1000000),
            allowed_model_region=None,
        )


# Create singleton instance
custom_auth = CustomAuth()

# Export the callable
__all__ = ["custom_auth"]