"""
Centralized environment/config loading. Every module that needs a credential or
setting should import from here rather than calling os.getenv directly, so that
all configuration is discoverable in one place.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY", "")
    PORTKEY_VIRTUAL_KEY = os.getenv("PORTKEY_VIRTUAL_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO = os.getenv("GITHUB_REPO", "")
    PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL") or "https://api.portkey.ai/v1/chat/completions"
    MAX_TEST_RETRIES = int(os.getenv("MAX_TEST_RETRIES", "3"))

    @classmethod
    def validate(cls):
        missing = []
        if not cls.PORTKEY_API_KEY:
            missing.append("PORTKEY_API_KEY")
        if not cls.PORTKEY_VIRTUAL_KEY:
            missing.append("PORTKEY_VIRTUAL_KEY")
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Copy .env.example to .env and fill these in."
            )


config = Config()
