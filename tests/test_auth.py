from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status
from jose import jwt
from pydantic import ValidationError

from backend.config import JWT_ALGORITHM, SECRET_KEY
from backend.models import User
from backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
    SignupRequest,
    SignupResponse,
)
from backend.services.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_user,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("Teste@123")
        assert hashed != "Teste@123"
        assert verify_password("Teste@123", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("Teste@123")
        assert verify_password("Senha@456", hashed) is False

    def test_empty_password_fails(self):
        hashed = hash_password("Teste@123")
        assert verify_password("", hashed) is False

    def test_different_hashes_per_call(self):
        h1 = hash_password("Teste@123")
        h2 = hash_password("Teste@123")
        assert h1 != h2  # bcrypt uses different salt each time


class TestJWTTokens:
    def test_create_and_decode(self):
        token = create_access_token(user_id=1, email="test@test.com")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == "1"
        assert payload["email"] == "test@test.com"
        assert "exp" in payload

    def test_token_contains_email(self):
        token = create_access_token(user_id=42, email="user@example.com")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert payload["email"] == "user@example.com"

    def test_invalid_token_raises_error(self):
        with pytest.raises(Exception):
            jwt.decode("token_invalido", SECRET_KEY, algorithms=[JWT_ALGORITHM])

    def test_expired_token_raises_error(self):
        """Gera um token com expiracao no passado e verifica que falha."""
        from jose import ExpiredSignatureError

        expire = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {"sub": "1", "email": "test@test.com", "exp": expire}
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
        with pytest.raises(ExpiredSignatureError):
            jwt.decode(expired_token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

    def test_token_with_wrong_secret_fails(self):
        token = create_access_token(user_id=1, email="test@test.com")
        with pytest.raises(Exception):
            jwt.decode(token, "wrong_secret_key", algorithms=[JWT_ALGORITHM])


class TestSignupSchema:
    def test_valid_signup(self):
        req = SignupRequest(
            email="usuario@teste.com",
            password="Teste@123",
            password_confirm="Teste@123",
        )
        assert req.email == "usuario@teste.com"

    def test_email_normalized_to_lowercase(self):
        req = SignupRequest(
            email="Usuario@Teste.Com",
            password="Teste@123",
            password_confirm="Teste@123",
        )
        assert req.email == "usuario@teste.com"

    def test_invalid_email_format(self):
        with pytest.raises(ValidationError) as exc:
            SignupRequest(
                email="email_invalido",
                password="Teste@123",
                password_confirm="Teste@123",
            )
        assert "Formato de email invalido" in str(exc.value)

    def test_password_without_number(self):
        with pytest.raises(ValidationError) as exc:
            SignupRequest(
                email="test@test.com",
                password="Senha@aaa",
                password_confirm="Senha@aaa",
            )
        assert "numero" in str(exc.value)

    def test_password_without_special_char(self):
        with pytest.raises(ValidationError) as exc:
            SignupRequest(
                email="test@test.com",
                password="Senha1234",
                password_confirm="Senha1234",
            )
        assert "especial" in str(exc.value)

    def test_passwords_do_not_match(self):
        with pytest.raises(ValidationError) as exc:
            SignupRequest(
                email="test@test.com",
                password="Teste@123",
                password_confirm="Outra@456",
            )
        assert "nao conferem" in str(exc.value)

    def test_signup_response_serialization(self):
        resp = SignupResponse(id=1, email="test@test.com")
        assert resp.message == "Cadastro realizado com sucesso!"


class TestLoginSchema:
    def test_valid_login(self):
        req = LoginRequest(email="test@test.com", password="Teste@123")
        assert req.email == "test@test.com"

    def test_blank_password(self):
        with pytest.raises(ValidationError) as exc:
            LoginRequest(email="test@test.com", password="")
        assert "em branco" in str(exc.value)

    def test_empty_email(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="", password="Teste@123")

    def test_login_response_serialization(self):
        resp = LoginResponse(
            access_token="fake_token",
            email="test@test.com",
        )
        assert resp.token_type == "bearer"
        assert resp.message == "Login realizado com sucesso!"


class TestAuthAPI:
    """Testes de integracao dos endpoints de autenticacao."""

    def test_signup_success(self, client):
        resp = client.post(
            "/api/auth/signup",
            json={
                "email": "novo@teste.com",
                "password": "Valido@123",
                "password_confirm": "Valido@123",
            },
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["email"] == "novo@teste.com"
        assert "id" in data

    def test_signup_duplicate_email(self, client):
        # Cria o primeiro usuario
        client.post(
            "/api/auth/signup",
            json={
                "email": "duplicado@teste.com",
                "password": "Valido@123",
                "password_confirm": "Valido@123",
            },
        )
        # Tenta criar o mesmo email
        resp = client.post(
            "/api/auth/signup",
            json={
                "email": "duplicado@teste.com",
                "password": "Outra@456",
                "password_confirm": "Outra@456",
            },
        )
        assert resp.status_code == status.HTTP_409_CONFLICT
        assert "ja esta cadastrado" in resp.json()["detail"]

    def test_login_success(self, client):
        # Primeiro cadastra
        client.post(
            "/api/auth/signup",
            json={
                "email": "logintest@teste.com",
                "password": "Login@123",
                "password_confirm": "Login@123",
            },
        )
        # Depois faz login
        resp = client.post(
            "/api/auth/login",
            json={"email": "logintest@teste.com", "password": "Login@123"},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "access_token" in data
        assert data["email"] == "logintest@teste.com"

    def test_login_wrong_password(self, client):
        # Primeiro cadastra
        client.post(
            "/api/auth/signup",
            json={
                "email": "wrongpwd@teste.com",
                "password": "Senha@123",
                "password_confirm": "Senha@123",
            },
        )
        # Login com senha errada
        resp = client.post(
            "/api/auth/login",
            json={"email": "wrongpwd@teste.com", "password": "Errada@456"},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorretos" in resp.json()["detail"]

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"email": "naoexiste@teste.com", "password": "Qualquer@1"},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorretos" in resp.json()["detail"]

    def test_check_auth_with_valid_token(self, client):
        # Cadastra e loga
        client.post(
            "/api/auth/signup",
            json={
                "email": "checktest@teste.com",
                "password": "Valid@123",
                "password_confirm": "Valid@123",
            },
        )
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "checktest@teste.com", "password": "Valid@123"},
        )
        token = login_resp.json()["access_token"]

        # Verifica token valido
        resp = client.get(
            "/api/auth/check",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["email"] == "checktest@teste.com"

    def test_check_auth_without_token(self, client):
        resp = client.get("/api/auth/check")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() is None

    def test_check_auth_with_invalid_token(self, client):
        resp = client.get(
            "/api/auth/check",
            headers={"Authorization": "Bearer token_invalido_aqui"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() is None

    def test_check_auth_with_expired_token(self, client):
        """Token com expiracao no passado deve retornar None."""
        from jose import jwt as jose_jwt

        expire = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {"sub": "1", "email": "old@teste.com", "exp": expire}
        expired_token = jose_jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

        resp = client.get(
            "/api/auth/check",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() is None

    def test_protected_route_without_token(self, client):
        """POST /api/auth/me (require_user) sem token deve dar 401."""
        resp = client.post("/api/auth/me")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Autenticacao necessaria" in resp.json()["detail"]

    def test_protected_route_with_invalid_token(self, client):
        resp = client.post(
            "/api/auth/me",
            headers={"Authorization": "Bearer token_qualquer_invalido"},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalido" in resp.json()["detail"]