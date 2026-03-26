# telegram-img Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-24

## Active Technologies

- Python 3.14 + `python-telegram-bot` ≥21.0, `google-genai` ≥1.14.0 (001-gemini-image-bot)

## Project Structure

```text
src/
tests/
```

## Commands

```bash
uv run python -m src.bot        # run the bot
uv run pytest --cov=src         # run tests with coverage
uv run ruff check .             # lint
uv run mypy .                   # type check
```

## Code Style

Python 3.14: Follow standard conventions

## Recent Changes

- 001-gemini-image-bot: Added Python 3.14 + `python-telegram-bot` ≥21.0, `google-genai` ≥1.14.0

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
