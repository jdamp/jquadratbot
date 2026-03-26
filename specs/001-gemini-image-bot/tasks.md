# Tasks: Gemini Image Bot

**Feature**: 001-gemini-image-bot
**Input**: Design documents from `/specs/001-gemini-image-bot/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/commands.md ✅, quickstart.md ✅

**Tests**: Included — TDD mandated by project constitution (Section II: Testing Standards; ≥80% coverage required)

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in all task descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — all paths and dependencies established before any coding begins.

- [X] T001 Create pyproject.toml with Python 3.14 as requires-python, dependencies (python-telegram-bot≥21.0, google-genai≥1.14.0, python-dotenv), dev dependencies (pytest, pytest-asyncio, pytest-cov, ruff, mypy), and ruff/mypy config sections at pyproject.toml
- [X] T002 [P] Create .gitignore (covering .env, __pycache__, .venv, *.pyc) and .env.example documenting TELEGRAM_TOKEN, GEMINI_API_KEY, SESSION_TIMEOUT_MINUTES=60, MAX_IMAGE_SIZE_BYTES=10485760, GEMINI_MODEL=gemini-3.1-flash-image-preview at .gitignore and .env.example
- [X] T003 [P] Create src/ package skeleton: src/__init__.py, src/gemini/__init__.py, src/handlers/__init__.py (empty files establishing import paths)
- [X] T004 [P] Create tests/ directory skeleton: tests/__init__.py, tests/unit/__init__.py, tests/integration/__init__.py (empty files establishing test package structure)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that ALL user stories depend on. No user story work begins until this phase is complete.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Write unit tests for BotConfig in tests/unit/test_config.py — cover: missing TELEGRAM_TOKEN raises SystemExit, missing GEMINI_API_KEY raises SystemExit, non-positive SESSION_TIMEOUT_MINUTES raises ValueError, valid env vars produce correct BotConfig field values (TDD — must fail before T007)
- [X] T006 [P] Write unit tests for ChatSession in tests/unit/test_context.py — cover: new session has empty history, is_expired() returns True after timeout, is_expired() returns False within timeout, last_active updates on access, two different chat_ids have independent sessions (TDD — must fail before T008)
- [X] T007 Implement BotConfig dataclass in src/config.py: read TELEGRAM_TOKEN, GEMINI_API_KEY (sys.exit if either missing), SESSION_TIMEOUT_MINUTES (default 60), MAX_IMAGE_SIZE_BYTES (default 10_485_760), GEMINI_MODEL (default "gemini-3.1-flash-image-preview") from environment; all fields type-annotated; passes T005 tests
- [X] T008 Implement ChatSession dataclass and sessions registry in src/context.py: ChatSession with chat_id: int, history: list[types.Content], last_active: datetime; is_expired(timeout_minutes: int) -> bool; get_or_create_session(chat_id: int) -> ChatSession; reset_session(chat_id: int) -> None; module-level sessions: dict[int, ChatSession]; passes T006 tests
- [X] T009 Implement async Gemini client factory in src/gemini/client.py: create_client(config: BotConfig) -> genai.Client initialised with google-genai Client(api_key=config.gemini_api_key); expose as module-level singleton to be initialised at bot startup
- [X] T010 [P] Implement /help, /start, unknown command, and global PTB error handler in src/handlers/common.py: /start and /help reply with the formatted command list from contracts/commands.md; unknown slash command replies "I don't know that command." + help list; error handler logs exception and replies with Gemini API error message without exposing internals
- [X] T011 Create tests/conftest.py with shared pytest fixtures: mock_update (AsyncMock PTB Update with message, photo, caption), mock_context (AsyncMock PTB ContextTypes.DEFAULT_TYPE), mock_genai_client (MagicMock genai.Client with aio namespace), sample_image_bytes (minimal valid JPEG bytes for use as image payload)
- [X] T012 Implement ApplicationBuilder setup in src/bot.py: build Application with TELEGRAM_TOKEN from BotConfig, register common handlers from src/handlers/common.py (/start, /help, MessageHandler with filters.COMMAND for unknown commands, error_handler), call app.run_polling() in main(); add if __name__ == "__main__": main() guard

**Checkpoint**: Foundation ready — bot starts, responds to /start and /help, handles unknown commands; unit tests for BotConfig and ChatSession pass.

---

## Phase 3: User Story 1 — Image Interpretation (Priority: P1) 🎯 MVP

**Goal**: Family member sends a photo with /interpret and receives a natural-language description. Follow-up questions use stored context without re-uploading. /reset clears context on demand.

**Independent Test**: `uv run pytest tests/unit/test_gemini_interpret.py tests/integration/test_interpret_handler.py -v`

### Tests for User Story 1 (TDD — write first, verify they FAIL, then implement)

- [X] T013 [P] [US1] Write unit tests for interpret Gemini logic in tests/unit/test_gemini_interpret.py — cover: interpret with new image builds history and returns text response, interpret follow-up uses stored session history without re-uploading image, expired session clears history before interpreting, Gemini API exception propagates as GeminiError (TDD)
- [X] T014 [P] [US1] Write integration tests for /interpret handler in tests/integration/test_interpret_handler.py — cover: photo+caption sends ACK "Analysing your image…" then description reply, photo-only sends general description, text-only follow-up with active session answers using context, no-image-no-context replies "I need an image to work with…", Gemini error replies with API error message, expired session informs user context was cleared (TDD)

### Implementation for User Story 1

- [X] T015 [US1] Implement interpret_image(client, config, session, image_payload, question) async function in src/gemini/interpret.py: build types.Content with image bytes (types.Part.from_bytes) and optional question text, call client.aio.chats.create(model=config.gemini_model, history=session.history), await chat.send_message(new_turn), store updated history via chat.get_history() back into session, return response text; raise GeminiError on API failure
- [X] T016 [US1] Implement /interpret command handler in src/handlers/interpret.py: extract PhotoSize[-1] from message or fall back to session context; reply error if no image and no context; check file_size ≤ config.max_image_size_bytes (error if exceeded); download bytes via File.download_as_bytearray(); check session expiry and notify if expired; send "Analysing your image…" ACK; await gemini.interpret_image(); reply with result text; handle GeminiError per contracts/commands.md
- [X] T017 [US1] Register /interpret handler with filters.COMMAND in src/bot.py (update ApplicationBuilder setup to add CommandHandler("interpret", interpret_handler))
- [X] T018 [US1] Implement /reset command handler in src/handlers/reset.py: call context.reset_session(update.effective_chat.id); reply "Conversation cleared. I've forgotten our previous images…" if session existed; reply "There's nothing to clear…" if no active session; per contracts/commands.md
- [X] T019 [US1] Register /reset handler with filters.COMMAND in src/bot.py (update ApplicationBuilder setup to add CommandHandler("reset", reset_handler))

**Checkpoint**: /interpret and /reset fully functional. Follow-up questions answer using stored context. Session expiry notifies user. All US1 tests pass.

---

## Phase 4: User Story 2 — Image Generation (Priority: P2)

**Goal**: Family member sends /generate with a text description and receives a generated image within 30 seconds, preceded by an acknowledgement within 3 seconds.

**Independent Test**: `uv run pytest tests/unit/test_gemini_generate.py tests/integration/test_generate_handler.py -v`

### Tests for User Story 2 (TDD — write first, verify they FAIL, then implement)

- [X] T020 [P] [US2] Write unit tests for generate Gemini logic in tests/unit/test_gemini_generate.py — cover: successful generate returns non-empty image bytes, content policy safety block raises ContentPolicyError, Gemini API exception raises GeminiError, empty prompt string raises ValueError (TDD)
- [X] T021 [P] [US2] Write integration tests for /generate handler in tests/integration/test_generate_handler.py — cover: valid prompt sends ACK "Generating your image…" then replies with photo, missing prompt replies with usage example error message, policy violation replies "I wasn't able to generate that image…", Gemini API error replies with API error message (TDD)

### Implementation for User Story 2

- [X] T022 [US2] Implement generate_image(client, config, prompt) async function in src/gemini/generate.py: call client.aio.models.generate_content(model=config.gemini_model, contents=prompt, config=types.GenerateContentConfig(response_modalities=["image", "text"])); extract image bytes from response.candidates[0].content.parts; raise ContentPolicyError if response blocked by safety filters; raise GeminiError on API failure
- [X] T023 [US2] Implement /generate command handler in src/handlers/generate.py: extract prompt by stripping the /generate command prefix from message text; reply with usage example error if prompt is empty; send "Generating your image…" ACK; await gemini.generate_image(); send photo via update.message.reply_photo(BytesIO(image_bytes)); handle ContentPolicyError and GeminiError per contracts/commands.md
- [X] T024 [US2] Register /generate handler with filters.COMMAND in src/bot.py (update ApplicationBuilder setup to add CommandHandler("generate", generate_handler))

**Checkpoint**: /generate fully functional. Valid text prompts return a generated image as a Telegram photo. All US2 tests pass.

---

## Phase 5: User Story 3 — Image Modification (Priority: P3)

**Goal**: Family member provides an image (attachment or reply to existing photo) plus a text instruction; bot returns the visibly modified image.

**Independent Test**: `uv run pytest tests/unit/test_gemini_modify.py tests/integration/test_modify_handler.py -v`

### Tests for User Story 3 (TDD — write first, verify they FAIL, then implement)

- [X] T025 [P] [US3] Write unit tests for modify Gemini logic in tests/unit/test_gemini_modify.py — cover: successful modify returns non-empty modified image bytes, unsupported modification (safety block) raises ContentPolicyError, Gemini API exception raises GeminiError (TDD)
- [X] T026 [P] [US3] Write integration tests for /modify handler in tests/integration/test_modify_handler.py — cover: photo+instruction sends ACK "Modifying your image…" then replies with modified photo, reply-to-photo+instruction resolves photo from replied message and modifies it, no image (no attachment, not a reply to photo) replies "I need an image to modify…", no instruction text replies usage example error, Gemini API error replies with API error message (TDD)

### Implementation for User Story 3

- [X] T027 [US3] Implement modify_image(client, config, image_payload, instruction) async function in src/gemini/modify.py: build content with image bytes (types.Part.from_bytes) and instruction text, call client.aio.models.generate_content(model=config.gemini_model, contents=[image_part, text_part], config=types.GenerateContentConfig(response_modalities=["image", "text"])); extract modified image bytes from response; raise ContentPolicyError on safety block; raise GeminiError on API failure
- [X] T028 [US3] Implement /modify command handler in src/handlers/modify.py: resolve photo from direct message attachment (PhotoSize[-1]) or from update.message.reply_to_message.photo[-1] if this is a reply to a photo; reply "I need an image to modify…" if neither present; extract instruction by stripping /modify prefix; reply usage error if instruction empty; check file_size limit; download bytes; send "Modifying your image…" ACK; await gemini.modify_image(); reply with modified photo; handle all error cases per contracts/commands.md
- [X] T029 [US3] Register /modify handler with filters.COMMAND in src/bot.py (update ApplicationBuilder setup to add CommandHandler("modify", modify_handler))

**Checkpoint**: /modify fully functional. Both direct attachment and reply-to-photo patterns work. All US3 tests pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Complete error-path test coverage, static analysis, and end-to-end validation across all stories.

- [X] T030 [P] Write integration tests covering all error conditions from contracts/commands.md in tests/integration/test_error_handling.py — cover: oversized image on /interpret and /modify, non-image media attachment on /interpret and /modify, unknown slash command /foo replies "I don't know that command." + help list, /interpret with no image and no context, /generate with no prompt text, /modify with no image, /modify with no instruction; assert exact error message strings match contracts
- [X] T031 [P] Run uv run ruff check . and uv run mypy . and fix all reported errors until both exit with zero issues across src/ and tests/
- [ ] T032 Run the eight verification scenarios from quickstart.md Section 6 against a locally running bot with valid TELEGRAM_TOKEN and GEMINI_API_KEY in .env: /start, /help, /reset (empty), /interpret with photo, /generate with description, /modify by reply, unknown command /foo, /interpret with no photo and no context

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — can begin once Foundational checkpoint passes
- **US2 (Phase 4)**: Depends on Phase 2 — can begin independently of US1
- **US3 (Phase 5)**: Depends on Phase 2 — can begin independently of US1 and US2
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: No dependency on US2 or US3 — fully independent after Phase 2
- **US2 (P2)**: No dependency on US1 or US3 — fully independent after Phase 2
- **US3 (P3)**: No dependency on US1 or US2 — fully independent after Phase 2

### Within Each User Story

- TDD test files MUST be written before implementation — verify tests FAIL first
- Gemini logic (src/gemini/*.py) before handler (src/handlers/*.py)
- Handler before bot.py registration
- Story complete and all tests green before marking phase done

### Parallel Opportunities

- T002, T003, T004 can run in parallel alongside T001 (different files)
- T005 and T006 can run in parallel (different test files)
- T010 and T011 can run in parallel (different files, no mutual dependency)
- T013 and T014 can run in parallel (different test files)
- T020 and T021 can run in parallel (different test files)
- T025 and T026 can run in parallel (different test files)
- T030 and T031 can run in parallel (different concerns)
- US1, US2, and US3 phases can be worked in parallel by different developers once Phase 2 is complete

---

## Parallel Example: User Story 1

```bash
# Step 1 — Write both TDD test files simultaneously:
Task T013: "Write unit tests for interpret Gemini logic in tests/unit/test_gemini_interpret.py"
Task T014: "Write integration tests for /interpret handler in tests/integration/test_interpret_handler.py"

