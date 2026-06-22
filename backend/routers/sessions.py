from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Session as SessionModel, ChatMessage
from backend.schemas.chat import SessionResponse, SessionTitleUpdate
from backend.services.auth import get_current_user, require_user

router = APIRouter()


def _session_to_response(s: SessionModel) -> SessionResponse:
    return SessionResponse(
        id=s.id,
        title=s.title,
        created_at=s.created_at.isoformat(),
        updated_at=s.updated_at.isoformat(),
    )


@router.get("/api/sessions", response_model=list[SessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista todas as sessoes (do usuario se autenticado, ou todas as orfas)."""
    query = db.query(SessionModel)

    if current_user:
        query = query.filter(SessionModel.user_id == current_user.id)
    else:
        query = query.filter(SessionModel.user_id.is_(None))

    sessions = query.order_by(SessionModel.updated_at.desc()).all()
    return [_session_to_response(s) for s in sessions]


@router.post("/api/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cria uma nova sessao vazia, vinculada ao usuario se autenticado."""
    sess = SessionModel(user_id=current_user.id if current_user else None)
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return _session_to_response(sess)


@router.get("/api/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    sess = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    return _session_to_response(sess)


@router.delete("/api/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    sess = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    # Se o usuario esta autenticado, so pode deletar proprias sessoes
    if current_user and sess.user_id and sess.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Nao autorizado")
    db.delete(sess)
    db.commit()


@router.put("/api/sessions/{session_id}/title", response_model=SessionResponse)
def update_session_title(
    session_id: str,
    payload: SessionTitleUpdate,
    db: Session = Depends(get_db),
):
    sess = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    sess.title = payload.title
    db.commit()
    db.refresh(sess)
    return _session_to_response(sess)


@router.get("/api/sessions/{session_id}/messages")
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
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


@router.post("/api/sessions/delete-unowned", status_code=204)
def delete_unowned_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(require_user),
):
    """Remove sessoes sem user_id (sessoes criadas antes do login)."""
    unowned = db.query(SessionModel).filter(SessionModel.user_id.is_(None)).all()
    for s in unowned:
        db.delete(s)
    db.commit()
