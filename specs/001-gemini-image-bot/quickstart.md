# Quickstart: Gemini Image Bot

**Branch**: `001-gemini-image-bot` | **Date**: 2026-03-24

---

## Prerequisites

- Python 3.14 installed (verify: `python --version`)
- `uv` installed (verify: `uv --version`)
- A Telegram Bot token — create one via [@BotFather](https://t.me/BotFather) on Telegram
- A Google Gemini API key — obtain from [Google AI Studio](https://aistudio.google.com/apikey)

---

## 1. Clone and Set Up the Environment

```bash
git clone <repo-url>
cd telegram-img
uv sync
```

`uv sync` reads `pyproject.toml` and `uv.lock`, creates a virtual environment, and installs
all pinned dependencies.

---

## 2. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
# Required
TELEGRAM_TOKEN=your-telegram-bot-token-here
GEMINI_API_KEY=your-gemini-api-key-here

# Optional (defaults shown)
SESSION_TIMEOUT_MINUTES=60
MAX_IMAGE_SIZE_BYTES=10485760
GEMINI_MODEL=gemini-3.1-flash-image-preview
```

**Never commit `.env` to version control.** It is already listed in `.gitignore`.

---

## 3. Run the Bot Locally

```bash
uv run python -m src.bot
```

You should see log output confirming the bot has started polling. Send `/start` to your
bot on Telegram to verify it responds.

---

## 4. Run the Tests

```bash
uv run pytest --cov=src --cov-report=term-missing
```

All tests must pass and coverage must be ≥80% before any commit is merged.

---

## 5. Run Linting and Type Checks

```bash
uv run ruff check .
uv run mypy .
```

Both must exit with zero errors. These checks are also enforced in CI.

---

## 6. Verify Bot Commands Work

After starting the bot, test each command:

| Test | Command | Expected |
|------|---------|----------|
| Welcome | `/start` | Welcome message + command list |
| Help | `/help` | Command list |
| Reset (empty) | `/reset` | "Nothing to clear" message |
| Interpret | Send a photo with caption `/interpret What is this?` | Image description within 30s |
| Generate | `/generate a sunset over mountains` | Generated image within 30s |
| Modify | Reply to a photo with `/modify make it black and white` | Modified image within 30s |
| Error: no image | `/interpret` (no photo, no context) | Friendly error asking for photo |
| Error: unknown command | `/foo` | Unknown command + help list |

---

## 7. Deploying

The bot runs as a single long-lived process. For a home server or VPS:

```bash
# Run in background with logging
uv run python -m src.bot >> bot.log 2>&1 &
```

For a more robust deployment, use a `systemd` service unit or a process manager like
`supervisor`. Ensure `TELEGRAM_TOKEN` and `GEMINI_API_KEY` are available as environment
variables in the service environment (do not embed them in the service file).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Bot does not respond to commands | Token incorrect or bot not added to chat | Re-check `TELEGRAM_TOKEN`; add bot to the group |
| "Gemini API error" on all requests | API key missing or invalid | Check `GEMINI_API_KEY` in `.env` |
| Model not found error | Preview model name changed | Update `GEMINI_MODEL` in `.env` to the current model name |
| `mypy` errors on startup | Type annotation mismatch | Run `uv run mypy .` and fix reported errors |
| Bot responds to every message | Command filtering misconfigured | Verify `filters.COMMAND` is applied to all handlers |
