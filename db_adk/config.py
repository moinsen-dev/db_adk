"""
Configuration settings for the DB-ADK package.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_url():
    """Get the database URL from environment variables."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "db_adk")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

def get_adk_api_key():
    """Get the ADK API key from environment variables."""
    return os.getenv("ADK_API_KEY")

def get_default_model():
    """Get the default model name from environment variables."""
    return os.getenv("DEFAULT_MODEL", "gemini-1.5-pro")
