from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.models import ChatMessage, Session
from backend.schemas.chat import ChatRequest, ChatResponse, ChatRequestWithSession
from backend.services.openrouter import OpenRouterConfigError, generate_reply, stream_reply
from backend.services.session_title import generate_chat_title


router = APIRouter()


def _ensure_session(session_id: str | None, db: Session) -> Session:
    """Retorna a sessao existente ou cria uma nova se session_id for None."""
    if session_id:
        sess = db.query(Session).filter(Session.id == session_id).first()
        if sess:
            return sess
    # Cria nova sessao
    sess = Session()
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


async def _auto_generate_title(sess: Session, user_message: str, db: Session) -> None:
    """Gera titulo automatico se a sessao ainda nao tiver um."""
    from backend.models import Session as SessionModel

    # Re-consulta para garantir objeto fresco (evita expired state)
    db_sess = db.query(SessionModel).filter(SessionModel.id == sess.id).first()
    if not db_sess or db_sess.title is not None:
        return

    title = await generate_chat_title(user_message)
    if title:
        db_sess.title = title
        db.commit()
        db.refresh(db_sess)

@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequestWithSession, db: Session = Depends(get_db)) -> ChatResponse:
    sess = _ensure_session(payload.session_id, db)

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

    db.add(ChatMessage(session_key=sess.id, role="user", content=payload.message, model=resolved_model))
    db.add(ChatMessage(session_key=sess.id, role="assistant", content=reply, model=resolved_model))
    db.commit()

    await _auto_generate_title(sess, payload.message, db)

    return ChatResponse(reply=reply, model=resolved_model)


@router.post("/api/chat/stream")
async def chat_stream(payload: ChatRequestWithSession, db: Session = Depends(get_db)) -> StreamingResponse:
    sess = _ensure_session(payload.session_id, db)
    resolved_model = payload.model or OPENROUTER_MODEL_DEFAULT

    async def event_generator():
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
            db.add(
                ChatMessage(
                    session_key=sess.id,
                    role="user",
                    content=payload.message,
                    model=resolved_model,
                )
            )
            db.add(
                ChatMessage(
                    session_key=sess.id,
                    role="assistant",
                    content=full_reply,
                    model=resolved_model,
                )
            )
            db.commit()

            await _auto_generate_title(sess, payload.message, db)

        yield f"data: {json.dumps({'session_id': sess.id, 'done': True}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
