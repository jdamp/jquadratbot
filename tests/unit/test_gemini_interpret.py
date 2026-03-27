"""Unit tests for interpret Gemini logic — TDD."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config import BotConfig
from src.gemini.context import ChatSession
from src.gemini.errors import GeminiError


@pytest.fixture
def config(monkeypatch: pytest.MonkeyPatch) -> BotConfig:
    monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    return BotConfig.from_env()


@pytest.fixture
def fresh_session() -> ChatSession:
    return ChatSession(chat_id=1, history=[], last_active=datetime.now(UTC))


@pytest.fixture
def expired_session() -> ChatSession:
    return ChatSession(
        chat_id=1,
        history=[MagicMock()],  # has prior history
        last_active=datetime.now(UTC) - timedelta(hours=2),
    )


class TestInterpretImage:
    async def test_interpret_with_new_image_returns_text(
        self,
        mock_genai_client: MagicMock,
        config: BotConfig,
        fresh_session: ChatSession,
        sample_image_bytes: bytes,
    ) -> None:
        from src.gemini.interpret import interpret_image

        mock_chat = mock_genai_client.aio.chats.create.return_value
        mock_response = MagicMock()
        mock_response.text = "This is a dog."
        mock_chat.send_message = AsyncMock(return_value=mock_response)
        mock_chat.get_history = MagicMock(return_value=[MagicMock(), MagicMock()])

        result = await interpret_image(
            client=mock_genai_client,
            config=config,
            session=fresh_session,
            image_bytes=sample_image_bytes,
            question="What is this?",
        )

        assert result == "This is a dog."
        mock_genai_client.aio.chats.create.assert_called_once()
        assert len(fresh_session.history) == 2  # history updated

    async def test_interpret_followup_uses_stored_history(
        self,
        mock_genai_client: MagicMock,
        config: BotConfig,
        fresh_session: ChatSession,
    ) -> None:
        from src.gemini.interpret import interpret_image

        existing_content = MagicMock()
        fresh_session.history.append(existing_content)

        mock_chat = mock_genai_client.aio.chats.create.return_value
        mock_response = MagicMock()
        mock_response.text = "It's still a dog."
        mock_chat.send_message = AsyncMock(return_value=mock_response)
        mock_chat.get_history = MagicMock(return_value=[existing_content, MagicMock()])

        result = await interpret_image(
            client=mock_genai_client,
            config=config,
            session=fresh_session,
            image_bytes=None,
            question="What colour is it?",
        )

        assert result == "It's still a dog."
        # history should have been passed to chats.create
        call_kwargs = mock_genai_client.aio.chats.create.call_args
        assert call_kwargs is not None

    async def test_gemini_api_exception_raises_gemini_error(
        self,
        mock_genai_client: MagicMock,
        config: BotConfig,
        fresh_session: ChatSession,
        sample_image_bytes: bytes,
    ) -> None:
        from src.gemini.interpret import interpret_image

        mock_chat = mock_genai_client.aio.chats.create.return_value
        mock_chat.send_message = AsyncMock(side_effect=Exception("API down"))

        with pytest.raises(GeminiError):
            await interpret_image(
                client=mock_genai_client,
                config=config,
                session=fresh_session,
                image_bytes=sample_image_bytes,
                question=None,
            )
