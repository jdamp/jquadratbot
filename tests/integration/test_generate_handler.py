"""Integration tests for /generate command handler — TDD."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config import BotConfig
from src.gemini.context import sessions


@pytest.fixture(autouse=True)
def clear_sessions() -> Generator[None]:
    sessions.clear()
    yield
    sessions.clear()


@pytest.fixture
def config(monkeypatch: pytest.MonkeyPatch) -> BotConfig:
    monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    return BotConfig.from_env()


class TestGenerateHandler:
    async def test_valid_prompt_sends_ack_then_photo(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
        sample_image_bytes: bytes,
    ) -> None:
        from src.handlers.generate import generate_handler

        mock_update.message.text = "/generate a sunset over mountains"
        mock_update.message.photo = []
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = sample_image_bytes
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_genai_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        await generate_handler(mock_update, mock_ptb_context)

        reply_text_calls = mock_update.message.reply_text.call_args_list
        assert len(reply_text_calls) >= 1
        assert "Generating" in reply_text_calls[0].args[0]
        mock_update.message.reply_photo.assert_called_once()

    async def test_missing_prompt_replies_usage_error(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.generate import generate_handler

        mock_update.message.text = "/generate"
        mock_update.message.photo = []
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        await generate_handler(mock_update, mock_ptb_context)

        mock_update.message.reply_text.assert_called_once()
        error_msg = mock_update.message.reply_text.call_args.args[0]
        assert "describe" in error_msg.lower() or "example" in error_msg.lower()
        mock_update.message.reply_photo.assert_not_called()

    async def test_policy_violation_replies_friendly_error(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.generate import generate_handler

        mock_update.message.text = "/generate something blocked"
        mock_update.message.photo = []
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        mock_candidate = MagicMock()
        mock_candidate.content = None
        mock_candidate.finish_reason = "SAFETY"
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_genai_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        await generate_handler(mock_update, mock_ptb_context)

        calls = mock_update.message.reply_text.call_args_list
        last_reply = calls[-1].args[0]
        assert "generate" in last_reply.lower() or "wasn't" in last_reply.lower()

    async def test_api_error_replies_with_gemini_error_message(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.generate import generate_handler

        mock_update.message.text = "/generate a nice dog"
        mock_update.message.photo = []
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        mock_genai_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("API failure")
        )

        await generate_handler(mock_update, mock_ptb_context)

        calls = mock_update.message.reply_text.call_args_list
        last_reply = calls[-1].args[0]
        assert "Gemini API" in last_reply
