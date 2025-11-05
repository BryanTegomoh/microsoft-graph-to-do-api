"""Configuration management for the application."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # Microsoft Graph API
    CLIENT_ID = os.getenv("CLIENT_ID")
    TENANT_ID = os.getenv("TENANT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    GRAPH_SCOPES = os.getenv("GRAPH_SCOPES", "Tasks.ReadWrite offline_access").split()

    # AI Provider Configuration
    AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    XAI_API_KEY = os.getenv("XAI_API_KEY")

    # AI Models
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-pro")
    XAI_MODEL = os.getenv("XAI_MODEL", "grok-beta")

    # Application Settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))

    # Output Settings
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))
    ENABLE_TASK_UPDATES = os.getenv("ENABLE_TASK_UPDATES", "false").lower() == "true"
    GENERATE_MARKDOWN_BRIEF = os.getenv("GENERATE_MARKDOWN_BRIEF", "true").lower() == "true"

    # Email Configuration
    SEND_EMAIL_BRIEF = os.getenv("SEND_EMAIL_BRIEF", "false").lower() == "true"
    EMAIL_FROM = os.getenv("EMAIL_FROM")
    EMAIL_TO = os.getenv("EMAIL_TO")
    EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    # Graph API Endpoints
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    GRAPH_TODO_LISTS_ENDPOINT = f"{GRAPH_API_BASE}/me/todo/lists"

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        errors = []

        if not cls.CLIENT_ID:
            errors.append("CLIENT_ID is required")
        if not cls.TENANT_ID:
            errors.append("TENANT_ID is required")
        # CLIENT_SECRET is optional - if not provided, will use device code flow

        # Validate AI provider config
        if cls.AI_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when using OpenAI")
        elif cls.AI_PROVIDER == "anthropic" and not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is required when using Anthropic")
        elif cls.AI_PROVIDER == "google" and not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY is required when using Google")
        elif cls.AI_PROVIDER == "xai" and not cls.XAI_API_KEY:
            errors.append("XAI_API_KEY is required when using xAI Grok")

        # Validate email config if enabled
        if cls.SEND_EMAIL_BRIEF:
            if not cls.EMAIL_FROM:
                errors.append("EMAIL_FROM is required when SEND_EMAIL_BRIEF is enabled")
            if not cls.EMAIL_TO:
                errors.append("EMAIL_TO is required when SEND_EMAIL_BRIEF is enabled")
            if not cls.EMAIL_PASSWORD:
                errors.append("EMAIL_PASSWORD is required when SEND_EMAIL_BRIEF is enabled")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True

    @classmethod
    def setup_output_dir(cls):
        """Create output directory if it doesn't exist."""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
