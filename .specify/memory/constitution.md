<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0 (2026-03-24, initial constitution)
               1.0.0 → 1.1.0 (2026-03-24, Principle IV revised: removed hard concurrency
               and memory caps inappropriate for a personal-scale bot; aligned to actual
               use case of a family chat with 2 members + individual accounts)

Modified principles:
  - IV. Performance Requirements — removed "10 concurrent requests" and "512 MB" hard caps;
    added explicit acknowledgement of personal-scale target; retained Telegram timeout and
    graceful-failure requirements.
  - Development Workflow — commit message style updated from "imperative mood" to
    conventional commit format (feat:/fix:/docs: etc.).

Added sections: all sections new in 1.0.0.

Removed sections: N/A

Templates requiring updates:
  ✅ .specify/templates/plan-template.md — no structural change needed.
  ✅ .specify/templates/spec-template.md — no structural change needed.
  ✅ .specify/templates/tasks-template.md — no structural change needed.
  ✅ .claude/commands/*.md — no agent-specific naming conflicts detected.

Follow-up TODOs:
  - TODO(RATIFICATION_DATE): Set to 2026-03-24 (today); confirm if project has an earlier
    kick-off date.
-->


# telegram-img Constitution

## Core Principles

### I. Code Quality (NON-NEGOTIABLE)

All Python code MUST:

- Carry complete type annotations using built-in generics (`list`, `dict`, `tuple`, etc.);
  `typing` imports are permitted only for constructs not yet available as built-ins in the
  target Python version.
- Pass `ruff` linting with zero warnings before any commit is merged.
- Pass `mypy --strict` (or the project-configured strictness level) with zero errors before
  any commit is merged.
- Avoid dead code, unused imports, and unused variables — ruff rules enforce this
  automatically and MUST NOT be suppressed without an inline comment justifying the exception.

**Rationale**: Consistent static analysis eliminates entire categories of runtime bugs and
accelerates code review. Since this project uses `uv` for environment management, tooling
runs are reproducible across all contributors.

### II. Testing Standards (NON-NEGOTIABLE)

- Every new module or public function MUST have at least one unit test covering the primary
  happy path and one test covering the primary failure/edge path.
- Integration tests MUST cover end-to-end Telegram bot interactions for each user-facing
  feature before that feature is considered complete.
- Tests MUST be written and confirmed to **fail** before the implementation that makes them
  pass is written (Red-Green-Refactor).
- `pytest` is the mandatory test runner; no other framework is permitted without a formal
  amendment.
- Test coverage MUST NOT decrease when a PR is merged; the project targets ≥ 80% line
  coverage as a minimum gate.

**Rationale**: Early test failures expose contract mismatches between the Telegram Bot API
and local logic. Mandatory failure-first discipline prevents tests that never actually
validate the code under test.

### III. User Experience Consistency

- All Telegram messages sent by the bot MUST use a consistent voice and formatting style
  defined in the UX guidelines document (to be created alongside the first feature spec).
- Error messages shown to users MUST be human-readable, actionable, and free of internal
  exception details or stack traces.
- Every user-facing operation MUST provide feedback within 3 seconds (e.g., a "Processing…"
  acknowledgement) even if the full result takes longer.
- Response structure MUST be uniform across all commands: success responses follow one
  template, error responses follow another; ad-hoc formatting is not permitted.

**Rationale**: A bot that behaves inconsistently across commands erodes user trust. The 3-
second feedback rule aligns with Telegram's own UX guidance and prevents users from
retrying due to perceived silence.

### IV. Performance Requirements

This is a personal bot used exclusively by a family chat (2 people) and their individual
accounts. Concurrency requirements are therefore minimal; correctness and reliability matter
more than throughput.

- Image processing operations MUST complete within **30 seconds** of the bot acknowledging
  receipt; operations exceeding this limit MUST notify the user and fail gracefully rather
  than timing out silently.
- All external API calls (Telegram, any third-party image services) MUST have an explicit
  timeout configured; no unbounded blocking calls are permitted.
- The bot MUST remain responsive to new messages while processing an image (i.e., processing
  MUST NOT block the event loop).

**Rationale**: Telegram enforces hard limits on bot response windows. For a personal-scale
bot, the key concerns are reliability and a responsive feel — not horizontal scalability.

### V. Simplicity & Maintainability

- Abstractions MUST justify their existence; no abstraction layer is added unless two or
  more concrete use-cases already exist (YAGNI).
- Module boundaries MUST map to clear responsibilities; cross-module imports SHOULD flow in
  one direction (no circular dependencies).
- Configuration MUST be externalised (environment variables or a config file); no
  hard-coded credentials, tokens, or environment-specific values in source code.
- Dependencies MUST be pinned in the lock file (`uv.lock`); unpinned transitive dependencies
  that change silently are not acceptable.

**Rationale**: A small bot codebase that grows organically is far easier to maintain than
one pre-loaded with speculative abstractions. Pinned dependencies ensure reproducible builds
and prevent supply-chain surprises.

## Technology Stack & Tooling

- **Language**: Python 3.11+ (minimum version; newer versions preferred when available via uv).
- **Dependency management**: `uv` exclusively — no pip, pipenv, or poetry invocations.
- **Linting**: `ruff` — configured in `pyproject.toml`; CI blocks on any lint failure.
- **Type checking**: `mypy` — configured in `pyproject.toml`; CI blocks on any type error.
- **Testing**: `pytest` with `pytest-asyncio` for async bot handlers; `pytest-cov` for
  coverage reporting.
- **Bot framework**: `python-telegram-bot` ≥21.0 — selected during feature 001 planning
  (see `specs/001-gemini-image-bot/plan.md`). Chosen for its managed asyncio event loop,
  built-in job queue, and lower maintenance burden for a solo-maintained personal bot.

Any addition of a new runtime dependency requires a rationale comment in `pyproject.toml`
and MUST be reviewed as part of the PR that introduces it.

## Development Workflow

- **Branching**: Feature branches follow `###-feature-name` convention (sequential numbering).
- **Code Review**: Every PR requires at least one reviewer approval; the reviewer MUST verify
  constitution compliance before approving.
- **CI Gates** (MUST all pass before merge):
  1. `ruff check .` — zero errors
  2. `mypy .` — zero errors
  3. `pytest --cov` — coverage MUST NOT decrease; all tests MUST pass
- **Commit Messages**: MUST follow conventional commit format (`feat:`, `fix:`, `docs:`,
  `chore:`, `refactor:`, `test:`, etc.); ≤ 72 chars subject line; reference task ID where
  applicable.
- **No Force Pushes** to `main`; use revert commits to undo merged changes.

## Governance

This Constitution supersedes all other development practices, style guides, and verbal
agreements. Any practice not addressed here defaults to Python community conventions (PEP 8,
PEP 20).

**Amendment procedure**:
1. Open a PR that edits this file with the proposed change and a version bump.
2. Summarise what principle is added, removed, or changed and why.
3. Obtain approval from at least one other contributor (or document a solo-project waiver).
4. Merge and update `LAST_AMENDED_DATE`.

**Versioning policy**:
- MAJOR: Removal or incompatible redefinition of a principle.
- MINOR: New principle or section, or materially expanded guidance.
- PATCH: Clarifications, wording fixes, typo corrections.

**Compliance review**: Constitution compliance MUST be checked at every PR review. If a
violation is found post-merge, a follow-up fix PR MUST be opened within one working day.

**Version**: 1.1.1 | **Ratified**: 2026-03-24 | **Last Amended**: 2026-03-24
