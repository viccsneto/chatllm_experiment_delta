# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem

Autenticação do usuário.

O sistema deve permitir que o usuário realize cadastro para que suas sessões sejam persistidas pela sua conta.

## Steps
- [ ] Criar modelo do usuário no banco de dados. No modelo, criar FKs que podem ter 0+ Sessions relacionadas.
- [ ] Criar sistema de cadastro/login do usuário apenas com login e senha.
- [ ] Criar botão no topo superior direito que leva o usuário à tela de login. A tela de login deve ter um link para a tela de cadastro.
Caso o usuário esteja logado, o botão deve ser substituído por "Logout", que faz o Logout do usuário quando desejar.
- [ ] Fazer a relação das sessões com o usuário. Quando o usuário realizar o login/cadastro/logout, todas as sessões em memória local devem ser limpas.
1. Cadastro: todas as sessões locais são limpas
2. Login: todas as sessões locais são limpas e as sessões do usuário são carregadas (se existentes)
3. Logout: todas as sessões do usuário PERMANECEM salvas no banco de dados mas são limpas de memória local.
No caso de login/cadastro, as sessões que estavam em memória local devem também ser excluídas do banco de dados.

## Success Looks Like
- [ ] Se o usuário não estiver autenticado, suas sessões devem ser salvas em memória local.
- [ ] Se o usuário estiver autenticado, suas sessões devem ser armazenadas no banco de dados e relacionadas à seu modelo.
- [ ] Se o usuário fizer login/cadastro, suas sessões enquanto não autenticado devem ser excluídas do banco de dados
- [ ] Se o usuário fizer login/cadastro, as sessões relacionadas à ele no banco de dados devem ser carregadas
- [ ] Se o usuário fizer logout, as sessões relacionadas à ele CONTINUARÃO salvas no banco mas serão apagadas de memória local

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
