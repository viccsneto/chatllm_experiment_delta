from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.models import ChatMessage, Session
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.openrouter import OpenRouterConfigError, generate_reply, stream_reply


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _ensure_session(db: Session, session_id: int | None) -> Session:
    """Retorna a sessao existente ou cria uma nova."""
    if session_id is not None:
        session = db.query(Session).filter(Session.id == session_id).first()
        if session:
            return session
    session = Session(title="Nova conversa")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _auto_title_from_message(message: str) -> str:
    """Gera um titulo automatico a partir da primeira mensagem do usuario."""
    cleaned = message.strip()
    if len(cleaned) <= 50:
        return cleaned
    return cleaned[:47] + "..."


@router.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    session = _ensure_session(db, payload.session_id)

    try:
        reply, model_name = await generate_reply(
            user_message=payload.message,
            history=[item.model_dump() for item in payload.history],
            model=payload.model,
        )
    except OpenRouterConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    resolved_model = payload.model or model_name or OPENROUTER_MODEL_DEFAULT

    # Auto-titulo na primeira mensagem da sessao
    if session.title == "Nova conversa":
        session.title = _auto_title_from_message(payload.message)

    db.add(ChatMessage(session_id=session.id, role="user", content=payload.message, model=resolved_model))
    db.add(ChatMessage(session_id=session.id, role="assistant", content=reply, model=resolved_model))
    db.commit()

    return ChatResponse(reply=reply, model=resolved_model)


@router.post("/api/chat/stream")
async def chat_stream(payload: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    session = _ensure_session(db, payload.session_id)
    resolved_model = payload.model or OPENROUTER_MODEL_DEFAULT
    is_first_message = session.title == "Nova conversa"

    async def event_generator():
        nonlocal session
        full_reply = ""
        try:
            async for delta in stream_reply(
                user_message=payload.message,
                history=[item.model_dump() for item in payload.history],
                model=payload.model,
            ):
                full_reply += delta
                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=True)}\n\n"
        except OpenRouterConfigError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            return
        except RuntimeError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            return

        if full_reply.strip():
            # Auto-titulo na primeira mensagem da sessao
            if is_first_message:
                session.title = _auto_title_from_message(payload.message)
                db.add(session)

            db.add(
                ChatMessage(
                    session_id=session.id,
                    role="user",
                    content=payload.message,
                    model=resolved_model,
                )
            )
            db.add(
                ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=full_reply,
                    model=resolved_model,
                )
            )
            db.commit()

        yield f"data: {json.dumps({'done': True, 'session_id': session.id, 'title': session.title}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
