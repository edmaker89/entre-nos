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
- **Phase / Task**: Fases 1–5 concluídas; próxima tarefa T30 da Fase 6.
- **Completed**: T1–T29 em commits atômicos. A Fase 5 entregou solicitação genérica, token hash-only de 15 minutos, limites por email/origem, Resend atrás de adaptador, conclusão concorrente de uso único, revogação atômica de sessões/tokens e telas seguras nos commits `0f47691`, `35ab596` e `0f69537`.
- **Verification**: gate transversal passou com 232/232 testes backend, Ruff/compile/import, Alembic check, 119/119 testes frontend, build TypeScript/Vite e 33/33 E2E; zero falhas/skips. Concorrência real de reset confirmou exatamente um vencedor, e nenhum teste enviou email real.
- **Database safety**: somente PostgreSQL efêmero `expense-flow-phase5-db` na porta 65434 foi usado e removido ao final. O banco local com dados reais na porta 55432, o volume `expense-flow-dev-data` e o Compose 8089 não foram alterados. Backup validado permanece em `backups/before-gestao-experiencia-v2-20260912-144607.dump`.
- **Next step**: executar T30–T36 da Fase 6 — catálogo e experiência visual de cartões, prontidão operacional e aceitação integrada.
- **Blockers**: nenhum.
- **Uncommitted files**: apenas mudanças preexistentes do usuário fora desta feature.
- **Branch**: `codex/gestao-experiencia-v2`.
