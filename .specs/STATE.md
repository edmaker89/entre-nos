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
- **Phase / Task**: Tasks; 28 tarefas propostas em quatro fases.
- **Completed**: Specify e Design aprovados; AD-005 registra sessão por cookie; tasks.md contém matriz e validações estruturais.
- **In-progress**: Confirmar ferramentas/testes e oferecer execução em lotes com subagentes conforme skill.
- **Next step**: Incorporar resposta; ler implement.md completo; materializar gates e executar T1 em diante.
- **Blockers**: Confirmação de Tasks exigida pela skill; nenhum código foi implementado.
- **Uncommitted files**: .specs/STATE.md e documentos de controle-familiar.
- **Branch**: Nenhuma; pasta ainda não é repositório Git.
