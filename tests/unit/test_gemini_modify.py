"""Unit tests for modify Gemini logic — TDD."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config import BotConfig
from src.gemini.errors import ContentPolicyError, GeminiError


@pytest.fixture
def config(monkeypatch: pytest.MonkeyPatch) -> BotConfig:
    monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    return BotConfig.from_env()


class TestModifyImage:
    async def test_successful_modify_returns_image_bytes(
        self,
        mock_genai_client: MagicMock,
        config: BotConfig,
        sample_image_bytes: bytes,
    ) -> None:
        from src.gemini.modify import modify_image

        modified_bytes = b"\xff\xd8\xff" + b"\x00" * 20  # fake modified JPEG
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = modified_bytes
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_genai_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        result = await modify_image(
            client=mock_genai_client,
            config=config,
            image_bytes=sample_image_bytes,
            instruction="make the background blue",
        )

        assert result == modified_bytes

    async def test_content_policy_violation_raises_content_policy_error(
        self,
        mock_genai_client: MagicMock,
        config: BotConfig,
        sample_image_bytes: bytes,
    ) -> None:
        from src.gemini.modify import modify_image

        mock_candidate = MagicMock()
        mock_candidate.content = None
        mock_candidate.finish_reason = "SAFETY"
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_genai_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with pytest.raises(ContentPolicyError):
            await modify_image(
                client=mock_genai_client,
                config=config,
                image_bytes=sample_image_bytes,
                instruction="something blocked",
            )

    async def test_api_exception_raises_gemini_error(
        self,
        mock_genai_client: MagicMock,
        config: BotConfig,
        sample_image_bytes: bytes,
    ) -> None:
        from src.gemini.modify import modify_image

        mock_genai_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("network error")
        )

        with pytest.raises(GeminiError):
            await modify_image(
                client=mock_genai_client,
                config=config,
                image_bytes=sample_image_bytes,
                instruction="make it black and white",
            )
