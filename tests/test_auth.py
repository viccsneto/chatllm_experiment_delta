from __future__ import annotations

from fastapi.testclient import TestClient


class TestAuth:
    def test_signup_creates_user(self, client: TestClient):
        """Cadastro deve retornar token e email."""
        response = client.post(
            "/api/auth/signup",
            json={"email": "teste@example.com", "password": "123456"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert data["email"] == "teste@example.com"

    def test_signup_duplicate_email(self, client: TestClient):
        """Email duplicado deve retornar 409."""
        client.post(
            "/api/auth/signup",
            json={"email": "dup@example.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/signup",
            json={"email": "dup@example.com", "password": "123456"},
        )
        assert response.status_code == 409

    def test_login_success(self, client: TestClient):
        """Login com credenciais corretas deve retornar token."""
        client.post(
            "/api/auth/signup",
            json={"email": "login@example.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["email"] == "login@example.com"

    def test_login_wrong_password(self, client: TestClient):
        """Senha errada deve retornar 401."""
        client.post(
            "/api/auth/signup",
            json={"email": "wrong@example.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpass"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_email(self, client: TestClient):
        """Email inexistente deve retornar 401."""
        response = client.post(
            "/api/auth/login",
            json={"email": "noone@example.com", "password": "123456"},
        )
        assert response.status_code == 401

    def test_me_authenticated(self, client: TestClient):
        """GET /api/auth/me com token valido deve retornar email."""
        signup_resp = client.post(
            "/api/auth/signup",
            json={"email": "me@example.com", "password": "123456"},
        )
        token = signup_resp.json()["token"]

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "me@example.com"

    def test_me_unauthenticated(self, client: TestClient):
        """GET /api/auth/me sem token deve retornar 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_logout_invalidates_token(self, client: TestClient):
        """Apos logout, o token deve ser invalidado."""
        signup_resp = client.post(
            "/api/auth/signup",
            json={"email": "logout@example.com", "password": "123456"},
        )
        token = signup_resp.json()["token"]

        # Logout
        logout_resp = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_resp.status_code == 200

        # Token deve estar invalidado
        me_resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 401

    def test_signup_case_insensitive_email(self, client: TestClient):
        """Emails com diferencas de case devem ser tratados como iguais."""
        client.post(
            "/api/auth/signup",
            json={"email": "Case@Example.com", "password": "123456"},
        )
        response = client.post(
            "/api/auth/signup",
            json={"email": "case@example.com", "password": "123456"},
        )
        assert response.status_code == 409
