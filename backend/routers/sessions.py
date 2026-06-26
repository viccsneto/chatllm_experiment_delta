from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from backend.database import get_db
from backend.models import Session, ChatMessage
from backend.schemas.chat import (
    SessionCreate,
    SessionOut,
    SessionUpdate,
    ChatMessageOut,
)
from backend.services.openrouter import generate_title_for_session

router = APIRouter()


@router.get("/api/sessions", response_model=list[SessionOut])
def list_sessions(db: DBSession = Depends(get_db)):
    sessions = (
        db.query(Session)
        .order_by(Session.created_at.desc())
        .all()
    )
    return sessions


@router.post("/api/sessions", response_model=SessionOut, status_code=201)
def create_session(payload: SessionCreate, db: DBSession = Depends(get_db)):
    session = Session(title=payload.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/api/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return session


@router.patch("/api/sessions/{session_id}", response_model=SessionOut)
def update_session(session_id: int, payload: SessionUpdate, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    session.title = payload.title
    db.commit()
    db.refresh(session)
    return session


@router.delete("/api/sessions/{session_id}", status_code=204)
def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    db.delete(session)
    db.commit()


@router.get("/api/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def list_session_messages(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return messages


@router.post("/api/sessions/{session_id}/auto-title", response_model=SessionOut)
async def auto_title_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    first_user_msg = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id, ChatMessage.role == "user")
        .order_by(ChatMessage.created_at.asc())
        .first()
    )

    if not first_user_msg:
        raise HTTPException(status_code=400, detail="Nenhuma mensagem do usuário encontrada para gerar título")

    try:
        title = await generate_title_for_session(first_user_msg.content)
    except Exception:
        title = None

    if title:
        session.title = title
        db.commit()
        db.refresh(session)

    return session