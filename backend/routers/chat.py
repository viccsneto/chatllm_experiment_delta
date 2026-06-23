from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.models import ChatMessage, ChatSession
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.openrouter import OpenRouterConfigError, generate_reply, generate_title, stream_reply


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _resolve_or_create_session(db: Session, session_id: int | None = None) -> tuple[int, bool]:
    """Returns (session_id, is_new). Creates a new session if none provided."""
    if session_id:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            return session.id, False
    session = ChatSession(title="Nova conversa", title_generated=False)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session.id, True


def _try_generate_title_blocking(db: Session, session_id: int, user_message: str):
    """Fire-and-forget title generation using a synchronous call."""
    import httpx
    from backend.config import OPENROUTER_API_KEY, OPENROUTER_API_URL

    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session or session.title_generated:
        return

    prompt = (
        "Gere um título curto e descritivo (máximo 50 caracteres, sem aspas) "
        "para uma conversa cuja primeira mensagem do usuário é:\n\n"
        f"{user_message}\n\nTítulo:"
    )

    try:
        resp = httpx.post(
            OPENROUTER_API_URL,
            json={
                "model": "google/gemma-4-31b-it",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 30,
                "temperature": 0.3,
            },
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )
        if resp.status_code < 400:
            content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip().strip('"\' \n')
            if content and len(content) <= 60 and content != "Nova conversa":
                session.title = content
                session.title_generated = True
                db.commit()
    except Exception:
        pass


@router.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
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

    session_id, _ = _resolve_or_create_session(db, payload.session_id)

    db.add(ChatMessage(session_id=session_id, role="user", content=payload.message, model=resolved_model))
    db.add(ChatMessage(session_id=session_id, role="assistant", content=reply, model=resolved_model))
    db.commit()

    _try_generate_title_blocking(db, session_id, payload.message)

    return ChatResponse(reply=reply, model=resolved_model)


@router.post("/api/chat/stream")
async def chat_stream(payload: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    resolved_model = payload.model or OPENROUTER_MODEL_DEFAULT
    session_id, _ = _resolve_or_create_session(db, payload.session_id)

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
                    session_id=session_id,
                    role="user",
                    content=payload.message,
                    model=resolved_model,
                )
            )
            db.add(
                ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=full_reply,
                    model=resolved_model,
                )
            )
            db.commit()

        _try_generate_title_blocking(db, session_id, payload.message)

        yield f"data: {json.dumps({'done': True}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
