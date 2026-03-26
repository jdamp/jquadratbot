"""Async Gemini client factory."""

from google import genai

from src.config import BotConfig


def create_client(config: BotConfig) -> genai.Client:
    """Create and return a google-genai Client initialised with the configured API key."""
    return genai.Client(api_key=config.gemini_api_key)
