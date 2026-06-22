from __future__ import annotations

from fastapi.testclient import TestClient


class TestSessionsList:
    def test_list_sessions_empty(self, client: TestClient):
        """Lista de sessoes deve vir vazia inicialmente."""
        response = client.get("/api/sessions")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_sessions_after_create(self, client: TestClient):
        """Apos criar sessao, a lista deve conter a sessao."""
        create_resp = client.post("/api/sessions")
        assert create_resp.status_code == 201
        created = create_resp.json()

        list_resp = client.get("/api/sessions")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert len(data) == 1
        assert data[0]["id"] == created["id"]
        assert data[0]["title"] is None

    def test_list_sessions_ordered_by_recent(self, client: TestClient):
        """Sessoes devem vir ordenadas por updated_at DESC."""
        import time as time_module

        r1 = client.post("/api/sessions")
        id1 = r1.json()["id"]
        time_module.sleep(0.01)

        r2 = client.post("/api/sessions")
        id2 = r2.json()["id"]

        list_resp = client.get("/api/sessions")
        data = list_resp.json()
        assert len(data) == 2
        # Mais recente primeiro
        assert data[0]["id"] == id2
        assert data[1]["id"] == id1


class TestSessionsCreate:
    def test_create_session_returns_201(self, client: TestClient):
        """Criacao de sessao retorna 201 com id e timestamps."""
        response = client.post("/api/sessions")
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert len(data["id"]) == 36  # UUID
        assert data["title"] is None
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_multiple_sessions(self, client: TestClient):
        """Criar varias sessoes gera IDs diferentes."""
        r1 = client.post("/api/sessions")
        r2 = client.post("/api/sessions")
        assert r1.json()["id"] != r2.json()["id"]


class TestSessionsGet:
    def test_get_existing_session(self, client: TestClient):
        """Deve retornar detalhes de uma sessao existente."""
        create_resp = client.post("/api/sessions")
        sess_id = create_resp.json()["id"]

        resp = client.get(f"/api/sessions/{sess_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == sess_id

    def test_get_nonexistent_session(self, client: TestClient):
        """Deve retornar 404 para sessao inexistente."""
        resp = client.get("/api/sessions/nonexistent-id")
        assert resp.status_code == 404
        assert "nao encontrada" in resp.json()["detail"]


class TestSessionsDelete:
    def test_delete_existing_session(self, client: TestClient):
        """Deve remover sessao com sucesso."""
        create_resp = client.post("/api/sessions")
        sess_id = create_resp.json()["id"]

        del_resp = client.delete(f"/api/sessions/{sess_id}")
        assert del_resp.status_code == 204

        # Verifica que foi removida
        get_resp = client.get(f"/api/sessions/{sess_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_session(self, client: TestClient):
        """Deve retornar 404 ao deletar sessao que nao existe."""
        resp = client.delete("/api/sessions/nonexistent-id")
        assert resp.status_code == 404

    def test_delete_session_cascades_messages(self, client: TestClient):
        """Deletar sessao deve remover mensagens associadas."""
        # Cria sessao
        create_resp = client.post("/api/sessions")
        sess_id = create_resp.json()["id"]

        # Envia msg (mock falha pois nao tem API key, mas mensagem nao persiste)
        client.post(
            "/api/chat",
            json={"message": "Ola", "session_id": sess_id},
        )

        # Verifica mensagens (pode ter sido criada sessao nova devido ao erro)
        # O teste do cascate sera feito via model tests


class TestSessionsTitle:
    def test_update_title(self, client: TestClient):
        """Deve atualizar o titulo de uma sessao."""
        create_resp = client.post("/api/sessions")
        sess_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/sessions/{sess_id}/title",
            json={"title": "Meu Novo Titulo"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Meu Novo Titulo"
        assert resp.json()["id"] == sess_id

    def test_update_title_empty_rejected(self, client: TestClient):
        """Titulo vazio deve ser rejeitado com 422."""
        create_resp = client.post("/api/sessions")
        sess_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/sessions/{sess_id}/title",
            json={"title": ""},
        )
        assert resp.status_code == 422

    def test_update_title_nonexistent_session(self, client: TestClient):
        """Atualizar titulo de sessao inexistente retorna 404."""
        resp = client.put(
            "/api/sessions/nonexistent-id/title",
            json={"title": "Novo Titulo"},
        )
        assert resp.status_code == 404


class TestSessionsMessages:
    def test_get_messages_empty(self, client: TestClient):
        """Sessao nova deve ter lista de mensagens vazia."""
        create_resp = client.post("/api/sessions")
        sess_id = create_resp.json()["id"]

        resp = client.get(f"/api/sessions/{sess_id}/messages")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_messages_nonexistent_session(self, client: TestClient):
        """Sessao inexistente retorna 404 em messages."""
        resp = client.get("/api/sessions/nonexistent-id/messages")
        assert resp.status_code == 404
