from __future__ import annotations

import hashlib
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User

_security = HTTPBearer(auto_error=False)


def _hash_password(password: str) -> str:
    """Gera hash SHA-256 do password com salt."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${h}"


def _verify_password(password: str, stored: str) -> bool:
    """Verifica password contra hash armazenado (salt$hash)."""
    salt, h = stored.split("$", 1)
    return hashlib.sha256((salt + password).encode()).hexdigest() == h


def _generate_token() -> str:
    return secrets.token_hex(16)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
    db: Session = Depends(get_db),
) -> User | None:
    """Retorna o usuario autenticado ou None se nao houver token."""
    if not credentials:
        return None
    token = credentials.credentials
    return db.query(User).filter(User.auth_token == token).first()


def require_user(user: User | None = Depends(get_current_user)) -> User:
    """Retorna o usuario ou levanta 401 se nao autenticado."""
    if not user:
        raise HTTPException(status_code=401, detail="Nao autenticado")
    return user