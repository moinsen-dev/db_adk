"""
Configuration settings for the DB-ADK package.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_url():
    """Get the database URL from environment variables."""
    # Use SQLite instead of PostgreSQL
    db_path = os.getenv("DB_PATH", "db_adk.sqlite")

    # Ensure the directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    return f"sqlite:///{db_path}"

def get_adk_api_key():
    """Get the ADK API key from environment variables."""
    return os.getenv("ADK_API_KEY")

def get_default_model():
    """Get the default model name from environment variables."""
    return os.getenv("DEFAULT_MODEL", "gemini-1.5-pro")
