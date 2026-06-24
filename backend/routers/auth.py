from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

import bcrypt

from backend.database import get_db
from backend.models import SessionToken, User
from backend.schemas.auth import AuthResponse, LoginRequest, MeResponse, SignupRequest


router = APIRouter()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def get_current_user(
    authorization: str = Header(""),
    db: Session = Depends(get_db),
) -> User:
    """Dependency that extracts and validates the session token from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token nao fornecido")

    token_str = authorization[7:].strip()
    if not token_str:
        raise HTTPException(status_code=401, detail="Token nao fornecido")

    token_record = (
        db.query(SessionToken)
        .filter(SessionToken.token == token_str)
        .first()
    )
    if not token_record:
        raise HTTPException(
            status_code=401, detail="Token invalido ou expirado")

    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado")

    return user


@router.post("/api/auth/signup", response_model=AuthResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Cadastra um novo usuario e retorna um token de sessao."""
    email = payload.email.strip().lower()
    if not email:
        raise HTTPException(status_code=422, detail="Email invalido")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email ja cadastrado")

    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()

    token = SessionToken(
        token=str(uuid.uuid4()),
        user_id=user.id,
    )
    db.add(token)
    db.commit()
    db.refresh(token)

    return AuthResponse(token=token.token, email=user.email)


@router.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Realiza login e retorna um token de sessao."""
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou senha invalidos")

    token = SessionToken(
        token=str(uuid.uuid4()),
        user_id=user.id,
    )
    db.add(token)
    db.commit()
    db.refresh(token)

    return AuthResponse(token=token.token, email=user.email)


@router.post("/api/auth/logout", status_code=200)
def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Invalida todos os tokens do usuario atual."""
    db.query(SessionToken).filter(
        SessionToken.user_id == current_user.id
    ).delete()
    db.commit()
    return {"status": "logged_out"}


@router.get("/api/auth/me", response_model=MeResponse)
def me(
    current_user: User = Depends(get_current_user),
) -> MeResponse:
    """Retorna os dados do usuario autenticado."""
    return MeResponse(email=current_user.email)
