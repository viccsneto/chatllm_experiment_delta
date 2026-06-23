from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    def test_signup_success(self, client: TestClient):
        response = client.post(
            "/api/auth/signup",
            json={"email": "novo@teste.com", "password": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["email"] == "novo@teste.com"
        assert data["user_id"] > 0

    def test_signup_duplicate_email(self, client: TestClient):
        client.post("/api/auth/signup", json={"email": "dup@teste.com", "password": "123456"})
        response = client.post(
            "/api/auth/signup",
            json={"email": "dup@teste.com", "password": "654321"},
        )
        assert response.status_code == 409
        assert "ja cadastrado" in response.json()["detail"]

    def test_signup_short_password(self, client: TestClient):
        response = client.post(
            "/api/auth/signup",
            json={"email": "short@teste.com", "password": "12345"},
        )
        assert response.status_code == 422

    def test_login_success(self, client: TestClient):
        client.post("/api/auth/signup", json={"email": "logintest@teste.com", "password": "123456"})
        response = client.post(
            "/api/auth/login",
            json={"email": "logintest@teste.com", "password": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["email"] == "logintest@teste.com"

    def test_login_wrong_password(self, client: TestClient):
        client.post("/api/auth/signup", json={"email": "wrongpw@teste.com", "password": "123456"})
        response = client.post(
            "/api/auth/login",
            json={"email": "wrongpw@teste.com", "password": "errada"},
        )
        assert response.status_code == 401
        assert "invalido" in response.json()["detail"]

    def test_login_nonexistent_email(self, client: TestClient):
        response = client.post(
            "/api/auth/login",
            json={"email": "naoexiste@teste.com", "password": "123456"},
        )
        assert response.status_code == 401

    def test_logout(self, client: TestClient):
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_me_with_token(self, client: TestClient):
        resp = client.post("/api/auth/signup", json={"email": "me@teste.com", "password": "123456"})
        token = resp.json()["token"]
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["email"] == "me@teste.com"

    def test_me_without_token(self, client: TestClient):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_with_expired_token(self, client: TestClient):
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401