from __future__ import annotations

from fastapi.testclient import TestClient


class TestAuthSignup:
    def test_signup_success(self, client: TestClient):
        """Cadastro deve retornar 201 com token."""
        resp = client.post(
            "/api/auth/signup",
            json={"email": "novo@teste.com", "password": "123456"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "user_id" in data
        assert "token" in data
        assert data["email"] == "novo@teste.com"

    def test_signup_duplicate_email(self, client: TestClient):
        """Email duplicado deve retornar 409."""
        client.post("/api/auth/signup", json={"email": "dup@teste.com", "password": "123456"})
        resp = client.post("/api/auth/signup", json={"email": "dup@teste.com", "password": "123456"})
        assert resp.status_code == 409
        assert "ja cadastrado" in resp.json()["detail"]

    def test_signup_invalid_data(self, client: TestClient):
        """Dados invalidos retornam 422."""
        resp = client.post("/api/auth/signup", json={"email": "x", "password": "123456"})
        assert resp.status_code == 422


class TestAuthLogin:
    def test_login_success(self, client: TestClient):
        """Login valido retorna token."""
        client.post("/api/auth/signup", json={"email": "login@teste.com", "password": "123456"})
        resp = client.post("/api/auth/login", json={"email": "login@teste.com", "password": "123456"})
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["email"] == "login@teste.com"

    def test_login_wrong_password(self, client: TestClient):
        """Senha errada retorna 401."""
        client.post("/api/auth/signup", json={"email": "wrong@teste.com", "password": "123456"})
        resp = client.post("/api/auth/login", json={"email": "wrong@teste.com", "password": "WRONG"})
        assert resp.status_code == 401

    def test_login_nonexistent(self, client: TestClient):
        """Usuario inexistente retorna 401."""
        resp = client.post("/api/auth/login", json={"email": "no@exists.com", "password": "123456"})
        assert resp.status_code == 401


class TestAuthLogout:
    def test_logout_success(self, client: TestClient):
        """Logout deve invalidar token."""
        signup_resp = client.post("/api/auth/signup", json={"email": "out@teste.com", "password": "123456"})
        token = signup_resp.json()["token"]

        resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

        # Verifica que o token nao funciona mais
        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 401

    def test_logout_without_token(self, client: TestClient):
        """Logout sem token retorna 401."""
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 401


class TestAuthMe:
    def test_me_authenticated(self, client: TestClient):
        """Usuario autenticado recebe dados."""
        signup_resp = client.post("/api/auth/signup", json={"email": "me@teste.com", "password": "123456"})
        token = signup_resp.json()["token"]

        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "me@teste.com"

    def test_me_unauthenticated(self, client: TestClient):
        """Sem token retorna 401."""
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401