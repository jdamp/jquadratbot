# Implementation Plan: Gemini Image Bot

**Branch**: `001-gemini-image-bot` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-gemini-image-bot/spec.md`

## Summary

Build a Telegram bot that lets a family chat (2–3 people) interpret, generate, and modify
images via Google Gemini AI, triggered exclusively by slash commands. The bot is implemented
in Python 3.14 using `python-telegram-bot` for the Telegram interface and `google-genai`
for all AI capabilities. Conversation context is maintained in memory per chat with a
configurable session expiry (default 1 hour).

## Technical Context

**Language/Version**: Python 3.14
**Primary Dependencies**: `python-telegram-bot` ≥21.0, `google-genai` ≥1.14.0
**Storage**: In-memory dict (no database; personal scale, context expires after 1 hour)
**Testing**: pytest + pytest-asyncio + pytest-cov
**Target Platform**: Linux server (long-running async process, self-hosted)
**Project Type**: Bot application (async event-driven service)
**Performance Goals**: Acknowledgement ≤3 seconds; full image response ≤30 seconds
**Constraints**: Telegram photo limit ~10 MB; `gemini-3.1-flash-image-preview` is a preview
model — model name must be externalised to config for easy updates when GA releases
**Scale/Scope**: 2–3 concurrent users; single family group chat + individual DMs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Code Quality | All code must pass `ruff check` (zero warnings) and `mypy` (zero errors); all functions must carry type annotations | ✅ Enforced via CI gates defined in constitution |
| II. Testing Standards | pytest mandatory; TDD (tests fail before implementation); ≥80% line coverage; integration tests for each slash command | ✅ Test tasks included in tasks.md |
| III. UX Consistency | Acknowledgement within 3 seconds for all long-running commands; uniform error message format across all commands (see contracts/commands.md) | ✅ Async handler pattern ensures non-blocking ACK; error messages standardised in contracts |
| IV. Performance | Gemini API calls must have explicit timeouts; event loop must not be blocked (all Gemini calls use `client.aio.*`) | ✅ PTB async handlers + `client.aio.*` satisfies non-blocking requirement |
| V. Simplicity | In-memory storage (no database for personal scale); PTB chosen over aiogram (simpler for solo maintainer); config via env vars; uv.lock pins all dependencies | ✅ No unjustified abstractions; YAGNI applied throughout |

**Bot framework amendment**: Constitution Section "Technology Stack & Tooling" specifies
the bot framework must be recorded here once chosen. **Selected: `python-telegram-bot`**.
(Constitution amendment to v1.1.1 made separately.)

## Project Structure

### Documentation (this feature)

```text
specs/001-gemini-image-bot/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── commands.md      # Bot command interface contracts
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── bot.py               # Entry point: ApplicationBuilder setup, handler registration
├── config.py            # BotConfig dataclass; loads + validates env vars at startup
├── context.py           # ChatSession dataclass; in-memory registry; expiry logic
├── gemini/
│   ├── __init__.py
│   ├── client.py        # Initialise google-genai async client
│   ├── interpret.py     # Image understanding: build/update chat history, call Gemini
│   ├── generate.py      # Image generation: call Imagen 3 via generate_images()
│   └── modify.py        # Image editing: call Imagen via edit_image()
└── handlers/
    ├── __init__.py
    ├── interpret.py     # /interpret command handler
    ├── generate.py      # /generate command handler
    ├── modify.py        # /modify command handler
    ├── reset.py         # /reset command handler
    └── common.py        # /help, /start, unknown command, error handler

tests/
├── conftest.py          # Shared fixtures (mock bot, mock Gemini client, sample images)
├── unit/
│   ├── test_config.py   # BotConfig validation
│   ├── test_context.py  # ChatSession expiry, reset, history management
│   ├── test_gemini_interpret.py
│   ├── test_gemini_generate.py
│   └── test_gemini_modify.py
└── integration/
    ├── test_interpret_handler.py  # /interpret end-to-end (mocked Gemini)
    ├── test_generate_handler.py   # /generate end-to-end (mocked Gemini)
    ├── test_modify_handler.py     # /modify end-to-end (mocked Gemini)
    └── test_error_handling.py     # all error conditions from contracts/commands.md

pyproject.toml           # Project metadata, dependencies, ruff + mypy config
uv.lock                  # Pinned dependency tree (committed to repo)
.env.example             # Template for required env vars (no secrets)
.env                     # Local secrets (gitignored)
.gitignore
```

**Structure Decision**: Single-project layout. The `src/` layout separates bot plumbing
(`bot.py`, `config.py`, `context.py`) from the two main concerns — Gemini AI operations
(`gemini/`) and PTB command handlers (`handlers/`). This maps cleanly to the three user
stories without premature abstraction.

## Complexity Tracking

> No constitution violations requiring justification.
