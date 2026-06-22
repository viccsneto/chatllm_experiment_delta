from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    model: str | None = None
    history: list[ChatMessageIn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    model: str


class SessionCreate(BaseModel):
    pass


class SessionResponse(BaseModel):
    id: str
    title: str | None = None
    created_at: str
    updated_at: str


class SessionTitleUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class ChatRequestWithSession(ChatRequest):
    session_id: str | None = None
