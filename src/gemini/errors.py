"""Custom exception types for Gemini operations."""


class GeminiError(Exception):
    """Raised when the Gemini API returns an error or is unavailable."""


class ContentPolicyError(GeminiError):
    """Raised when Gemini refuses to process/generate content due to safety policies."""
