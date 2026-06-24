# Proof of Mastery (REACTO)

> Explain it to prove you own it.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## R — Repeat (The Problem)

O objetivo era adicionar uma camada de autenticação (cadastro, login e logout) por e-mail e senha ao sistema, garantindo que os dados fossem persistidos em um banco SQLite. Além disso, foi necessário isolar as rotas privadas para que apenas usuários autenticados pudessem acessar suas informações e garantir que os dados antigos do sistema continuassem sem conflitos com as novas tabelas de usuários e tokens.

## E — Examples

- **Happy Path Input**: Chamada para POST /api/auth/signup com um e-mail novo e senha. Em seguida, login com as mesmas credenciais em POST /api/auth/login.
  **Output**: O cadastro retorna 201 ou 200 com um UUID válido. O login valida os dados e retorna o mesmo formato de token. A rota /api/auth/me com o header Authorization: Bearer <token> responde com sucesso trazendo os dados do usuário.

- **Edge Case Input**: Tentativa de cadastro com um e-mail que já existe no banco ou tentativa de login com a senha errada.
  **Output**: O cadastro duplicado retorna erro 409 Conflict. O login com senha incorreta ou e-mail inexistente retorna 401 Unauthorized.

## A — Approach

A estratégia consistiu em criar uma estrutura simples de autenticação baseada em tokens UUID persistidos no banco. No backend, separei o modelo de usuário do modelo de token de sessão para permitir que um usuário mude de estado ou deslogue invalidando o registro no banco. Para evitar colisões com o SQLAlchemy, o modelo antigo Session foi renomeado para ChatSession. No frontend, o App.jsx gerencia se o usuário vê a tela de login ou a aplicação principal, persistindo o token localmente

## C — Code

backend/models.py: Criação das tabelas User e SessionToken. Renomeação da antiga entidade para ChatSession para não quebrar as querys do SQLAlchemy com o novo conceito de sessão de usuário.

backend/routers/auth.py: Centralização da lógica de criptografia de senhas usando bcrypt e a criação da dependência get_current_user() que usa o header Bearer para proteger as rotas.

frontend/src/Login.jsx e App.jsx: Implementação do formulário que alterna dinamicamente entre login e cadastro, e o estado de inicialização (checkingAuth) no componente principal para evitar problemas de tela antes de validar se o usuário já possui um token salvo.

## T — Tests

A validação foi feita de forma automatizada adicionando um pacote de testes dedicado em tests/test_auth.py. Foram criados 9 cenários de teste específicos utilizando pytest com banco SQLite em memória. Eles cobrem fluxo perfeito de signup e login, rejeição de e-mails duplicados, bloqueio de acessos não autenticados na rota protegida /me e invalidação real do token no banco após o logout.

## O — Optimize

Complexidade: A busca por usuários por e-mail e a validação de tokens operam em tempo constante O(1) ou quase constante devido aos índices nativos do banco de dados sobre chaves primárias e campos únicos.
