from __future__ import annotations

import httpx

from backend.config import OPENROUTER_API_KEY, OPENROUTER_API_URL, OPENROUTER_MODEL_DEFAULT
from backend.services.openrouter import _build_headers

_TITLE_PROMPT = (
    "Generate a very short title (maximum 6 words) for a conversation "
    "that starts with the following user message. "
    "Respond with ONLY the title, no quotes, no punctuation, no explanation.\n\n"
    "User message: {message}"
)


async def generate_chat_title(user_message: str) -> str | None:
    """Gera um titulo curto para a sessao com base na primeira mensagem do usuario.

    Retorna None se a geracao falhar (ex: sem API key).
    """
    if not OPENROUTER_API_KEY:
        return None

    payload = {
        "model": OPENROUTER_MODEL_DEFAULT,
        "messages": [
            {
                "role": "user",
                "content": _TITLE_PROMPT.format(message=user_message[:500]),
            }
        ],
        "max_tokens": 30,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                OPENROUTER_API_URL, json=payload, headers=_build_headers()
            )

        if response.status_code >= 400:
            return None

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        title = content.strip().strip('"').strip("'")
        return title if title else None
    except Exception:
        return None
