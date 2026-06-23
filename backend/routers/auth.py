from __future__ import annotations

import secrets

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import SessionToken, User
from backend.schemas.auth import AuthResponse, LoginRequest, RegisterRequest


router = APIRouter(prefix="/api/auth", tags=["auth"])


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _get_current_user(token: str = Header(alias="authorization"), db: Session = Depends(get_db)) -> User:
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token invalido")
    token_value = token[7:]
    session_token = db.query(SessionToken).filter(SessionToken.token == token_value).first()
    if not session_token:
        raise HTTPException(status_code=401, detail="Token invalido")
    user = db.query(User).filter(User.id == session_token.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Token invalido")
    return user


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if len(payload.email) < 5 or "@" not in payload.email:
        raise HTTPException(status_code=422, detail="Email invalido")
    if len(payload.password) < 6:
        raise HTTPException(status_code=422, detail="Senha deve ter no minimo 6 caracteres")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email ja cadastrado")

    user = User(
        email=payload.email,
        password_hash=_hash_password(payload.password),
    )
    db.add(user)
    db.flush()

    token = secrets.token_hex(32)
    db.add(SessionToken(user_id=user.id, token=token))
    db.commit()

    return AuthResponse(token=token, email=user.email, user_id=user.id)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

    token = secrets.token_hex(32)
    db.add(SessionToken(user_id=user.id, token=token))
    db.commit()

    return AuthResponse(token=token, email=user.email, user_id=user.id)


@router.post("/logout", status_code=204)
def logout(db: Session = Depends(get_db), current_user: User = Depends(_get_current_user)):
    db.query(SessionToken).filter(SessionToken.user_id == current_user.id).delete()
    db.commit()


@router.get("/me", response_model=AuthResponse)
def me(current_user: User = Depends(_get_current_user)):
    return AuthResponse(token="", email=current_user.email, user_id=current_user.id)