# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
Implementar autenticação de usuários com email e senha. Usuários devem poder se cadastrar, fazer login, ter a sessão mantida e poder fazer logout.

## Steps
- [ ] Criar o model do usuário no banco (email e senha hasheada)
- [ ] Exigir que a senha seja forte (Pelo menos 8 caracteres, Pelo menos 1 numero, Pelo menos 1 caracter especial, Pedir confirmação da senha)
- [ ] Criar endpoints de cadastro, login, logout
- [ ] Adicionar autenticador e proteger as rotas que devem ser protegidas (JWT)
- [ ] Implementar UI de cadastro e login no frontend
- [ ] Testar o fluxo completo

## Success Looks Like
- [ ] Usuário consegue se cadastrar com email e senha
- [ ] Usuario consegue fazer login com email e senha
- [ ] Após logout, voltar a tela de login
- [ ] Sessão deve persistir ao recarregar a pagina (ate o logout)

## Notes
- [ ] Retornar erro em portugues user-friendly caso o email ja esteja cadastrado no banco
- [ ] Retornar erro em portugues user-friendly caso o email esteja escrito no formato errado
- [ ] Retornar erro em portugues user-friendly caso haja alguma credencial errada no login

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
