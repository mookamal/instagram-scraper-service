# app/core/config.py
import os
from pydantic_settings import BaseSettings
from typing import Set

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """
    # Load API keys from .env, split by comma, strip whitespace, filter empty
    ALLOWED_API_KEYS: Set[str] = set(
        key.strip() for key in os.getenv("ALLOWED_API_KEYS", "").split(',') if key.strip()
    )
    SCRAPER_HEADLESS: bool = os.getenv("SCRAPER_HEADLESS", 'True').lower() in ('true', '1', 't')

    class Config:
        # Specifies the .env file to load variables from
        env_file = ".env"
        env_file_encoding = 'utf-8'
        # Allows setting case-insensitive environment variables if needed
        # case_sensitive = False

# Create a single instance of settings to be imported elsewhere
settings = Settings()

# Basic validation on load
if not settings.ALLOWED_API_KEYS:
    print("WARNING: No ALLOWED_API_KEYS found in environment or .env file. API key security is disabled.")