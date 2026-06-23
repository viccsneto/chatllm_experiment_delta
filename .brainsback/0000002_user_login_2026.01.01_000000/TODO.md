# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem
Precisa fazer 1. Cadastro/login por email e senha, Logout funcional, Dados de autenticacao persistidos no SQLite. Tem que criptar a senha por questões de segurança, token na sessão simples, uma tela de login simples.

## Steps
- [ ] Criar tabela `users` no SQLite com campos `id`, `email` (unique), `password_hash`, `created_at`
- [ ] Configurar hash de senha com bcrypt na camada de serviço
- [ ] Endpoint de registro: valida email/senha, gera hash, insere no banco, retorna 409 se email duplicado
- [ ] Endpoint de login: busca por email, compara hash, gera token de sessão simples (ex: UUID aleatório salvo no banco)
- [ ] Persistir token no cliente (localStorage) e criar guard que bloqueia rotas sem token
- [ ] Tela de login/cadastro simples com campos email + senha
- [ ] Em caso de falha no login, exibir "E-mail ou senha incorretos" sem distinguir qual está errado
- [ ] Endpoint de logout: deleta token do banco
- [ ] No cliente, logout remove token do localStorage e redireciona para login

## Success Looks Like
- [ ] COnseguir fazer cadastro com sucesso no banco
- [ ] Entrar na plataforma com sucesso com as credenciais certas
- [ ] Se inserir credenciais erradas, mostrar erro humanizado falando que e-mail ou senha errados(para nao entregar qual esta errado de cara)
- [ ] Poder sair normalmente

## Notes
- [ ] Não pode deixar entrar usuarios com credenciais erradas

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