# Step 2 — Verify tests FAIL (no implementation yet)
uv run pytest tests/unit/test_gemini_interpret.py tests/integration/test_interpret_handler.py

# Step 3 — Implement sequentially (each depends on prior):
Task T015: "Implement interpret_image() in src/gemini/interpret.py"
Task T016: "Implement /interpret handler in src/handlers/interpret.py"
Task T017: "Register /interpret handler in src/bot.py"
Task T018: "Implement /reset handler in src/handlers/reset.py"
Task T019: "Register /reset handler in src/bot.py"

# Step 4 — Verify all US1 tests pass:
uv run pytest tests/unit/test_gemini_interpret.py tests/integration/test_interpret_handler.py -v
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (/interpret + /reset)
4. **STOP and VALIDATE**: `uv run pytest tests/unit/test_gemini_interpret.py tests/integration/test_interpret_handler.py -v`
5. Run the bot locally (`uv run python -m src.bot`) and manually test /interpret with a real photo

### Incremental Delivery

1. Setup + Foundational → Bot starts, /help and /start work
2. Add US1 (/interpret + /reset) → Test independently → Family can interpret images
3. Add US2 (/generate) → Test independently → Family can generate images
4. Add US3 (/modify) → Test independently → Full feature set complete
5. Polish: cross-cutting error tests, lint/type check, quickstart validation

### Parallel Team Strategy

With multiple developers:

1. All: Complete Setup + Foundational together
2. Once Foundational checkpoint passes:
   - Developer A: US1 (Image Interpretation + Reset)
   - Developer B: US2 (Image Generation)
   - Developer C: US3 (Image Modification)
3. All: Polish phase after all stories complete

---

## Notes

- [P] tasks operate on different files with no dependency on incomplete work — safe to parallelise
- [Story] label maps each task to its user story for traceability and independent testability
- TDD: every test file is written first and must FAIL before implementation begins
- All Gemini API calls must use `client.aio.*` (async) — never block the PTB event loop
- `GEMINI_MODEL` must always be read from `config.gemini_model`, never hard-coded — preview model name will change at GA
- Run `uv run ruff check . && uv run mypy .` before each commit
- Commit after each checkpoint or logical task group
