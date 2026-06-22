from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas.auth import AuthLogin, AuthResponse, AuthSignup, AuthMe
from backend.services.auth import (
    _hash_password,
    _verify_password,
    _generate_token,
    get_current_user,
    require_user,
)

router = APIRouter()


@router.post("/api/auth/signup", response_model=AuthResponse, status_code=201)
def signup(payload: AuthSignup, db: Session = Depends(get_db)):
    """Cadastra um novo usuario."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email ja cadastrado")

    user = User(
        email=payload.email,
        password_hash=_hash_password(payload.password),
        auth_token=_generate_token(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return AuthResponse(user_id=user.id, email=user.email, token=user.auth_token)


@router.post("/api/auth/login", response_model=AuthResponse)
def login(payload: AuthLogin, db: Session = Depends(get_db)):
    """Autentica um usuario existente."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha invalidos")

    if not _verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou senha invalidos")

    # Gera novo token a cada login
    user.auth_token = _generate_token()
    db.commit()
    db.refresh(user)

    return AuthResponse(user_id=user.id, email=user.email, token=user.auth_token)


@router.post("/api/auth/logout", status_code=204)
def logout(current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Invalida o token do usuario."""
    current_user.auth_token = None
    db.commit()


@router.get("/api/auth/me", response_model=AuthMe)
def me(current_user: User | None = Depends(get_current_user)):
    """Retorna dados do usuario autenticado, ou 401."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Nao autenticado")
    return AuthMe(user_id=current_user.id, email=current_user.email)