# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem

O objetivo é criar um sistema básico de autenticação (cadastro, login e logout) utilizando e-mail e senha. A aplicação precisa persistir os dados dos usuários em um banco de dados SQLite para que as sessões ou estados de login não se percam ao reiniciar o servidor. O foco principal é a funcionalidade e a independência das rotas.

## Steps

- [ ] Configuração do Banco: Criar a tabela de usuários no SQLite (campos: id, email e senha).
- [ ] Endpoint de Cadastro: Criar a rota para receber e-mail e senha e salvar no banco.
- [ ] Endpoint de Login: Criar a rota que valida se o e-mail existe e se a senha bate com a salva no banco.
- [ ] Mecanismo de Sessão/Token: Implementar uma forma simples de identificar o usuário logado (geração de um token simples ou cookie de sessão).
- [ ] Endpoint de Logout: Criar a rota que invalida a sessão ou limpa o identificador do usuário ativo.
- [ ] Proteção de Rota: Criar uma rota privada só para garantir que o fluxo de autenticação está segurando o acesso.

## Success Looks Like

- [ ] Criar um usuário novo retorna status 201 Created (ou 200 OK) e o e-mail cadastrado aparece na tabela do SQLite.
- [ ] Fazer login com as credenciais certas retorna sucesso e um identificador/token de acesso.
- [ ] Fazer login com e-mail inexistente ou senha errada retorna erro (401 Unauthorized ou 400 Bad Request).
- [ ] Tentar acessar a rota protegida sem estar logado barra o acesso.
- [ ] Chamar o logout limpa o estado e, após isso, a rota protegida volta a ficar inacessível.

## Notes

- [ ] _Any specific edge cases, libraries to consider, or potential pitfalls._

---

**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
