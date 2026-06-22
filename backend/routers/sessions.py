from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Session as SessionModel
from backend.schemas.chat import SessionResponse, SessionTitleUpdate

router = APIRouter()


def _session_to_response(s: SessionModel) -> SessionResponse:
    return SessionResponse(
        id=s.id,
        title=s.title,
        created_at=s.created_at.isoformat(),
        updated_at=s.updated_at.isoformat(),
    )


@router.get("/api/sessions", response_model=list[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    """Lista todas as sessoes ordenadas pela mais recente."""
    sessions = (
        db.query(SessionModel)
        .order_by(SessionModel.updated_at.desc())
        .all()
    )
    return [_session_to_response(s) for s in sessions]


@router.post("/api/sessions", response_model=SessionResponse, status_code=201)
def create_session(db: Session = Depends(get_db)):
    """Cria uma nova sessao vazia."""
    sess = SessionModel()
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return _session_to_response(sess)


@router.get("/api/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Retorna os dados de uma sessao especifica."""
    sess = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    return _session_to_response(sess)


@router.delete("/api/sessions/{session_id}", status_code=204)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Remove uma sessao e todas as suas mensagens."""
    sess = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    db.delete(sess)
    db.commit()


@router.put("/api/sessions/{session_id}/title", response_model=SessionResponse)
def update_session_title(
    session_id: str,
    payload: SessionTitleUpdate,
    db: Session = Depends(get_db),
):
    """Atualiza o titulo de uma sessao."""
    sess = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    sess.title = payload.title
    db.commit()
    db.refresh(sess)
    return _session_to_response(sess)


@router.get("/api/sessions/{session_id}/messages")
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """Retorna todo o historico de mensagens de uma sessao."""
    from backend.models import ChatMessage

    sess = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_key == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "model": m.model,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
