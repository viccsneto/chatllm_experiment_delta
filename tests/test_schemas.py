from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.schemas.chat import (
    ChatMessageIn,
    ChatRequest,
    ChatRequestWithSession,
    ChatResponse,
    SessionCreate,
    SessionResponse,
    SessionTitleUpdate,
)


class TestChatMessageIn:
    def test_valid_user_message(self):
        msg = ChatMessageIn(role="user", content="Ola!")
        assert msg.role == "user"
        assert msg.content == "Ola!"

    def test_valid_assistant_message(self):
        msg = ChatMessageIn(role="assistant", content="Resposta.")
        assert msg.role == "assistant"
        assert msg.content == "Resposta."

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            ChatMessageIn(role="system", content="Nao permitido")

    def test_empty_content(self):
        with pytest.raises(ValidationError):
            ChatMessageIn(role="user", content="")

    def test_content_too_long(self):
        with pytest.raises(ValidationError):
            ChatMessageIn(role="user", content="x" * 8001)


class TestChatRequest:
    def test_valid_request_minimal(self):
        req = ChatRequest(message="Hello")
        assert req.message == "Hello"
        assert req.model is None
        assert req.history == []

    def test_valid_request_with_model(self):
        req = ChatRequest(message="Hi", model="openai/gpt-4o")
        assert req.model == "openai/gpt-4o"

    def test_valid_request_with_history(self):
        history = [
            ChatMessageIn(role="user", content="pergunta"),
            ChatMessageIn(role="assistant", content="resposta"),
        ]
        req = ChatRequest(message="continuacao", history=history)
        assert len(req.history) == 2
        assert req.history[0].role == "user"

    def test_empty_message(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_message_too_long(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="x" * 8001)

    def test_history_defaults_to_empty(self):
        req = ChatRequest(message="Hello")
        assert req.history == []


class TestChatResponse:
    def test_valid_response(self):
        resp = ChatResponse(reply="Resposta do modelo.", model="google/gemma-4-31b-it")
        assert resp.reply == "Resposta do modelo."
        assert resp.model == "google/gemma-4-31b-it"


class TestSessionCreate:
    def test_create_empty(self):
        """SessionCreate nao requer campos."""
        req = SessionCreate()
        assert req is not None


class TestSessionResponse:
    def test_valid_response(self):
        """SessionResponse deve aceitar campos obrigatorios."""
        resp = SessionResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            title="Minha Sessao",
            created_at="2026-06-21T10:00:00",
            updated_at="2026-06-21T10:30:00",
        )
        assert resp.id == "550e8400-e29b-41d4-a716-446655440000"
        assert resp.title == "Minha Sessao"

    def test_response_title_none(self):
        """SessionResponse aceita title=None."""
        resp = SessionResponse(
            id="abc", created_at="2026-01-01T00:00:00", updated_at="2026-01-01T00:00:00"
        )
        assert resp.title is None


class TestSessionTitleUpdate:
    def test_valid_title(self):
        req = SessionTitleUpdate(title="Novo Titulo")
        assert req.title == "Novo Titulo"

    def test_empty_title(self):
        with pytest.raises(ValidationError):
            SessionTitleUpdate(title="")

    def test_title_too_long(self):
        with pytest.raises(ValidationError):
            SessionTitleUpdate(title="x" * 256)


class TestChatRequestWithSession:
    def test_without_session_id(self):
        req = ChatRequestWithSession(message="Ola")
        assert req.session_id is None
        assert req.message == "Ola"

    def test_with_session_id(self):
        req = ChatRequestWithSession(message="Ola", session_id="abc-123")
        assert req.session_id == "abc-123"
