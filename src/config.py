"""BotConfig: load and validate environment variables at startup."""

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class BotConfig:
    telegram_token: str
    gemini_api_key: str
    session_timeout_minutes: int
    max_image_size_bytes: int
    gemini_model: str

    @classmethod
    def from_env(cls) -> BotConfig:
        """Load configuration from environment variables.

        Calls sys.exit(1) if required variables are missing.
        Raises ValueError if optional integer variables are invalid.
        """
        load_dotenv()

        telegram_token = os.getenv("TELEGRAM_TOKEN", "").strip()
        if not telegram_token:
            print("ERROR: TELEGRAM_TOKEN environment variable is required.", file=sys.stderr)
            sys.exit(1)

        gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not gemini_api_key:
            print("ERROR: GEMINI_API_KEY environment variable is required.", file=sys.stderr)
            sys.exit(1)

        timeout_str = os.getenv("SESSION_TIMEOUT_MINUTES", "60")
        try:
            session_timeout_minutes = int(timeout_str)
        except ValueError as exc:
            raise ValueError(
                f"SESSION_TIMEOUT_MINUTES must be an integer, got: {timeout_str!r}"
            ) from exc
        if session_timeout_minutes <= 0:
            raise ValueError(
                f"SESSION_TIMEOUT_MINUTES must be positive, got: {session_timeout_minutes}"
            )

        size_str = os.getenv("MAX_IMAGE_SIZE_BYTES", "10485760")
        try:
            max_image_size_bytes = int(size_str)
        except ValueError as exc:
            raise ValueError(
                f"MAX_IMAGE_SIZE_BYTES must be an integer, got: {size_str!r}"
            ) from exc
        if max_image_size_bytes <= 0:
            raise ValueError(
                f"MAX_IMAGE_SIZE_BYTES must be a positive integer, got: {max_image_size_bytes}"
            )

        gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-image-preview").strip()

        return cls(
            telegram_token=telegram_token,
            gemini_api_key=gemini_api_key,
            session_timeout_minutes=session_timeout_minutes,
            max_image_size_bytes=max_image_size_bytes,
            gemini_model=gemini_model,
        )
