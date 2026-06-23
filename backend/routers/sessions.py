from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from backend.database import get_db
from backend.models import ChatMessage, Session
from backend.schemas.session import SessionCreate, SessionOut


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionOut])
def list_sessions(db: DBSession = Depends(get_db)):
    """Lista todas as sessoes ordenadas pela mais recente."""
    return (
        db.query(Session)
        .order_by(Session.updated_at.desc())
        .all()
    )


@router.post("", response_model=SessionOut, status_code=201)
def create_session(payload: SessionCreate, db: DBSession = Depends(get_db)):
    """Cria uma nova sessao."""
    session = Session(title=payload.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    return session


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    db.delete(session)
    db.commit()


@router.patch("/{session_id}/title", response_model=SessionOut)
def update_session_title(session_id: int, title: str, db: DBSession = Depends(get_db)):
    """Atualiza o titulo de uma sessao."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    session.title = title
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}/messages", response_model=list[dict])
def get_session_messages(session_id: int, db: DBSession = Depends(get_db)):
    """Retorna as mensagens de uma sessao."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]