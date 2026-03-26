# Research: Gemini Image Bot

**Branch**: `001-gemini-image-bot` | **Date**: 2026-03-24
**Phase**: 0 — Resolve all NEEDS CLARIFICATION from Technical Context

---

## Decision 1: Telegram Bot Framework

**Decision**: `python-telegram-bot` (PTB) v21.x

**Rationale**:
- Batteries-included: `ApplicationBuilder` manages the asyncio event loop, polling, and
  graceful shutdown — no boilerplate needed for a small project.
- Built-in `JobQueue` (wraps APScheduler) and `create_task()` for non-blocking background
  work, which satisfies the constitution's "non-blocking event loop" requirement.
- Photo handling is ergonomic: `update.message.photo[-1]` returns the highest-resolution
  `PhotoSize`; `File.download_as_bytearray()` retrieves raw bytes for passing to Gemini.
- Extensive documentation and stable release cadence — low maintenance burden for a solo
  developer.

**Alternatives considered**:
- `aiogram` v3: fully async, modern design, but requires explicit dispatcher/router/FSM
  setup that adds unnecessary complexity for a 2–3 user personal bot.

**Version note**: PTB 21.x targets Python 3.9+; both libraries are pure-Python with no C
extensions, so they install cleanly on Python 3.14. Verify latest stable on PyPI before
pinning: `uv pip index versions python-telegram-bot`.

---

## Decision 2: Google Gemini SDK

**Decision**: `google-genai` (NOT `google-generativeai`)

**Rationale**:
- `google-generativeai` is the legacy SDK, deprecated by Google in 2024.
- `google-genai` is the current, actively maintained SDK. It supports both the Gemini
  Developer API (API key) and Vertex AI through a single unified client.
- Version `1.14.0` is confirmed present in the local uv cache — use as the minimum pin.
- The SDK provides async counterparts under `client.aio.*`, essential for non-blocking
  operation inside PTB's asyncio event loop.

**Import pattern**:
```python
from google import genai
from google.genai import types
```

---

## Decision 3: Gemini Models per Capability

**Default model for all image tasks**: `gemini-3.1-flash-image-preview`

This single model handles image understanding, generation, and editing through the unified
`generate_content()` / `chats` API surface, eliminating the need for separate Imagen API
calls and simplifying the implementation to a single client pattern.

| Capability       | Model                          | API method                        | Status   |
|------------------|--------------------------------|-----------------------------------|----------|
| Image understand | `gemini-3.1-flash-image-preview` | `client.aio.models.generate_content()` | Preview |
| Multi-turn chat  | `gemini-3.1-flash-image-preview` | `client.aio.chats.create()`       | Preview  |
| Image generation | `gemini-3.1-flash-image-preview` | `client.aio.models.generate_content()` with image output modality | Preview |
| Image editing    | `gemini-3.1-flash-image-preview` | `client.aio.models.generate_content()` with image input + output | Preview  |

**Important caveats**:
- This is a preview model; the name and API surface may change before GA. The model name
  MUST be externalised to a config value (not hard-coded) so it can be updated without a
  code change.
- Because it is in preview, monitor the Google AI changelog and update the pinned model
  name in config when a stable version is released.
- Previous alternative (now replaced): separate `imagen-3.0-generate-002` for generation
  and `imagen-3.0-capability-preview-0001` for editing. These required different API methods
  and billing tiers. The unified model removes this complexity.

---

## Decision 4: Conversation Context Storage

**Decision**: In-memory `dict` keyed by `chat_id`; no database.

**Rationale**:
- Personal scale (2–3 users) makes database overhead unjustified (Principle V: Simplicity).
- Context expires after 1 hour of inactivity by design, so losing it on bot restart is
  acceptable.
- The Gemini SDK returns history as `list[types.Content]`, which is serialisable to JSON
  if persistence across restarts is ever needed — easy to add later.

**Storage shape**:
```python
{
  chat_id: {
    "history": list[types.Content],   # raw Gemini history
    "last_active": datetime,          # UTC timestamp of last interaction
  }
}
```

**Session expiry check**: on every slash command, compare `datetime.now(UTC) - last_active`
against the configured timeout. If expired, clear the history entry and notify the user.

**Alternatives considered**:
- SQLite: more robust persistence but unnecessary complexity for this scale.
- Pickle file: fragile serialisation format; discarded in favour of potential JSON approach.

---

## Decision 5: Async Pattern

PTB handlers are native `async def` coroutines. The pattern for long-running operations:

```python
async def interpret_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Analysing your image…")   # immediate ACK ≤3s
    result = await gemini.interpret(chat_id, image_bytes, text) # awaitable, non-blocking
    await update.message.reply_text(result)
```

Because `gemini.interpret()` is `async`, it yields control to the event loop while waiting
for the API response. Other incoming messages are processed concurrently. No `create_task()`
is needed for the standard request/response flow.

---

## Decision 6: Image Size Handling

Telegram delivers photos in multiple sizes (`PhotoSize` list); the bot always takes
`photo[-1]` (largest). Telegram itself enforces a ~10 MB limit on photo uploads from
clients, so oversized images are rejected by Telegram before reaching the bot in most cases.

However, documents sent as files bypass Telegram's compression and can exceed this limit.
The bot will check the `file_size` attribute of the `PhotoSize` and reject images above a
configurable threshold (default: 10 MB) with a user-friendly message.

The Gemini Files API accepts inline bytes up to ~20 MB; images well within the Telegram
limit will not require the Files API, but the architecture leaves room to adopt it later.
