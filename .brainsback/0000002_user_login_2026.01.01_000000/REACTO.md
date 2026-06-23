## R — Repeat (O Problema)
Implementar autenticação completa com cadastro e login por email/senha, logout funcional, sessão persistida e senhas criptografadas no SQLite.

## E — Examples

- **Happy Path — Cadastro**
  Input: `POST /auth/register { email: "user@email.com", password: "123456" }`
  Output: `201 Created { token: "uuid-gerado", email: "user@email.com" }` — `password_hash` salvo no banco via `User`, token na tabela `SessionToken`

- **Happy Path — Login**
  Input: `POST /auth/login { email: "user@email.com", password: "123456" }`
  Output: `200 OK { token: "uuid-gerado", email: "user@email.com" }` — `loginUser()` em `api.js` salva token no localStorage

- **Edge Case — Credenciais erradas**
  Input: `POST /auth/login { email: "user@email.com", password: "errada" }`
  Output: `401 { detail: "E-mail ou senha incorretos" }` — mesmo erro se o email não existir, sem distinguir o motivo

- **Edge Case — Email duplicado**
  Input: `POST /auth/register { email: "user@email.com", password: "outrasenha" }`
  Output: `409 Conflict { detail: "E-mail já cadastrado" }`

- **Edge Case — Logout e acesso protegido**
  Input: `POST /auth/logout` com token válido, seguido de `GET /auth/me` sem token
  Output: `401 Unauthorized` — token deletado da tabela `SessionToken`, `App.jsx` redireciona para `Login.jsx`

## A — Approach
Fluxo em três camadas: endpoint (`routers/auth.py`) → modelo (`models.py`) → banco SQLite.

O hash da senha é gerado com `bcrypt` dentro do endpoint de register antes de criar o `User`. O token de sessão é um UUID salvo na tabela `SessionToken` — stateful e simples, sem JWT. O frontend armazena o token no localStorage via `api.js` e o envia no header `Authorization: Bearer <token>` em todas as requisições. O `App.jsx` controla o estado de autenticação: se não há token válido, renderiza `Login.jsx`; após logout via `logoutUser()`, limpa localStorage e volta para a tela de login. A mensagem de erro no login é sempre a mesma independente do motivo da falha.

## C — Code

`backend/models.py`
- `User`: campos `id`, `email` (unique), `password_hash`, `created_at`
- `SessionToken`: campos `id`, `token` (unique), `user_id` (FK para `User`), `created_at`

`backend/schemas/auth.py`
- `RegisterRequest`: valida `email` e `password` (mínimo 6 chars)
- `LoginRequest`: `email` + `password`
- `AuthResponse`: retorna `token` + `email` — nunca expõe `password_hash`

`backend/routers/auth.py`
- `POST /auth/register`: valida unicidade do email → gera hash com `bcrypt.hashpw()` → cria `User` → cria `SessionToken` → retorna `AuthResponse`
- `POST /auth/login`: busca `User` por email → `bcrypt.checkpw()` → se falhar por qualquer motivo retorna 401 com mensagem genérica → cria novo `SessionToken` → retorna `AuthResponse`
- `POST /auth/logout`: busca `SessionToken` pelo header → deleta do banco → retorna 204
- `GET /auth/me`: valida token → retorna email do usuário autenticado

`backend/main.py`
- Registra `auth_router` com prefixo `/auth`

`backend/requirements.txt`
- Adicionado `bcrypt`

`frontend/api.js`
- `registerUser(email, password)`: POST `/auth/register` → salva token no localStorage
- `loginUser(email, password)`: POST `/auth/login` → salva token no localStorage
- `logoutUser()`: POST `/auth/logout` com `getAuthHeaders()` → remove token do localStorage
- `getAuthHeaders()`: retorna `{ Authorization: "Bearer <token>" }` lendo do localStorage

`frontend/Login.jsx`
- Toggle entre modo login e cadastro
- Submit chama `loginUser()` ou `registerUser()` conforme modo
- Em erro 401/409: exibe mensagem humanizada abaixo do formulário

`frontend/App.jsx`
- No mount: chama `GET /auth/me` com `getAuthHeaders()` para validar sessão persistida
- Se inválido ou sem token: renderiza `Login.jsx`
- Sidebar expõe botão de logout que chama `logoutUser()` e reseta estado

`frontend/index.html`
- CSS da tela de login (centralizado, campos simples)
- Footer da sidebar com botão de logout
- Carrega `Login.jsx` como entry point de autenticação

## T — Tests

`backend/routers/auth.py` — testes manuais via curl ou Swagger (`/docs`):
- Cadastrar com email novo → conferir via SQLite que `password_hash` ≠ senha original
- Cadastrar com mesmo email → esperar 409
- Login com credenciais corretas → token retornado e salvo
- Login com senha errada → 401 com mensagem genérica
- Login com email inexistente → mesmo 401, mesma mensagem
- `GET /auth/me` sem token → 401
- Logout → 204; chamar `GET /auth/me` com o mesmo token → 401

`frontend/Login.jsx` — testes manuais no browser:
- Submeter login errado → mensagem "E-mail ou senha incorretos" aparece
- Submeter cadastro com email duplicado → mensagem de erro aparece
- Após logout, pressionar voltar no browser → permanece na tela de login

## O — Optimize
Complexidade não é o foco — volume de usuários é baixo e SQLite é suficiente.

Trade-offs conscientes: token stateful (UUID na tabela `SessionToken`) em vez de JWT simplifica o logout mas adiciona uma query por requisição autenticada via `GET /auth/me`. Sem rate limiting no login por ora — oportunidade futura se houver risco de brute force. Sem refresh token — sessão persiste até logout explícito ou deleção manual da tabela.