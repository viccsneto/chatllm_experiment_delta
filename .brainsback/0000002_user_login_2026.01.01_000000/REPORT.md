# Implementation Report

> A concise summary for the reviewer.

**Reviewer note**: If a PR modifies `.brainsback/<task-folder>/TODO.md` or `.brainsback/<task-folder>/REACTO.md`, assume this is expected and that those files were modified by the human developer.
If present, use `.github/skills/brainsback-reviewer/SKILL.md` as the review rubric.

## Snapshot
- **Change**: Implementação de autenticação por email e senha com JWT.
- **Status**: Concluído.

## The Changes
- [x] `backend/models.py` — Modelo `User` (email único, password_hash, created_at) + `Session.user_id` FK
- [x] `backend/schemas/auth.py` — Schemas `SignupRequest` (valida email, senha forte, confirmação), `LoginRequest`, `LoginResponse`, `SignupResponse`
- [x] `backend/routers/auth.py` — Endpoints: signup (201), login (200+token), me (protegido), check (público), logout
- [x] `backend/services/auth.py` — hash/verify com bcrypt, criação e validação de JWT, dependências `get_current_user` e `require_user`
- [x] `backend/config.py` — `SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRATION_HOURS`
- [x] `.env` — Geração de `SECRET_KEY` com `secrets.token_urlsafe(48)`
- [x] `backend/requirements.txt` — `python-jose`, `passlib`, `bcrypt<4.1`
- [x] `backend/routers/sessions.py` — Todas as rotas de sessão filtradas por `user_id` (autenticadas via `get_current_user`)
- [x] `frontend/src/api.js` — Funções `authSignup`, `authLogin`, `authCheck`, `authLogout`, `getToken`, `setToken` + `extractDetail` para erros user-friendly
- [x] `frontend/src/AuthPage.jsx` — Tela de login/cadastro com validação inline, alternância entre modos
- [x] `frontend/src/App.jsx` — `authCheck` na montagem, renderização condicional (AuthPage vs Chat), botão "Sair" com email do usuário
- [x] `frontend/index.html` — Estilos CSS da página de auth, script da AuthPage
- [x] `tests/test_auth.py` — Testes unitários (hash, JWT, schemas) e de integração (11 cenários via TestClient)

## Testing Strategy
- **Testes unitários**: hash bcrypt (correta/errada), JWT (válido/expirado/inválido/chave errada), schemas (email inválido, senha sem número, sem especial, não conferem, em branco)
- **Testes de integração**: signup (201), email duplicado (409), login (200), senha errada (401), usuário inexistente (401), check com/sem/inválido/expirado (200), rota protegida sem token/inválido (401)
- **Script de teste via API**: 7 cenários de erro validando mensagens em português
- **Teste manual no navegador**: fluxo completo cadastro → login → reload → logout

## Risks & Follow-up
- [ ] Logout não invalida token no servidor (stateless) — token dura até expirar
- [ ] Sem rate limiting no login — vulnerável a força bruta
- [ ] Token 24h fixo sem refresh token
- [ ] Sem auditoria de tentativas de login
