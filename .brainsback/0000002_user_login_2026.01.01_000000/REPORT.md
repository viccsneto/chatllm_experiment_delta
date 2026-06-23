# Implementation Report — Task 2: Login e Logout

## Visão Geral
Implementação de autenticação por email e senha com persistência em SQLite, utilizando JWT (stateless) e bcrypt para hash de senhas.

## Arquivos Criados/Modificados

### Backend
- `backend/models.py` — Adicionada tabela `User` (id, email, password_hash, created_at)
- `backend/config.py` — Adicionada constante `JWT_SECRET`
- `backend/schemas/auth.py` — Schemas: SignupRequest, LoginRequest, AuthResponse, MeResponse
- `backend/routers/auth.py` — Endpoints: POST /api/auth/signup, POST /api/auth/login, POST /api/auth/logout, GET /api/auth/me + dependência get_current_user
- `backend/main.py` — Registrado auth_router
- `backend/requirements.txt` — Adicionados bcrypt e pyjwt

### Frontend
- `frontend/src/Login.jsx` — Componente de login/cadastro com toggle entre modos
- `frontend/src/App.jsx` — Adicionados AppAuthenticated (conteúdo logado), App (wrapper com controle de token), fluxo de login/logout
- `frontend/src/api.js` — Função authHeaders() para enviar token JWT em todas as requisições
- `frontend/index.html` — Estilos da página de login e rodapé do usuário

### Testes
- `tests/test_auth.py` — 10 testes: signup, login, logout, me (com/sem token, token inválido)

## Lógica Central
- Senhas armazenadas com hash bcrypt (salt automático)
- JWT tokens HS256 com expiração de 24h
- Autenticação via decorator get_current_user com HTTPBearer
- Frontend: token persistido em localStorage, removido no logout
- Segurança: senha mínima de 6 caracteres, email único

## Dependências
- bcrypt>=4.0 — hash de senhas
- pyjwt>=2.0 — geração/validação de tokens JWT

## Testes
- 53 testes passando (43 anteriores + 10 novos de auth)
- Cobertura: cadastro, login sucesso, senha errada, email inexistente, duplicata, logout, /me autenticado/não autenticado/token inválido

## Limitações Conhecidas
- JWT secret fixo em dev (configurável via env JWT_SECRET)
- Logout stateless (apenas remoção do token no frontend) 

---
**Note**: Usually filled by the AI.
