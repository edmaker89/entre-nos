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
- **Phase / Task**: Execute concluído; verificação independente final PASS.
- **Completed**: T1–T36 em commits atômicos; 9/9 requisitos e 60/60 critérios ancorados em `.specs/features/gestao-e-experiencia-v2/validation.md`.
- **Verification**: 263 backend, 169 frontend unitários, build e 42 E2E passaram sem skips; Compose smoke passou; discrimination sensor P0 matou 9/9 mutantes.
- **Database safety**: somente PostgreSQL/Compose efêmeros em 65436/8001/5174 foram usados e removidos. O banco local com dados reais na porta 55432, `expense-flow-dev-data` e o backup `backups/before-gestao-experiencia-v2-20260912-144607.dump` não foram alterados.
- **Next step**: UAT visual humano opcional e preparação do deploy HTTPS; nenhuma tarefa funcional pendente no escopo aprovado.
- **Blockers**: nenhum.
- **Uncommitted files**: apenas mudanças preexistentes do usuário fora desta feature.
- **Branch**: `codex/gestao-experiencia-v2`.
