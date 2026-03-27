"""Integration tests covering all error conditions from contracts/commands.md."""

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest

from src.config import BotConfig
from src.gemini.context import sessions
from src.handlers.common import HELP_TEXT


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


class TestUnknownCommand:
    async def test_unknown_slash_command_replies_with_help(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
    ) -> None:
        from src.handlers.common import unknown_command_handler

        mock_update.message.text = "/foo"
        await unknown_command_handler(mock_update, mock_ptb_context)

        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args.args[0]
        assert "I don't know that command." in response
        assert HELP_TEXT in response


class TestHelpAndStart:
    async def test_help_returns_command_list(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
    ) -> None:
        from src.handlers.common import help_handler

        await help_handler(mock_update, mock_ptb_context)

        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args.args[0]
        assert "/interpret" in response
        assert "/generate" in response
        assert "/modify" in response
        assert "/reset" in response
        assert "/help" in response

    async def test_start_returns_welcome_and_command_list(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
    ) -> None:
        from src.handlers.common import start_handler

        await start_handler(mock_update, mock_ptb_context)

        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args.args[0]
        assert "/interpret" in response


class TestInterpretErrors:
    async def test_interpret_no_image_no_context_error_message(
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

        response = mock_update.message.reply_text.call_args.args[0]
        assert "image" in response.lower()

    async def test_interpret_oversized_image_error_message(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        mock_photo_size: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.interpret import interpret_handler

        mock_photo_size.file_size = 20_000_000  # 20 MB > 10 MB limit
        mock_update.message.photo = [mock_photo_size]
        mock_update.message.caption = "/interpret"
        mock_update.message.text = None
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        await interpret_handler(mock_update, mock_ptb_context)

        response = mock_update.message.reply_text.call_args.args[0]
        assert "large" in response.lower() or "10 MB" in response


class TestGenerateErrors:
    async def test_generate_no_prompt_error_includes_example(
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

        response = mock_update.message.reply_text.call_args.args[0]
        assert "/generate" in response  # usage example present


class TestModifyErrors:
    async def test_modify_no_image_error_message(
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

        response = mock_update.message.reply_text.call_args.args[0]
        assert "image" in response.lower()

    async def test_modify_no_instruction_error_message(
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

        response = mock_update.message.reply_text.call_args.args[0]
        assert "describe" in response.lower() or "/modify" in response

    async def test_modify_oversized_image_error_message(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
        mock_photo_size: MagicMock,
        config: BotConfig,
        mock_genai_client: MagicMock,
    ) -> None:
        from src.handlers.modify import modify_handler

        mock_photo_size.file_size = 20_000_000
        mock_update.message.photo = [mock_photo_size]
        mock_update.message.caption = "/modify make it darker"
        mock_update.message.text = None
        mock_update.message.reply_to_message = None
        mock_ptb_context.bot_data = {"config": config, "client": mock_genai_client}

        await modify_handler(mock_update, mock_ptb_context)

        response = mock_update.message.reply_text.call_args.args[0]
        assert "large" in response.lower() or "10 MB" in response


class TestResetHandler:
    async def test_reset_with_active_session_confirms_cleared(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
    ) -> None:
        from src.gemini.context import get_or_create_session
        from src.handlers.reset import reset_handler

        chat_id = mock_update.effective_chat.id
        get_or_create_session(chat_id)
        mock_ptb_context.bot_data = {}

        await reset_handler(mock_update, mock_ptb_context)

        response = mock_update.message.reply_text.call_args.args[0]
        assert "cleared" in response.lower() or "forgotten" in response.lower()

    async def test_reset_with_no_session_replies_nothing_to_clear(
        self,
        mock_update: MagicMock,
        mock_ptb_context: MagicMock,
    ) -> None:
        from src.handlers.reset import reset_handler

        mock_ptb_context.bot_data = {}

        await reset_handler(mock_update, mock_ptb_context)

        response = mock_update.message.reply_text.call_args.args[0]
        assert "nothing" in response.lower() or "no active" in response.lower()
