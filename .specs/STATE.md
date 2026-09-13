# STATE

## Decisions

### AD-001
- **Decision**: Conduzir o projeto com tlc-spec-driven, com requisitos rastreáveis e verificação independente ao final de Execute.
- **Reason**: Solicitação explícita do usuário.
- **Trade-off**: Especificação e aprovação precedem o desenho e a implementação.
- **Scope**: Todo o projeto.
- **Date**: 2026-09-10
- **Status**: active

### AD-002
- **Decision**: Usar PostgreSQL diretamente na VM existente, sem Supabase.
- **Reason**: Escolha explícita do usuário; VM com 2 GB de RAM e 4 vCPUs.
- **Trade-off**: Operação do banco, backup/restauração e autenticação ficam sob responsabilidade do projeto.
- **Scope**: Persistência e implantação de toda a aplicação.
- **Date**: 2026-09-10
- **Status**: active

### AD-003
- **Decision**: Implantar com Docker Compose na VM dedicada exclusivamente à aplicação (2 GB RAM, 4 vCPUs).
- **Reason**: Direcionamento explícito do usuário para simplificar a operação do serviço.
- **Trade-off**: Os componentes compartilham recursos e disponibilidade de uma única VM.
- **Scope**: Implantação da aplicação.
- **Date**: 2026-09-10
- **Status**: active

### AD-004
- **Decision**: Usar Alembic para migrações versionadas do PostgreSQL, na stack React/FastAPI confirmada pelo usuário ao autorizar continuidade.
- **Reason**: Solicitação explícita para facilitar evolução do banco.
- **Trade-off**: Alterações de esquema exigem revisão e migração versionada junto do código.
- **Scope**: Persistência e entregas do backend.
- **Date**: 2026-09-10
- **Status**: active

### AD-005
- **Decision**: Autenticar a aplicação web com sessão opaca no PostgreSQL e cookie HttpOnly/Secure, sem JWT de acesso/refresh.
- **Reason**: Usuário aceitou a recomendação de controle centralizado e revogação simples.
- **Trade-off**: Requisições autenticadas consultam a sessão no banco.
- **Scope**: Autenticação web.
- **Date**: 2026-09-10
- **Status**: active

### AD-006
- **Decision**: Representar a responsabilidade financeira com snapshots explícitos por parcela e ocorrência; compromisso e recorrência permanecem templates apenas para obrigações futuras.
- **Reason**: Usuário aprovou a abordagem A, que permite transferir somente obrigações abertas sem reescrever histórico pago.
- **Trade-off**: O banco terá mais linhas e a migração precisa fazer backfill e validar equivalência de totais.
- **Scope**: Domínio financeiro, consultas mensais, edições, transferências, recorrências e antecipações.
- **Date**: 2026-09-12
- **Status**: active

## Handoff

- **Feature**: gestao-e-experiencia-v2 — `.specs/features/gestao-e-experiencia-v2/`
- **Phase / Task**: Fases 1–2 concluídas; próxima tarefa T14 da Fase 3.
- **Completed**: T1–T13 em commits atômicos. A Fase 2 entregou snapshots de parcelas/ocorrências, prévia e aplicação transacional de transferência, cronograma reutilizável e edição completa segura nos commits `6ffc008`, `d219837`, `23c957c`, `46a1587`, `67afc8e` e `90df1d5`.
- **Verification**: gate transversal Full Backend com 161 testes, Ruff/compile/import e Alembic check; zero falhas/skips. Gate frontend da Fase 1 permanece com 37 testes unitários e build TypeScript/Vite.
- **Database safety**: somente PostgreSQL efêmero `expense-flow-phase2-test` na porta 55433 foi usado. O banco local com dados reais na porta 55432 e o Compose 8089 não foram alterados. Backup validado: `backups/before-gestao-experiencia-v2-20260912-144607.dump`.
- **Next step**: executar T14 — modal de transferência — e depois T15–T19 em ordem.
- **Blockers**: nenhum.
- **Uncommitted files**: apenas mudanças preexistentes do usuário fora desta feature.
- **Branch**: `codex/gestao-experiencia-v2`.
