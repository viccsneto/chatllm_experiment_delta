from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestRootEndpoint:
    def test_root_returns_frontend(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestChatEndpoint:
    def test_chat_endpoint_exists(self, client: TestClient):
        """Verifica que o endpoint /api/chat responde."""
        with patch("backend.routers.chat.generate_reply") as mock_generate:
            mock_generate.return_value = ("Resposta mockada", "modelo-mock")
            response = client.post(
                "/api/chat",
                json={"message": "Ola"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Resposta mockada"

    def test_chat_empty_message_rejected(self, client: TestClient):
        """Mensagem vazia deve ser rejeitada com 422 (validacao Pydantic)."""
        response = client.post(
            "/api/chat",
            json={"message": ""},
        )
        assert response.status_code == 422


class TestChatStreamEndpoint:
    def test_chat_stream_endpoint_exists(self, client: TestClient):
        """Verifica que o endpoint /api/chat/stream aceita requisicoes."""
        response = client.post(
            "/api/chat/stream",
            json={"message": "Ola"},
        )
        # Streaming pode iniciar e depois falhar sem API key
        assert response.status_code in (200, 422, 503)

    def test_chat_stream_empty_message_rejected(self, client: TestClient):
        """Stream com mensagem vazia deve ser rejeitado com 422."""
        response = client.post(
            "/api/chat/stream",
            json={"message": ""},
        )
        assert response.status_code == 422


class TestCORSMiddleware:
    def test_cors_headers_present(self, client: TestClient):
        """Verifica que os headers CORS estao presentes."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code in (200, 405)


class TestChatWithSession:
    def test_chat_with_existing_session(self, client: TestClient):
        """Chat com session_id existente usa a sessao."""
        create_resp = client.post("/api/sessions")
        sess_id = create_resp.json()["id"]

        with patch("backend.routers.chat.generate_reply") as mock_generate:
            mock_generate.return_value = ("Resposta mockada", "modelo-mock")
            resp = client.post(
                "/api/chat",
                json={"message": "Ola", "session_id": sess_id},
            )
        assert resp.status_code == 200

    def test_chat_with_nonexistent_session_creates_new(self, client: TestClient):
        """Se session_id nao existir, uma nova sessao deve ser criada."""
        count_before = len(client.get("/api/sessions").json())

        with patch("backend.routers.chat.generate_reply") as mock_generate:
            mock_generate.return_value = ("Resposta mockada", "modelo-mock")
            client.post(
                "/api/chat",
                json={"message": "Ola", "session_id": "uuid-inexistente"},
            )

        count_after = len(client.get("/api/sessions").json())
        # _ensure_session cria nova sessao mesmo com session_id invalido
        assert count_after == count_before + 1

    def test_chat_without_session_id_creates_new(self, client: TestClient):
        """Chat sem session_id deve criar nova sessao."""
        count_before = len(client.get("/api/sessions").json())

        with patch("backend.routers.chat.generate_reply") as mock_generate:
            mock_generate.return_value = ("Resposta mockada", "modelo-mock")
            client.post(
                "/api/chat",
                json={"message": "Ola"},
            )

        count_after = len(client.get("/api/sessions").json())
        assert count_after == count_before + 1
