from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.schemas.auth import AuthSignup, AuthLogin, AuthResponse, AuthMe


class TestAuthSignup:
    def test_valid(self):
        req = AuthSignup(email="user@test.com", password="123456")
        assert req.email == "user@test.com"
        assert req.password == "123456"

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            AuthSignup(email="user@test.com", password="12345")

    def test_email_too_short(self):
        with pytest.raises(ValidationError):
            AuthSignup(email="ab", password="123456")


class TestAuthLogin:
    def test_valid(self):
        req = AuthLogin(email="user@test.com", password="abc")
        assert req.email == "user@test.com"

    def test_empty_password(self):
        with pytest.raises(ValidationError):
            AuthLogin(email="user@test.com", password="")


class TestAuthResponse:
    def test_valid(self):
        resp = AuthResponse(user_id="abc", email="u@t.com", token="tok")
        assert resp.user_id == "abc"
        assert resp.email == "u@t.com"
        assert resp.token == "tok"


class TestAuthMe:
    def test_valid(self):
        resp = AuthMe(user_id="abc", email="u@t.com")
        assert resp.user_id == "abc"
        assert resp.email == "u@t.com"