# Data Model: Gemini Image Bot

**Branch**: `001-gemini-image-bot` | **Date**: 2026-03-24

---

## Entities

### BotConfig

Application-level configuration loaded once at startup from environment variables.

| Field                    | Type       | Source          | Description                                    |
|--------------------------|------------|-----------------|------------------------------------------------|
| `telegram_token`         | `str`      | `TELEGRAM_TOKEN` env var | Telegram Bot API token              |
| `gemini_api_key`         | `str`      | `GEMINI_API_KEY` env var | Google Gemini API key               |
| `session_timeout_minutes`| `int`      | `SESSION_TIMEOUT_MINUTES` env var (default: 60) | Idle timeout before context is cleared |
| `max_image_size_bytes`   | `int`      | `MAX_IMAGE_SIZE_BYTES` env var (default: 10_485_760 = 10 MB) | Reject images above this size |
| `gemini_model`           | `str`      | `GEMINI_MODEL` env var (default: `"gemini-3.1-flash-image-preview"`) | Gemini model used for all image tasks; externalised so it can be updated without a code change when a GA model is released |

**Validation rules**:
- `telegram_token` and `gemini_api_key` MUST be non-empty strings; bot MUST fail fast at
  startup if either is missing.
- `session_timeout_minutes` MUST be a positive integer.
- `max_image_size_bytes` MUST be a positive integer.

---

### ChatSession

One instance per active chat (group chat or direct message). Held in an in-memory registry
keyed by `chat_id`. Not persisted to disk.

| Field         | Type                  | Description                                              |
|---------------|-----------------------|----------------------------------------------------------|
| `chat_id`     | `int`                 | Telegram chat identifier (unique per chat)               |
| `history`     | `list[types.Content]` | Ordered list of Gemini conversation turns (user + model) |
| `last_active` | `datetime`            | UTC timestamp of the most recent slash command in this chat |

**Validation rules**:
- `history` may be empty (new session or after reset).
- `last_active` is updated to `datetime.now(UTC)` on every successful slash command.

**State transitions**:

```
[no session] ──(first slash command)──► [active]
[active]     ──(idle > timeout)──────► [expired → cleared to no session]
[active]     ──(/reset command)──────► [cleared to no session]
```

When a session transitions to expired/cleared, the next slash command starts a new
`[active]` session from scratch.

---

### ImagePayload

Transient — built per request, not stored. Represents an image extracted from a Telegram
update for passing to the Gemini API.

| Field        | Type    | Description                                              |
|--------------|---------|----------------------------------------------------------|
| `data`       | `bytes` | Raw image bytes downloaded from Telegram                 |
| `mime_type`  | `str`   | MIME type (always `"image/jpeg"` or `"image/png"`)       |
| `file_size`  | `int`   | Size in bytes; used for the size limit check             |

---

### BotCommand (enumeration)

The set of slash commands the bot recognises.

| Command     | Arguments                          | Requires image |
|-------------|------------------------------------|----------------|
| `/interpret`| optional question text             | yes (or context) |
| `/generate` | required description text          | no             |
| `/modify`   | required instruction text          | yes (or reply) |
| `/reset`    | none                               | no             |
| `/help`     | none                               | no             |
| `/start`    | none                               | no             |

---

## In-Memory Registry Shape

```python
# src/context.py — conceptual shape (not literal code)
sessions: dict[int, ChatSession] = {}
# key: Telegram chat_id
# value: ChatSession with history and last_active
```

---

## Gemini History Format

Each turn in `ChatSession.history` follows the `google.genai.types.Content` schema:

```
Content(
    role = "user" | "model",
    parts = [
        Part(text="..."),                    # text part
        Part(inline_data=Blob(              # image part (user turns only)
            mime_type="image/jpeg",
            data=<bytes>
        )),
    ]
)
```

When reconstructing a chat for a follow-up, the full `history` list is passed to
`client.aio.chats.create(model=..., history=history)`. The returned `chat` object is used
to call `await chat.send_message(new_message)`, and the updated history is retrieved via
`chat.get_history()` and stored back in `ChatSession.history`.

---

## Configuration Precedence

1. Environment variables (production)
2. `.env` file loaded at startup via the environment (development)

No configuration is hard-coded in source. See `quickstart.md` for `.env` setup.
