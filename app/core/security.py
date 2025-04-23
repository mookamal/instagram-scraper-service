# app/core/security.py
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from .config import settings # Import the settings instance

# Define the header name we expect the API key in
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key_header: str | None = Security(API_KEY_HEADER)):
    """
    Dependency function to verify the provided API key.
    Checks if the key from the 'X-API-Key' header is in the allowed set.
    """
    # Check if any keys are configured at all
    if not settings.ALLOWED_API_KEYS:
        # If no keys are configured, perhaps allow access or log a warning.
        # For this example, we'll still require a key if the header exists,
        # but won't raise an error if no keys are defined and no header is sent.
        # If strict security is needed even with no keys defined, raise error here.
        # print("Security Warning: No API keys configured, but proceeding.") # Optional warning
        pass # Allow request if no keys are set up and no key provided

    # If keys are configured, a valid key must be provided
    if settings.ALLOWED_API_KEYS:
        if api_key_header is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing API Key. Provide 'X-API-Key' header.",
            )
        if api_key_header not in settings.ALLOWED_API_KEYS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API Key.",
            )
    # If the key is valid (or no keys are required and none was provided), return it (optional)
    # You could return the key if you need to use it later, e.g., for rate limiting per key
    # return api_key_header