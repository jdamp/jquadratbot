"""Shared pytest fixtures for unit and integration tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Chat, Message, PhotoSize, Update, User
from telegram.ext import ContextTypes


def _make_minimal_jpeg() -> bytes:
    """Return a minimal valid JPEG (1×1 white pixel)."""
    return bytes(
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
        b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
        b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1e"
        b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
        b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
        b"\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04"
        b"\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa"
        b"\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br"
        b"\x82\t\n\x16\x17\x18\x19\x1a%&'()*456789:CDEFGHIJ"
        b"STUVWXYZ\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd4P\x00\x00\x00\xff\xd9"
    )


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Return minimal valid JPEG bytes usable as an image payload."""
    return _make_minimal_jpeg()


@pytest.fixture
def mock_telegram_user() -> MagicMock:
    user = MagicMock(spec=User)
    user.id = 12345
    user.first_name = "Test"
    user.username = "testuser"
    return user


@pytest.fixture
def mock_chat() -> MagicMock:
    chat = MagicMock(spec=Chat)
    chat.id = 67890
    return chat


@pytest.fixture
def mock_photo_size(sample_image_bytes: bytes) -> MagicMock:
    photo = MagicMock(spec=PhotoSize)
    photo.file_id = "file_id_123"
    photo.file_size = len(sample_image_bytes)
    photo.width = 1
    photo.height = 1
    mock_file = AsyncMock()
    mock_file.download_as_bytearray = AsyncMock(return_value=bytearray(sample_image_bytes))
    photo.get_file = AsyncMock(return_value=mock_file)
    return photo


@pytest.fixture
def mock_message(mock_telegram_user: MagicMock, mock_chat: MagicMock) -> MagicMock:
    msg = MagicMock(spec=Message)
    msg.from_user = mock_telegram_user
    msg.chat = mock_chat
    msg.chat_id = mock_chat.id
    msg.message_id = 1
    msg.photo = []
    msg.caption = None
    msg.text = None
    msg.reply_to_message = None
    msg.reply_text = AsyncMock()
    msg.reply_photo = AsyncMock()
    return msg


@pytest.fixture
def mock_update(mock_message: MagicMock, mock_chat: MagicMock) -> MagicMock:
    update = MagicMock(spec=Update)
    update.message = mock_message
    update.effective_chat = mock_chat
    update.effective_user = mock_message.from_user
    return update


@pytest.fixture
def mock_ptb_context() -> MagicMock:
    ctx = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    ctx.bot = AsyncMock()
    ctx.error = None
    return ctx


@pytest.fixture
def mock_genai_client() -> MagicMock:
    """Return a MagicMock mimicking google.genai.Client with an aio namespace."""
    client = MagicMock()
    # aio.models.generate_content (async)
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock()
    # aio.chats.create returns a mock chat object
    mock_chat = MagicMock()
    mock_chat.send_message = AsyncMock()
    mock_chat.get_history = MagicMock(return_value=[])
    client.aio.chats = MagicMock()
    # chats.create() is a synchronous call that returns an AsyncChat object
    client.aio.chats.create = MagicMock(return_value=mock_chat)
    return client
