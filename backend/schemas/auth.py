from __future__ import annotations

from pydantic import BaseModel, Field


class AuthSignup(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class AuthLogin(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    user_id: str
    email: str
    token: str


class AuthMe(BaseModel):
    user_id: str
    email: str