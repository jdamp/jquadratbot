"""Integration tests for /modify command handler — TDD."""

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


def _make_modified_response(image_bytes: bytes) -> MagicMock:
    mock_part = MagicMock()
    mock_part.inline_data = MagicMock()
    mock_part.inline_data.data = image_bytes
    mock_candidate = MagicMock()
    mock_candidate.content.parts = [mock_part]
    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]
    return mock_response


class TestModifyHandler:
    async def test_photo_with_instruction_sends_ack_then_photo(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        mock_photo_size: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
        sample_image_bytes: bytes,
    ) -> None:
        from src.handlers.modify import modify_handler

        mock_update.message.photo = [mock_photo_size]
        mock_update.message.caption = "/modify make the background blue"
        mock_update.message.text = None
        mock_update.message.reply_to_message = None
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        mock_genai_client.aio.models.generate_content = AsyncMock(
            return_value=_make_modified_response(sample_image_bytes)
        )

        await modify_handler(mock_update, mock_ptb_context)

        ack_calls = mock_update.message.reply_text.call_args_list
        assert len(ack_calls) >= 1
        assert "Modifying" in ack_calls[0].args[0]
        mock_update.message.reply_photo.assert_called_once()

    async def test_reply_to_photo_with_instruction_modifies_referenced_image(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        mock_photo_size: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
        sample_image_bytes: bytes,
    ) -> None:
        from src.handlers.modify import modify_handler

        # No photo directly attached — instead it's a reply to a photo message
        mock_update.message.photo = []
        mock_update.message.text = "/modify make it black and white"
        mock_update.message.caption = None

        reply_msg = MagicMock()
        reply_msg.photo = [mock_photo_size]
        mock_update.message.reply_to_message = reply_msg
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        mock_genai_client.aio.models.generate_content = AsyncMock(
            return_value=_make_modified_response(sample_image_bytes)
        )

        await modify_handler(mock_update, mock_ptb_context)

        mock_update.message.reply_photo.assert_called_once()

    async def test_no_image_replies_error(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.modify import modify_handler

        mock_update.message.photo = []
        mock_update.message.text = "/modify make it blue"
        mock_update.message.caption = None
        mock_update.message.reply_to_message = None
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        await modify_handler(mock_update, mock_ptb_context)

        mock_update.message.reply_text.assert_called_once()
        error_msg = mock_update.message.reply_text.call_args.args[0]
        assert "image" in error_msg.lower()
        mock_update.message.reply_photo.assert_not_called()

    async def test_no_instruction_replies_error(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        mock_photo_size: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.modify import modify_handler

        mock_update.message.photo = [mock_photo_size]
        mock_update.message.caption = "/modify"
        mock_update.message.text = None
        mock_update.message.reply_to_message = None
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        await modify_handler(mock_update, mock_ptb_context)

        mock_update.message.reply_text.assert_called_once()
        error_msg = mock_update.message.reply_text.call_args.args[0]
        assert "describe" in error_msg.lower() or "instruction" in error_msg.lower()

    async def test_api_error_replies_with_gemini_error_message(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        mock_photo_size: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.modify import modify_handler

        mock_update.message.photo = [mock_photo_size]
        mock_update.message.caption = "/modify make it darker"
        mock_update.message.text = None
        mock_update.message.reply_to_message = None
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        mock_genai_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("API failure")
        )

        await modify_handler(mock_update, mock_ptb_context)

        calls = mock_update.message.reply_text.call_args_list
        last_reply = calls[-1].args[0]
        assert "Gemini API" in last_reply
