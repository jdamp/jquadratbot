"""Unit tests for ChatSession and context registry — TDD: written before implementation."""

from datetime import UTC, datetime, timedelta

from src.gemini.context import ChatSession, get_or_create_session, reset_session, sessions


class TestChatSessionExpiry:
    def test_new_session_has_empty_history(self) -> None:
        session = ChatSession(chat_id=1, history=[], last_active=datetime.now(UTC))
        assert session.history == []

    def test_is_expired_returns_false_within_timeout(self) -> None:
        session = ChatSession(
            chat_id=1,
            history=[],
            last_active=datetime.now(UTC) - timedelta(minutes=30),
        )
        assert session.is_expired(timeout_minutes=60) is False

    def test_is_expired_returns_true_after_timeout(self) -> None:
        session = ChatSession(
            chat_id=1,
            history=[],
            last_active=datetime.now(UTC) - timedelta(minutes=61),
        )
        assert session.is_expired(timeout_minutes=60) is True

    def test_is_expired_exactly_at_boundary_is_expired(self) -> None:
        session = ChatSession(
            chat_id=1,
            history=[],
            last_active=datetime.now(UTC) - timedelta(minutes=60),
        )
        assert session.is_expired(timeout_minutes=60) is True


class TestSessionRegistry:
    def setup_method(self) -> None:
        sessions.clear()

    def test_get_or_create_returns_new_session_for_unknown_chat(self) -> None:
        session = get_or_create_session(chat_id=42)
        assert session.chat_id == 42
        assert session.history == []

    def test_get_or_create_returns_same_session_on_second_call(self) -> None:
        s1 = get_or_create_session(chat_id=99)
        s2 = get_or_create_session(chat_id=99)
        assert s1 is s2

    def test_two_different_chat_ids_are_independent(self) -> None:
        s1 = get_or_create_session(chat_id=1)
        s2 = get_or_create_session(chat_id=2)
        assert s1 is not s2
        assert s1.chat_id != s2.chat_id

    def test_reset_session_removes_entry(self) -> None:
        get_or_create_session(chat_id=10)
        assert 10 in sessions
        reset_session(chat_id=10)
        assert 10 not in sessions

    def test_reset_nonexistent_session_does_not_raise(self) -> None:
        reset_session(chat_id=999)  # should not raise

    def test_last_active_is_set_on_creation(self) -> None:
        before = datetime.now(UTC)
        session = get_or_create_session(chat_id=5)
        after = datetime.now(UTC)
        assert before <= session.last_active <= after
