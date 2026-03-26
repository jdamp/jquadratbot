"""Image generation via the Gemini generate_content API."""

from google import genai
from google.genai import types

from src.config import BotConfig
from src.gemini.errors import ContentPolicyError, GeminiError


async def generate_image(
    client: genai.Client,
    config: BotConfig,
    prompt: str,
) -> bytes:
    """Generate a new image from a text prompt using Gemini.

    Args:
        client: Initialised google-genai async client.
        config: Bot configuration (model name, etc.).
        prompt: Natural-language description of the desired image.

    Returns:
        Raw image bytes of the generated image.

    Raises:
        ValueError: If the prompt is empty.
        ContentPolicyError: If Gemini refuses the request due to content policy.
        GeminiError: If the Gemini API call fails.
    """
    if not prompt.strip():
        raise ValueError("Prompt must not be empty.")

    try:
        response = await client.aio.models.generate_content(
            model=config.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
            ),
        )
    except Exception as exc:
        raise GeminiError(str(exc)) from exc

    if not response.candidates:
        raise GeminiError("Gemini returned no candidates.")

    candidate = response.candidates[0]

    # Safety block: content is None or finish_reason indicates policy violation
    if candidate.content is None:
        raise ContentPolicyError("Content policy violation.")

    parts = candidate.content.parts or []
    for part in parts:
        if hasattr(part, "inline_data") and part.inline_data is not None:
            data = part.inline_data.data
            if data is not None:
                return bytes(data)

    raise GeminiError("Gemini response contained no image data.")
