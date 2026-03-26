"""Unit tests for BotConfig — TDD: written before implementation."""


import pytest

from src.config import BotConfig


class TestBotConfigValidation:
    def test_missing_telegram_token_raises_system_exit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        with pytest.raises(SystemExit):
            BotConfig.from_env()

    def test_empty_telegram_token_raises_system_exit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TELEGRAM_TOKEN", "")
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        with pytest.raises(SystemExit):
            BotConfig.from_env()

    def test_missing_gemini_api_key_raises_system_exit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TELEGRAM_TOKEN", "test-token")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(SystemExit):
            BotConfig.from_env()

    def test_empty_gemini_api_key_raises_system_exit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        with pytest.raises(SystemExit):
            BotConfig.from_env()

    def test_zero_session_timeout_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("SESSION_TIMEOUT_MINUTES", "0")
        with pytest.raises(ValueError, match="SESSION_TIMEOUT_MINUTES"):
            BotConfig.from_env()

    def test_negative_session_timeout_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("SESSION_TIMEOUT_MINUTES", "-5")
        with pytest.raises(ValueError, match="SESSION_TIMEOUT_MINUTES"):
            BotConfig.from_env()

    def test_non_integer_session_timeout_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("SESSION_TIMEOUT_MINUTES", "abc")
        with pytest.raises(ValueError):
            BotConfig.from_env()

    def test_valid_env_produces_correct_fields(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TELEGRAM_TOKEN", "tok123")
        monkeypatch.setenv("GEMINI_API_KEY", "key456")
        monkeypatch.setenv("SESSION_TIMEOUT_MINUTES", "30")
        monkeypatch.setenv("MAX_IMAGE_SIZE_BYTES", "5242880")
        monkeypatch.setenv("GEMINI_MODEL", "gemini-custom-model")
        config = BotConfig.from_env()
        assert config.telegram_token == "tok123"
        assert config.gemini_api_key == "key456"
        assert config.session_timeout_minutes == 30
        assert config.max_image_size_bytes == 5242880
        assert config.gemini_model == "gemini-custom-model"

    def test_defaults_applied_when_optional_env_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
        monkeypatch.setenv("GEMINI_API_KEY", "key")
        monkeypatch.delenv("SESSION_TIMEOUT_MINUTES", raising=False)
        monkeypatch.delenv("MAX_IMAGE_SIZE_BYTES", raising=False)
        monkeypatch.delenv("GEMINI_MODEL", raising=False)
        config = BotConfig.from_env()
        assert config.session_timeout_minutes == 60
        assert config.max_image_size_bytes == 10_485_760
        assert config.gemini_model == "gemini-3.1-flash-image-preview"
