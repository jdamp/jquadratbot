"""Image interpretation via the Gemini multi-turn chat API."""

from datetime import UTC, datetime

from google import genai
from google.genai import types

from src.config import BotConfig
from src.gemini.context import ChatSession
from src.gemini.errors import GeminiError


async def interpret_image(
    client: genai.Client,
    config: BotConfig,
    session: ChatSession,
    image_bytes: bytes | None,
    question: str | None,
) -> str:
    """Send an image (or follow-up question) to Gemini and return the response text.

    Args:
        client: Initialised google-genai async client.
        config: Bot configuration (model name, etc.).
        session: The ChatSession for this chat — history is read and updated in place.
        image_bytes: Raw image bytes to interpret, or None for a text-only follow-up.
        question: Optional question / instruction text.

    Returns:
        The model's natural-language response.

    Raises:
        GeminiError: If the Gemini API call fails.
    """
    parts: list[types.Part] = []

    if image_bytes is not None:
        parts.append(
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        )

    if question:
        parts.append(types.Part.from_text(text=question))
    elif not image_bytes:
        # No image and no question — caller should have validated; default prompt
        parts.append(types.Part.from_text(text="Describe this image."))

    if not parts and image_bytes is None:
        parts.append(types.Part.from_text(text="Describe this image."))

    new_turn = types.Content(role="user", parts=parts)

    # Cast history to the exact type expected by the google-genai type signature.
    history: list[types.Content | types.ContentDict] = list(session.history)

    try:
        # client.aio.chats.create() returns AsyncChat directly (not a coroutine).
        chat = client.aio.chats.create(
            model=config.gemini_model,
            history=history,
        )
        response = await chat.send_message(new_turn)
        session.history = list(chat.get_history())
        session.last_active = datetime.now(UTC)
        return str(response.text)
    except Exception as exc:
        raise GeminiError(str(exc)) from exc
