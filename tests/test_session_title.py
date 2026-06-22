from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.session_title import generate_chat_title


class TestGenerateChatTitle:
    @pytest.mark.asyncio
    async def test_returns_none_without_api_key(self):
        """Sem API key, deve retornar None."""
        with patch("backend.services.session_title.OPENROUTER_API_KEY", ""):
            result = await generate_chat_title("Ola, mundo!")
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_title_on_success(self):
        """Deve retornar o titulo gerado pelo modelo."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": '"Saudacoes Iniciais"'}}
            ]
        }

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("backend.services.session_title.OPENROUTER_API_KEY", "sk-test"):
            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await generate_chat_title("Ola, mundo!")
                assert result == "Saudacoes Iniciais"

    @pytest.mark.asyncio
    async def test_returns_none_on_http_error(self):
        """Erro HTTP deve retornar None sem exception."""
        mock_response = MagicMock()
        mock_response.status_code = 429  # Rate limited

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("backend.services.session_title.OPENROUTER_API_KEY", "sk-test"):
            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await generate_chat_title("Ola, mundo!")
                assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self):
        """Excecao generica deve retornar None sem propagar."""
        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=RuntimeError("Timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("backend.services.session_title.OPENROUTER_API_KEY", "sk-test"):
            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await generate_chat_title("Ola, mundo!")
                assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_empty_content(self):
        """Resposta vazia do modelo deve retornar None."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": ""}}
            ]
        }

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("backend.services.session_title.OPENROUTER_API_KEY", "sk-test"):
            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await generate_chat_title("Ola, mundo!")
                assert result is None
