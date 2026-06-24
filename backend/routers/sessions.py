from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ChatSession as SessionModel
from backend.schemas.session import SessionCreate, SessionList, SessionOut, TitleSuggestion
from backend.services.openrouter import generate_reply, OpenRouterConfigError


router = APIRouter()


@router.get("/api/sessions", response_model=SessionList)
def list_sessions(db: Session = Depends(get_db)) -> SessionList:
    sessions = (
        db.query(SessionModel)
        .order_by(SessionModel.updated_at.desc())
        .all()
    )
    return SessionList(sessions=[SessionOut.model_validate(s) for s in sessions])


@router.post("/api/sessions", response_model=SessionOut, status_code=201)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> SessionOut:
    session = SessionModel()
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionOut.model_validate(session)


@router.delete("/api/sessions/{session_id}", status_code=200)
def delete_session(session_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")
    db.delete(session)
    db.commit()
    return {"status": "deleted"}


@router.get("/api/sessions/{session_id}/history")
def get_session_history(session_id: int, db: Session = Depends(get_db)) -> list[dict]:
    from backend.models import ChatMessage

    session = db.query(SessionModel).filter(
        SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {"role": m.role, "content": m.content, "model": m.model,
            "created_at": m.created_at.isoformat()}
        for m in messages
    ]


@router.post("/api/sessions/{session_id}/suggest-title", response_model=TitleSuggestion)
async def suggest_title(session_id: int, db: Session = Depends(get_db)) -> TitleSuggestion:
    """Gera um titulo automatico para a sessao com base nas primeiras mensagens."""
    from backend.models import ChatMessage

    session = db.query(SessionModel).filter(
        SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(4)
        .all()
    )

    if not messages:
        raise HTTPException(
            status_code=400, detail="Sessao vazia, nao e possivel sugerir titulo")

    context_text = "\n".join(
        f"{m.role}: {m.content[:200]}" for m in messages
    )

    prompt = (
        "Based on the following conversation, suggest a short title (max 6 words, in the same language as the conversation). "
        "Return ONLY the title, no quotes, no extra text.\n\n"
        f"{context_text}"
    )

    try:
        reply, _ = await generate_reply(
            user_message=prompt,
            history=[],
            model=None,
        )
    except (OpenRouterConfigError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    title = reply.strip().strip('"').strip("'").strip()
    if len(title) > 200:
        title = title[:200]

    session.title = title
    db.commit()

    return TitleSuggestion(title=title)
