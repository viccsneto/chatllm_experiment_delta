# Proof of Mastery (REACTO)

> Explain it to prove you own it.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## R — Repeat (The Problem)
Implementar autenticação com email e senha, persistida em SQLite.

## E — Examples

- **Happy Path Input**: Usuário faz login com email e senha corretos
  **Output**: Entra no chat autenticado, token salvo no localStorage

- **Edge Case Input**: Usuário tenta cadastrar com email já existente
  **Output**: Erro "Este email já está cadastrado"

- **Edge Case Input**: Usuário faz logout e recarrega a página
  **Output**: Volta à tela de login, chats da conta persistem para próximo login

## A — Approach
JWT guardado no localStorage. Cada request envia Bearer token. Backend decodifica e valida. Logout remove o token do localStorage.

## C — Code
- verify_password — mais crítica, porta de entrada da autenticação
- create_access_token — gera identidade digital, erros aqui comprometem tudo
- get_current_user/require_user — gatekeeper executado em toda request
- hash_password — importante mas delegado ao bcrypt battle-tested

## T — Tests
4 camadas — testes unitários (schemas, hash, JWT), integração (11 cenários via TestClient), script Python via API, teste manual no navegador com reload.

## O — Optimize
Logout não invalida token no servidor, sem rate limiting, token 24h fixo sem refresh, SECRET_KEY no .env, sem auditoria de login, sem HTTPS.
