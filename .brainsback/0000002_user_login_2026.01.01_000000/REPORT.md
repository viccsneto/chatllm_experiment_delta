# Implementation Report — Tarefa 2 (Login/Logout)

> A concise summary for the reviewer.

**Reviewer note**: If a PR modifies `.brainsback/<task-folder>/TODO.md` or `.brainsback/<task-folder>/REACTO.md`, assume this is expected and that those files were modified by the human developer.
If present, use `.github/skills/brainsback-reviewer/SKILL.md` as the review rubric.

## Snapshot

- **Change**: Implementação de autenticação por email/senha com persistência SQLite.
- **Status**: Concluído.
- **Testes**: 51 passando (9 novos testes de auth + 42 existentes).

## The Changes

### Backend

- [x] `backend/models.py` — Novos modelos `User` (id, email, hashed_password, created_at) e `SessionToken` (id, token uuid, user_id, created_at). `Session` renomeado para `ChatSession` para evitar conflito com SQLAlchemy.
- [x] `backend/schemas/auth.py` — Schemas `SignupRequest`, `LoginRequest`, `AuthResponse`, `MeResponse`.
- [x] `backend/routers/auth.py` — Endpoints:
  - `POST /api/auth/signup` — cadastro com bcrypt, retorna token uuid
  - `POST /api/auth/login` — login valida email+senha, retorna token uuid
  - `POST /api/auth/logout` — invalida todos os tokens do usuário
  - `GET /api/auth/me` — rota protegida que retorna email do usuário autenticado
  - `get_current_user()` — dependência que extrai token do header `Authorization: Bearer <token>`
- [x] `backend/main.py` — Router de auth registrado.

### Frontend

- [x] `frontend/src/Login.jsx` — Componente de login/cadastro com toggle entre modos.
- [x] `frontend/src/api.js` — Funções `getToken`, `saveAuth`, `clearAuth`, `authHeaders`, `fetchMe`, `apiLogout`.
- [x] `frontend/src/App.jsx` — `checkingAuth` inicial, `handleLogin`/`handleLogout`, header com email e botão de sair.
- [x] `frontend/index.html` — CSS do formulário de login e header; script `Login.jsx` incluído.

### Testes

- [x] `tests/test_auth.py` — 9 testes: signup, email duplicado (409), login sucesso, senha errada (401), email inexistente (401), me autenticado, me não autenticado (401), logout invalida token, case insensitive email.

## Testing Strategy

- `pytest` com SQLite em memória: 51 testes, 0 falhas.
- Senhas com bcrypt (hash + salt).
- Sessão via uuid4 armazenado em `SessionToken`, sem expiração.

## The Changes

- [ ]

## Testing Strategy

_How we ensured it works._

## Risks & Follow-up

- [ ]

---

**Note**: Usually filled by the AI.
