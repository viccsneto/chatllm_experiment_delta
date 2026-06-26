from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from backend.database import get_db
from backend.models import User
from backend.schemas.auth import (
    ErrorResponse,
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

router = APIRouter(tags=["auth"])


@router.post(
    "/api/auth/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def signup(payload: SignupRequest, db: DBSession = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este email ja esta cadastrado. Tente fazer login ou use outro email.",
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return SignupResponse(id=user.id, email=user.email)


@router.post(
    "/api/auth/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}},
)
def login(payload: LoginRequest, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos. Verifique suas credenciais e tente novamente.",
        )

    token = create_access_token(user.id, user.email)
    return LoginResponse(access_token=token, email=user.email)


@router.post(
    "/api/auth/me",
    response_model=SignupResponse,
    responses={401: {"model": ErrorResponse}},
)
def me(current_user: User = Depends(require_user)):
    return SignupResponse(id=current_user.id, email=current_user.email)


@router.post(
    "/api/auth/logout",
    responses={200: {"description": "Logout realizado com sucesso"}},
)
def logout(current_user: User = Depends(require_user)):
    return {"message": "Logout realizado com sucesso. Seu token foi invalidado."}


@router.get(
    "/api/auth/check",
    response_model=SignupResponse | None,
)
def check_auth(current_user: User | None = Depends(get_current_user)):
    if current_user is None:
        return None
    return SignupResponse(id=current_user.id, email=current_user.email)