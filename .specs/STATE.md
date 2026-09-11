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

## Handoff

- **Feature**: controle-familiar — .specs/features/controle-familiar/
- **Phase / Task**: Implementação e verificação automatizada concluídas; UAT humano pendente.
- **Completed**: T1–T36 em commits atômicos. Verifier independente: PASS, 58/58 critérios, 105 testes (73 backend + 13 frontend unit + 19 E2E), seis mutantes detectados. Lint, build e Alembic check passaram.
- **Deploy local**: Compose expense-flow-validation em http://localhost:8089 atualizado; backup/restauração e persistência após restart verificados. VM remota não foi alterada.
- **Última solicitação**: usuário pediu limpeza do banco da aplicação local e criação de seu acesso. Limpeza executada preservando Alembic; usuário Douglas criado e login validado com totais zerados. Credenciais em .env.local-access, modo 600, ignorado pelo Git. A demonstração anterior foi removida.
- **Backup pré-limpeza**: backups/before-local-reset-20260911-063912.dump (local, ignorado pelo Git).
- **Next step**: Usuário testar aplicação vazia com seu acesso. Para implantação remota ainda faltam destino/acesso à VM e domínio/configuração HTTPS.
- **Blockers**: Nenhum para uso local. Não executar smoke de seed no banco limpo sem necessidade; ele cria dados de teste.
- **Branch**: main.
- **Ambiente dev separado**: Postgres expense-flow-postgres localhost:55432 e API8000 permanecem para testes; não são o banco da aplicação8089.
