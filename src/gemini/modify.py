"""Image modification via the Gemini generate_content API."""

from google import genai
from google.genai import types

from src.config import BotConfig
from src.gemini.errors import ContentPolicyError, GeminiError


async def modify_image(
    client: genai.Client,
    config: BotConfig,
    image_bytes: bytes,
    instruction: str,
) -> bytes:
    """Apply a text instruction to an existing image using Gemini.

    Args:
        client: Initialised google-genai async client.
        config: Bot configuration (model name, etc.).
        image_bytes: Raw bytes of the image to modify.
        instruction: Natural-language modification instruction.

    Returns:
        Raw image bytes of the modified image.

    Raises:
        ContentPolicyError: If Gemini refuses the modification due to content policy.
        GeminiError: If the Gemini API call fails or returns no image data.
    """
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
    text_part = types.Part.from_text(text=instruction)
    content = types.Content(role="user", parts=[image_part, text_part])

    try:
        response = await client.aio.models.generate_content(
            model=config.gemini_model,
            contents=[content],
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
            ),
        )
    except Exception as exc:
        raise GeminiError(str(exc)) from exc

    if not response.candidates:
        raise GeminiError("Gemini returned no candidates.")

    candidate = response.candidates[0]

    if candidate.content is None:
        raise ContentPolicyError("Content policy violation.")

    parts = candidate.content.parts or []
    for part in parts:
        if hasattr(part, "inline_data") and part.inline_data is not None:
            data = part.inline_data.data
            if data is not None:
                return bytes(data)

    raise GeminiError("Gemini response contained no image data.")
