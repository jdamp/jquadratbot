"""ChatSession dataclass and in-memory session registry with expiry logic."""

from dataclasses import dataclass
from datetime import UTC, datetime

from google.genai import types


@dataclass
class ChatSession:
    chat_id: int
    history: list[types.Content]
    last_active: datetime

    def is_expired(self, timeout_minutes: int) -> bool:
        """Return True if the session has been idle longer than timeout_minutes."""
        elapsed = datetime.now(UTC) - self.last_active
        return elapsed.total_seconds() >= timeout_minutes * 60


# Module-level in-memory registry keyed by Telegram chat_id.
sessions: dict[int, ChatSession] = {}


def get_or_create_session(chat_id: int) -> ChatSession:
    """Return the existing ChatSession for chat_id, or create a new one."""
    if chat_id not in sessions:
        sessions[chat_id] = ChatSession(
            chat_id=chat_id,
            history=[],
            last_active=datetime.now(UTC),
        )
    return sessions[chat_id]


def reset_session(chat_id: int) -> None:
    """Remove the ChatSession for chat_id, if it exists."""
    sessions.pop(chat_id, None)
