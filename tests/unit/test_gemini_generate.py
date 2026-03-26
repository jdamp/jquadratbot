"""Unit tests for generate Gemini logic — TDD."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config import BotConfig
from src.gemini.errors import ContentPolicyError, GeminiError


@pytest.fixture
def config(monkeypatch: pytest.MonkeyPatch) -> BotConfig:
    monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    return BotConfig.from_env()


class TestGenerateImage:
    async def test_successful_generate_returns_image_bytes(
        self,
        mock_genai_client: MagicMock,
        config: BotConfig,
        sample_image_bytes: bytes,
    ) -> None:
        from src.gemini.generate import generate_image

        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = sample_image_bytes
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_genai_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        result = await generate_image(
            client=mock_genai_client,
            config=config,
            prompt="a cartoon cat wearing a sunhat",
        )

        assert result == sample_image_bytes

    async def test_empty_prompt_raises_value_error(
        self,
        mock_genai_client: MagicMock,
        config: BotConfig,
    ) -> None:
        from src.gemini.generate import generate_image

        with pytest.raises(ValueError):
            await generate_image(client=mock_genai_client, config=config, prompt="")

    async def test_content_policy_violation_raises_content_policy_error(
        self,
        mock_genai_client: MagicMock,
        config: BotConfig,
    ) -> None:
        from src.gemini.generate import generate_image

        mock_candidate = MagicMock()
        mock_candidate.content = None
        mock_candidate.finish_reason = "SAFETY"
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_genai_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with pytest.raises(ContentPolicyError):
            await generate_image(
                client=mock_genai_client,
                config=config,
                prompt="something problematic",
            )

    async def test_api_exception_raises_gemini_error(
        self,
        mock_genai_client: MagicMock,
        config: BotConfig,
    ) -> None:
        from src.gemini.generate import generate_image

        mock_genai_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("network error")
        )

        with pytest.raises(GeminiError):
            await generate_image(
                client=mock_genai_client,
                config=config,
                prompt="a nice landscape",
            )
