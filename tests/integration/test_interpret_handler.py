"""Integration tests for /interpret command handler — TDD."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config import BotConfig
from src.context import ChatSession, sessions


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


class TestInterpretHandler:
    async def test_photo_with_caption_sends_ack_then_description(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        mock_photo_size: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.interpret import interpret_handler

        mock_update.message.photo = [mock_photo_size]
        mock_update.message.caption = "/interpret What breed is this?"
        mock_update.message.text = None
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        mock_chat = mock_genai_client.aio.chats.create.return_value
        mock_response = MagicMock()
        mock_response.text = "This is a Labrador."
        mock_chat.send_message = AsyncMock(return_value=mock_response)
        mock_chat.get_history = MagicMock(return_value=[MagicMock()])

        await interpret_handler(mock_update, mock_ptb_context)

        calls = mock_update.message.reply_text.call_args_list
        assert len(calls) == 2
        assert "Analysing" in calls[0].args[0]
        assert "Labrador" in calls[1].args[0]

    async def test_no_image_and_no_context_replies_error(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.interpret import interpret_handler

        mock_update.message.photo = []
        mock_update.message.caption = None
        mock_update.message.text = "/interpret"
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        await interpret_handler(mock_update, mock_ptb_context)

        mock_update.message.reply_text.assert_called_once()
        error_msg = mock_update.message.reply_text.call_args.args[0]
        assert "image" in error_msg.lower()

    async def test_expired_session_notifies_user(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.interpret import interpret_handler

        chat_id = mock_update.effective_chat.id
        sessions[chat_id] = ChatSession(
            chat_id=chat_id,
            history=[MagicMock()],
            last_active=datetime.now(UTC) - timedelta(hours=2),
        )

        mock_update.message.photo = []
        mock_update.message.caption = None
        mock_update.message.text = "/interpret follow up"
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        await interpret_handler(mock_update, mock_ptb_context)

        reply_text = mock_update.message.reply_text.call_args.args[0]
        assert "expired" in reply_text.lower() or "inactivity" in reply_text.lower()

    async def test_gemini_error_replies_with_api_error_message(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        mock_photo_size: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.interpret import interpret_handler

        mock_update.message.photo = [mock_photo_size]
        mock_update.message.caption = "/interpret describe this"
        mock_update.message.text = None
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        mock_chat = mock_genai_client.aio.chats.create.return_value
        mock_chat.send_message = AsyncMock(side_effect=Exception("API failure"))

        await interpret_handler(mock_update, mock_ptb_context)

        calls = mock_update.message.reply_text.call_args_list
        # ACK sent first, then error
        assert len(calls) >= 2
        last_reply = calls[-1].args[0]
        assert "Gemini API" in last_reply

    async def test_oversized_image_replies_size_error(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        mock_photo_size: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.interpret import interpret_handler

        mock_photo_size.file_size = config.max_image_size_bytes + 1
        mock_update.message.photo = [mock_photo_size]
        mock_update.message.caption = "/interpret"
        mock_update.message.text = None
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        await interpret_handler(mock_update, mock_ptb_context)

        mock_update.message.reply_text.assert_called_once()
        error_msg = mock_update.message.reply_text.call_args.args[0]
        assert "large" in error_msg.lower() or "size" in error_msg.lower()
