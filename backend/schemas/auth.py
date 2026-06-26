from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator, model_validator


class SignupRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    password_confirm: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
            raise ValueError("Formato de email invalido. Use um email valido como usuario@exemplo.com")
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not re.search(r"[0-9]", value):
            raise ValueError("A senha deve conter pelo menos um numero")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-`~\[\];'\\/]", value):
            raise ValueError("A senha deve conter pelo menos um caractere especial")
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> SignupRequest:
        if self.password != self.password_confirm:
            raise ValueError("As senhas nao conferem")
        return self


class SignupResponse(BaseModel):
    id: int
    email: str
    message: str = "Cadastro realizado com sucesso!"


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value:
            raise ValueError("A senha nao pode estar em branco")
        return value


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    message: str = "Login realizado com sucesso!"


class ErrorResponse(BaseModel):
    detail: str