# Gestão familiar, edição, perfil, recuperação e cartões — Tasks

## Protocolo de execução (obrigatório)

Implementar estas tarefas com a skill `tlc-spec-driven`: ativá-la por nome e seguir integralmente o fluxo Execute e suas Critical Rules. Cada tarefa produz um commit atômico somente depois de seu gate passar; testes não podem ser enfraquecidos, ignorados ou removidos para obter aprovação.

Se a skill não puder ser ativada, interromper a execução e informar o usuário.

**Design:** `.specs/features/gestao-e-experiencia-v2/design.md`  
**Status:** In Progress — tarefas, matriz, ferramentas e subagentes aprovados em 2026-09-12  
**Total:** 36 tarefas em 6 fases

---

## Test Coverage Matrix

> Gerada a partir do código, das configurações e da spec — confirmar antes de Execute. Diretrizes encontradas: `README.md` (seção Testes), `backend/pyproject.toml`, `frontend/package.json` e `frontend/playwright.config.ts`; não há `AGENTS.md`/`CONTRIBUTING.md` com política adicional. Amostras: `test_uow.py`, `test_auth.py`, `test_commitments.py`, `test_schema.py`, `test_money.py`, `CommitmentForm.test.tsx`, `Cards.test.tsx`, `client.test.ts` e `unified-entry.spec.ts`. Defaults fortes aplicados onde os arquivos não definem profundidade.

| Camada de código | Tipo de teste obrigatório | Expectativa de cobertura | Padrão de localização | Comando |
| --- | --- | --- | --- | --- |
| Domínio financeiro/autenticação | unitário | Todos os ramos; mapeamento 1:1 dos ACs e casos de borda | `backend/tests/unit/test_*.py` | `cd backend && uv run pytest -q tests/unit` |
| Modelos, migração, RLS e concorrência | integração PostgreSQL | Backfill, constraints, isolamento, rollback e conflitos reais | `backend/tests/integration/test_*.py` | `cd backend && uv run pytest -q tests/integration` |
| Rotas FastAPI | integração PostgreSQL | Toda rota: sucesso, validação, autorização, estado e falha | `backend/tests/integration/test_*.py` | `cd backend && uv run pytest -q tests/integration` |
| Adaptador de email/config | unitário | Sucesso, timeout/erro, idempotência, escaping e ausência de segredo em logs | `backend/tests/unit/test_*.py` | `cd backend && uv run pytest -q tests/unit` |
| Cliente/API e utilitários React | unitário | Todos os ramos públicos e preservação de retry/erro | `frontend/src/**/*.test.ts` | `cd frontend && npm run test:unit` |
| Componentes React | unitário | Estados, teclado, acessibilidade, erro, busy e preservação de formulário | `frontend/src/**/*.test.tsx` | `cd frontend && npm run test:unit` |
| Fluxos de usuário e responsividade | E2E | Caminho feliz + bordas/erros dos nove requisitos em 360/390/768/1440 | `frontend/e2e/*.spec.ts` | `cd frontend && npm run test:e2e` |
| Entidades/config sem comportamento isolado | nenhum | Build, lint, Alembic e smoke são o gate | — | gate Build/System |

## Gate Check Commands

> Gerados a partir do repositório — confirmar antes de Execute. E2E pressupõe API local em `127.0.0.1:8000` e PostgreSQL de desenvolvimento protegido pela fixture.

| Gate | Quando usar | Comando |
| --- | --- | --- |
| Quick Backend | Domínio/adaptador unitário | `cd backend && uv run pytest -q tests/unit && uv run ruff check app tests` |
| Quick Frontend | Cliente ou componente React | `cd frontend && npm run test:unit` |
| Full Backend | Migração, persistência ou rota | `./scripts/check-backend.sh && cd backend && uv run pytest -q && uv run alembic check` |
| Full Frontend | Fluxo visual integrado | `cd frontend && npm run test:unit && npm run build && npm run test:e2e` |
| Build/System | Fim de fase e entrega | `./scripts/check-backend.sh && (cd backend && uv run pytest -q && uv run alembic check) && (cd frontend && npm run test:unit && npm run build && npm run test:e2e)` |
| Deploy | Configuração/Compose | `docker compose config && docker compose build api web && python3 deploy/tests/smoke.py` |

## Ferramentas propostas

- Todas as tarefas: `apply_patch`, terminal local e `tlc-spec-driven`.
- T1, T8–T13 e T20–T30: Graphify para conferir relações antes de alterar domínio/autenticação.
- T5, T27 e T31: documentação oficial/web somente quando a API externa ou identidade visual exigir confirmação atual.
- T36 e UAT: Playwright; CUA apenas para inspeção visual complementar no navegador, sem substituir asserts.
- Git: um commit atômico por tarefa, preservando mudanças preexistentes do usuário.

## Plano de execução

As fases e tarefas são sequenciais. Cada seta corresponde ao `Depends on` da tarefa seguinte.

### Fase 1 — Fundação de dados, segurança e interface

```text
T1 → T2 → T3 → T4 → T5 → T6 → T7
```

### Fase 2 — Snapshots e edição financeira no backend

```text
T7 → T8 → T9 → T10 → T11 → T12 → T13
```

### Fase 3 — Modais e fluxos financeiros no frontend

```text
T13 → T14 → T15 → T16 → T17 → T18 → T19
```

### Fase 4 — Família, perfil e convites

```text
T19 → T20 → T21 → T22 → T23 → T24 → T25 → T26
```

### Fase 5 — Recuperação de senha

```text
T26 → T27 → T28 → T29
```

### Fase 6 — Cartões, operação e aceitação integrada

```text
T29 → T30 → T31 → T32 → T33 → T34 → T35 → T36
```

## Task Breakdown

### Fase 1 — Fundação de dados, segurança e interface

### T1: Criar esquema relacional e migração de backfill

**What:** Adicionar modelos e uma revisão Alembic para roles/código/versões, campos de cartão, snapshots, convites, resets e rate limits, incluindo RLS e backfill validado.  
**Where:** `backend/app/db/models.py`, `backend/alembic/versions/*_experience_v2.py`, `backend/tests/integration/test_schema.py`  
**Depends on:** None  
**Reuses:** `Financial`, constraints/FKs compostas e políticas da migração inicial  
**Requirement:** EDIT-01, FAMILY-01, INVITE-01, PROFILE-01, AUTH-RESET-01, CARD-CATALOG-01  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** upgrade em banco vazio e populado funciona; Douglas vira único owner ou a migração falha claramente; snapshots/cards preservam dados; RLS/constraints são provados; ≥12 novos casos/asserts; Full Backend passa sem reduzir testes.  
**Tests:** integração PostgreSQL  
**Gate:** Full Backend  
**Commit:** `feat(db): add experience v2 schema and backfill`

### T2: Implementar distribuição matricial de responsabilidade

**What:** Criar funções puras que transformam divisão agregada em pesos por obrigação com somas exatas por linha e coluna.  
**Where:** `backend/app/domain/responsibility.py`, `backend/tests/unit/test_responsibility.py`  
**Depends on:** T1  
**Reuses:** `app.domain.money.allocate`, `MAX_CENTS`  
**Requirement:** EDIT-01  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** cobre centavos, pesos zero, múltiplas parcelas, entradas inválidas e determinismo; ≥10 novos casos; Quick Backend passa.  
**Tests:** unitário  
**Gate:** Quick Backend  
**Commit:** `feat(domain): allocate responsibility snapshots exactly`

### T3: Separar autenticação de contexto familiar

**What:** Extrair `CurrentUser` de `FamilyID`, manter CSRF/sessão e rejeitar múltiplas memberships em vez de escolher a primeira.  
**Where:** `backend/app/api/auth.py`, `backend/app/api/permissions.py`, `backend/tests/integration/test_auth.py`  
**Depends on:** T2  
**Reuses:** `database`, `family_context`, sessão opaca e `digest`  
**Requirement:** INVITE-01, FAMILY-01, PROFILE-01  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** usuário sem família mantém sessão utilizável para convite; rotas financeiras ainda exigem família; zero/uma/múltiplas memberships cobertas; ≥6 novos casos; Full Backend passa.  
**Tests:** integração PostgreSQL  
**Gate:** Full Backend  
**Commit:** `refactor(auth): separate user session from family context`

### T4: Centralizar política de senha e rate limit seguro

**What:** Implementar política 15–200, comparação com hash atual e janelas atômicas com chaves HMAC para email/origem/família.  
**Where:** `backend/app/domain/passwords.py`, `backend/app/domain/rate_limits.py`, testes unitários e de integração correspondentes  
**Depends on:** T3  
**Reuses:** Argon2, `LoginWindow` e locks PostgreSQL  
**Requirement:** AUTH-RESET-01, INVITE-01  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** Unicode/espaços/tamanhos, senha igual, reset de janela e concorrência são cobertos; email/IP não ficam em claro; ≥10 novos casos; Full Backend passa.  
**Tests:** integração + unitário  
**Gate:** Full Backend  
**Commit:** `feat(auth): centralize password and rate limit policies`

### T5: Criar adaptador EmailSender e implementação Resend

**What:** Adicionar interface, templates texto/HTML, cliente Resend com timeout/idempotência e provider em memória para testes.  
**Where:** `backend/app/email/`, `backend/app/config.py`, `backend/pyproject.toml`, lock/requirements, `backend/tests/unit/test_email.py`  
**Depends on:** T4  
**Reuses:** `operation_id`, configuração Pydantic e domínio verificado  
**Requirement:** AUTH-RESET-01  
**Tools:** Local + documentação oficial/web; skill `tlc-spec-driven`  
**Done when:** sucesso, 409 idempotente, timeout, 4xx/5xx, escaping e logs sem segredo são cobertos; ≥8 casos; Quick Backend passa.  
**Tests:** unitário  
**Gate:** Quick Backend  
**Commit:** `feat(email): add resend sender adapter`

### T6: Enriquecer o contrato de erro do cliente React

**What:** Fazer `ApiError` preservar `code`, `fields`, `difference_cents` e `operation_id` sem quebrar retry idempotente.  
**Where:** `frontend/src/api/client.ts`, `frontend/src/api/client.test.ts`  
**Depends on:** T5  
**Reuses:** `api`, `createOperation`, `pendingOperations`  
**Requirement:** EDIT-01, EDIT-02, MODAL-01  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** respostas JSON/não JSON, rede, 401, 409 e 422 são tipadas e retry mantém identidade; ≥6 novos casos; Quick Frontend passa.  
**Tests:** unitário  
**Gate:** Quick Frontend  
**Commit:** `refactor(web): preserve structured api errors`

### T7: Criar o primitive acessível de modal

**What:** Entregar `Modal`, header/body/footer/close, erro, confirmação e guarda de alterações sobre `<dialog>`.  
**Where:** `frontend/src/components/modal/`, estilos e testes colocalizados  
**Depends on:** T6  
**Reuses:** tokens CSS, botões e Testing Library  
**Requirement:** MODAL-01  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** foco inicial/restauração, Tab, Escape, backdrop, scroll, busy, confirmação e 360–1440 são cobertos; ≥12 casos; Quick Frontend passa.  
**Tests:** unitário de componente  
**Gate:** Quick Frontend  
**Commit:** `feat(modal): add accessible composable dialog primitive`

### Fase 2 — Snapshots e edição financeira no backend

### T8: Persistir e ler snapshots de parcelas

**What:** Criar snapshots ao cadastrar/importar/reconstruir parcelas e trocar detalhes/mês/previsão para a tabela por parcela.  
**Where:** `backend/app/api/commitments.py`, `imports.py`, `months.py`, serviço de responsabilidade e testes  
**Depends on:** T7  
**Reuses:** `persist_purchase`, `month_data`, `allocate`  
**Requirement:** EDIT-01, EDIT-02  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** criação/importação preservam totais, filtro por pessoa usa snapshot e templates não reescrevem pago; ≥8 casos; Full Backend passa.  
**Tests:** integração PostgreSQL  
**Gate:** Full Backend  
**Commit:** `feat(finance): snapshot installment responsibility`

### T9: Persistir e ler snapshots de ocorrências

**What:** Fotografar responsabilidade em `materialize()` e usar ocorrência, não JSON da regra, nas consultas mensais.  
**Where:** `backend/app/api/recurrences.py`, `months.py`, serviço de responsabilidade e testes  
**Depends on:** T8  
**Reuses:** `materialize`, `Occurrence`, regras de propagação variável  
**Requirement:** EDIT-01  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** ocorrências antigas mantêm responsáveis após mudança do template e recorrência paga fica imutável; ≥6 casos; Full Backend passa.  
**Tests:** integração PostgreSQL  
**Gate:** Full Backend  
**Commit:** `feat(finance): snapshot recurring responsibility`

### T10: Implementar prévia de transferência

**What:** Criar comando/rota que calcula antes/depois para todas as parcelas abertas e lista meses e antecipações planejadas.  
**Where:** `backend/app/domain/responsibility.py`, `backend/app/api/commitment_changes.py`, testes  
**Depends on:** T9  
**Reuses:** `details`, `AdvanceItem`, `check_version`  
**Requirement:** EDIT-01 AC1, AC3, AC4  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** prévia 100%, divisão agregada, zero abertas, antecipação e `preview_hash` são cobertos; ≥7 casos; Full Backend passa.  
**Tests:** integração + unitário  
**Gate:** Full Backend  
**Commit:** `feat(commitments): preview open responsibility transfer`

### T11: Implementar transferência transacional

**What:** Aplicar a prévia sob lock, substituir somente snapshots abertos, reabrir meses e auditar ator/campos.  
**Where:** `backend/app/api/commitment_changes.py`, testes de integração/concorrência  
**Depends on:** T10  
**Reuses:** `operation`, `check_version`, `reopen_month`, `Audit`  
**Requirement:** EDIT-01 AC2, AC5–AC7  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** 2 pagas/2 abertas, conflito entre prévia/confirmação, rollback e retry idempotente são provados; ≥8 casos; Full Backend passa.  
**Tests:** integração PostgreSQL  
**Gate:** Full Backend  
**Commit:** `feat(commitments): transfer open responsibility atomically`

### T12: Extrair serviço e prévia de edição completa

**What:** Extrair cálculo de cronograma e criar prévia com campos permitidos, antes/depois, ciclos e planos afetados.  
**Where:** `backend/app/domain/commitments.py`, `backend/app/api/commitment_changes.py`, testes  
**Depends on:** T11  
**Reuses:** `preview_purchase`, `ensure_cycle`, `editable`  
**Requirement:** EDIT-02 AC2–AC4  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** não pago permite todos os campos; parcialmente pago bloqueia recálculo; plano previsto e ciclo conferido aparecem; ≥10 casos; Full Backend passa.  
**Tests:** integração + unitário  
**Gate:** Full Backend  
**Commit:** `refactor(commitments): add reusable edit schedule preview`

### T13: Implementar edição completa transacional

**What:** Expandir PATCH para alterações permitidas, reconstrução atômica, cancelamento seguro de planos abertos e audit event.  
**Where:** `backend/app/api/commitment_changes.py`, testes de integração  
**Depends on:** T12  
**Reuses:** serviço T12, `operation`, `check_version`, snapshots T8  
**Requirement:** EDIT-02 AC2, AC3, AC7  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** edição não paga e parcial, erro intermediário/rollback, idempotência e auditoria são provados; ≥8 casos; Full Backend passa.  
**Tests:** integração PostgreSQL  
**Gate:** Full Backend  
**Commit:** `feat(commitments): apply full safe edits`

### Fase 3 — Modais e fluxos financeiros no frontend

### T14: Criar modal de transferência de responsabilidade

**What:** Implementar atalho 100%, divisão avançada, prévia e confirmação com preservação de conflito/inputs.  
**Where:** `frontend/src/components/commitments/TransferResponsibilityModal.tsx` e teste  
**Depends on:** T13  
**Reuses:** Modal T7, `ApiError`, `money`, members  
**Requirement:** EDIT-01  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** mostra atual/destino/quantidade/meses/planos, valida soma e trata stale preview; ≥8 casos; Quick Frontend passa.  
**Tests:** unitário de componente  
**Gate:** Quick Frontend  
**Commit:** `feat(web): add responsibility transfer modal`

### T15: Criar modal de edição completa

**What:** Reutilizar campos do cadastro, exibir bloqueios por pagamento e antes/depois do cronograma.  
**Where:** `frontend/src/components/commitments/EditCommitmentModal.tsx` e teste  
**Depends on:** T14  
**Reuses:** Modal T7 e campos/conversões de `CommitmentForm`  
**Requirement:** EDIT-02  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** prefill, dirty guard, campos bloqueados, erros por campo, busy e confirmação são cobertos; ≥10 casos; Quick Frontend passa.  
**Tests:** unitário de componente  
**Gate:** Quick Frontend  
**Commit:** `feat(web): add full commitment edit modal`

### T16: Migrar ações do detalhe do compromisso

**What:** Compor detalhe, competência, antecipação/pagamento e exclusão com os novos modais, removendo prompts desse fluxo.  
**Where:** `frontend/src/pages/Commitment.tsx`, componentes de ação e testes  
**Depends on:** T15  
**Reuses:** Modal T7, T14, T15 e APIs existentes  
**Requirement:** EDIT-01, EDIT-02, MODAL-01  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** todas as ações anteriores continuam possíveis sem diálogo nativo; cancelamento/erro preservam estado; ≥8 casos; Quick Frontend passa.  
**Tests:** unitário de componente  
**Gate:** Quick Frontend  
**Commit:** `refactor(web): compose commitment actions with modals`

### T17: Migrar pagamentos e fechamento do resumo

**What:** Substituir data/confirm de pagamento de parcela/fatura e avanço de mês por modais compostos.  
**Where:** `frontend/src/pages/Overview.tsx`, componentes de pagamento/confirmação e testes  
**Depends on:** T16  
**Reuses:** Modal T7, endpoints de pagamento/mês  
**Requirement:** MODAL-01  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** pagamento simples/fatura, reabertura e fechamento mensal não usam API nativa e anunciam escopo; ≥7 casos; Quick Frontend passa.  
**Tests:** unitário de componente  
**Gate:** Quick Frontend  
**Commit:** `refactor(web): replace overview native dialogs`

### T18: Migrar ações de recorrências

**What:** Criar modal de valor, encerramento e exclusão de recorrência e integrá-los ao gerenciador.  
**Where:** `frontend/src/pages/RecurrenceManager.tsx`, componentes de recorrência e testes  
**Depends on:** T17  
**Reuses:** Modal T7 e APIs de recorrência  
**Requirement:** MODAL-01  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** três ações preservam valores/erros e confirmação destrutiva é interna; ≥6 casos; Quick Frontend passa.  
**Tests:** unitário de componente  
**Gate:** Quick Frontend  
**Commit:** `refactor(web): replace recurrence native dialogs`

### T19: Migrar formulários existentes e zerar diálogos nativos

**What:** Converter AddExpense/CommitmentForm/ScheduledExpenseForm e estruturas diretas restantes ao primitive; criar gate de regressão.  
**Where:** `frontend/src/components/`, estilos, testes existentes  
**Depends on:** T18  
**Reuses:** Modal T7 e formulários existentes  
**Requirement:** MODAL-01  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** `rg 'window\.(alert|prompt|confirm)' frontend/src` e renderizações diretas de `.dialog-backdrop` retornam zero; 360/390/768/1440 sem overflow; ≥6 casos; Full Frontend passa.  
**Tests:** unitário + E2E  
**Gate:** Full Frontend  
**Commit:** `refactor(web): standardize all product dialogs`

### Fase 4 — Família, perfil e convites

### T20: Criar leitura familiar e autorização owner/member

**What:** Implementar `require_owner` e GET familiar com papéis, integrantes, código e convites sem segredo.  
**Where:** `backend/app/api/family.py`, `permissions.py`, `main.py`, testes  
**Depends on:** T19  
**Reuses:** `FamilyID`, RLS, `serialize`  
**Requirement:** FAMILY-01 AC1–AC4, AC7  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** Douglas/Vanessa/terceira família recebem dados e capacidades corretos; hash/token nunca retorna; ≥7 casos; Full Backend passa.  
**Tests:** integração PostgreSQL  
**Gate:** Full Backend  
**Commit:** `feat(family): expose isolated family management view`

### T21: Implementar nome e rotação do código familiar

**What:** Criar mutações owner-only, versionadas/idempotentes, com código curto único e auditoria.  
**Where:** `backend/app/api/family.py`, testes  
**Depends on:** T20  
**Reuses:** `require_owner`, `operation`, `Audit`  
**Requirement:** FAMILY-01 AC5–AC7  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** nome 1–100, colisão/retry de código, member/outsider e conflito de versão são cobertos; owner não tem remoção; ≥7 casos; Full Backend passa.  
**Tests:** integração PostgreSQL  
**Gate:** Full Backend  
**Commit:** `feat(family): manage family name and code`

### T22: Implementar criação, listagem e revogação de convites

**What:** Criar endpoints owner-only com hash, 7 dias, limite, resposta one-time do link e revogação.  
**Where:** `backend/app/api/family_invites.py`, testes  
**Depends on:** T21  
**Reuses:** rate limit T4, `PUBLIC_APP_URL`, RLS e `operation`  
**Requirement:** INVITE-01 AC1, AC6, AC8  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** token bruto só aparece na criação; lista/revogação/renovação/limite e autorização são cobertos; ≥9 casos; Full Backend passa.  
**Tests:** integração PostgreSQL  
**Gate:** Full Backend  
**Commit:** `feat(family): create and revoke secure invites`

### T23: Implementar inspeção e consumo público do convite

**What:** Criar POST inspect/accept/register com token limpo, sessão para cadastro e consumo concorrente único.  
**Where:** `backend/app/api/invite_auth.py`, helpers de sessão, testes  
**Depends on:** T22  
**Reuses:** CurrentUser T3, política T4, RLS por family_id do token  
**Requirement:** INVITE-01 AC5–AC7, D12  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** conta nova/existente, mesma/outra família, expirado/revogado/usado e concorrência são cobertos; cadastro público segue fechado; ≥12 casos; Full Backend passa.  
**Tests:** integração PostgreSQL  
**Gate:** Full Backend  
**Commit:** `feat(auth): accept family invites safely`

### T24: Implementar perfil próprio

**What:** Criar GET/PATCH de nome próprio, versionado, com email somente leitura e atualização de referências por identidade.  
**Where:** `backend/app/api/profile.py`, `auth.py`, testes  
**Depends on:** T23  
**Reuses:** CurrentUser, `operation`, `Audit`  
**Requirement:** PROFILE-01  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** nome válido atualiza `/me`/integrantes, email não é mutável e outro usuário não pode editar; ≥6 casos; Full Backend passa.  
**Tests:** integração PostgreSQL  
**Gate:** Full Backend  
**Commit:** `feat(profile): allow editing own display name`

### T25: Criar área Família e perfil na navegação

**What:** Extrair AppShell/Sidebar/Topbar, tornar família e nome acionáveis e implementar telas/modais conforme capacidades.  
**Where:** `frontend/src/layout/`, `frontend/src/pages/Family.tsx`, `ProfileModal.tsx`, `App.tsx`, testes  
**Depends on:** T24  
**Reuses:** Modal T7, auth data e layout atual  
**Requirement:** FAMILY-01, PROFILE-01  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** owner/member veem ações corretas, perfil atualiza topo/seletores e acesso móvel “Família” existe; ≥10 casos; Quick Frontend passa.  
**Tests:** unitário de componente  
**Gate:** Quick Frontend  
**Commit:** `feat(web): add family management and profile entry points`

### T26: Criar compartilhamento e landing de convite

**What:** Implementar modal one-time, Web Share/WhatsApp/cópia e landing para login/cadastro com limpeza imediata da URL.  
**Where:** `frontend/src/components/family/`, `frontend/src/pages/InviteLanding.tsx`, `App.tsx`, testes  
**Depends on:** T25  
**Reuses:** Modal, API T22/T23, `navigator.share`, clipboard  
**Requirement:** INVITE-01 AC2–AC7  
**Tools:** Local + documentação oficial; skill `tlc-spec-driven`  
**Done when:** três fallbacks, aviso localhost, token fora do histórico, conta nova/existente e estados inválidos são cobertos; ≥12 unitários/E2E; Full Frontend passa.  
**Tests:** unitário + E2E  
**Gate:** Full Frontend  
**Commit:** `feat(web): share and consume family invitations`

### Fase 5 — Recuperação de senha

### T27: Implementar solicitação e entrega de reset

**What:** Criar rota genérica, token hash-only, limites, tarefa pós-commit e envio Resend com status seguro.  
**Where:** `backend/app/api/password_reset.py`, email/config, testes  
**Depends on:** T26  
**Reuses:** T4, T5, `BackgroundTasks`, `operation_id`  
**Requirement:** AUTH-RESET-01 AC1, AC2, AC6, AC7  
**Tools:** Local + Graphify + docs oficiais Resend; skill `tlc-spec-driven`  
**Done when:** existente/inexistente têm resposta idêntica; 3/email e 10/origem; sucesso/falha/timeout não vazam token/email; ≥12 casos; Full Backend passa.  
**Tests:** integração + unitário  
**Gate:** Full Backend  
**Commit:** `feat(auth): request password reset by email`

### T28: Implementar validação e conclusão do reset

**What:** Criar validate/complete com lock, 15 minutos, uso único, senha diferente e revogação atômica de sessões/tokens.  
**Where:** `backend/app/api/password_reset.py`, testes de integração/concorrência  
**Depends on:** T27  
**Reuses:** política T4, Argon2, sessão opaca  
**Requirement:** AUTH-RESET-01 AC3–AC5, AC8  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** válido/expirado/usado/inexistente/concorrente e senha igual são cobertos; apenas um concorrente vence; ≥10 casos; Full Backend passa.  
**Tests:** integração PostgreSQL  
**Gate:** Full Backend  
**Commit:** `feat(auth): complete one-time password reset`

### T29: Criar telas de esquecimento e redefinição

**What:** Adicionar link no login, solicitação genérica e página de nova senha que limpa token/referrer e volta ao login.  
**Where:** `frontend/src/pages/ForgotPassword.tsx`, `ResetPassword.tsx`, `Login.tsx`, `App.tsx`, testes  
**Depends on:** T28  
**Reuses:** Modal/form errors, APIs T27/T28  
**Requirement:** AUTH-RESET-01 AC1, AC4, AC8, AC9  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** estados sucesso/erro, senha Unicode/espaços, token removido do histórico e sessão revogada são cobertos; ≥10 unitários/E2E; Full Frontend passa.  
**Tests:** unitário + E2E  
**Gate:** Full Frontend  
**Commit:** `feat(web): add password recovery flow`

### Fase 6 — Cartões, operação e aceitação integrada

### T30: Estruturar API e catálogo de instituições do cartão

**What:** Validar chaves/redes/custom/últimos quatro, expor catálogo e manter compatibilidade dos cartões migrados.  
**Where:** `backend/app/domain/card_catalog.py`, `backend/app/api/cards.py`, testes  
**Depends on:** T29  
**Reuses:** Card T1, `CardInput`, `operation`  
**Requirement:** CARD-CATALOG-01  
**Tools:** Local + Graphify; skill `tlc-spec-driven`  
**Done when:** 16 opções incluindo Neon, custom, networks, last_four e rejeição de PAN/CVV são cobertos; ≥12 casos; Full Backend passa.  
**Tests:** integração + unitário  
**Gate:** Full Backend  
**Commit:** `feat(cards): structure institution and network catalog`

### T31: Criar temas acessíveis das instituições

**What:** Definir catálogo visual/tokens por chave e testes automatizados de contraste/estabilidade.  
**Where:** `frontend/src/domain/cardInstitutions.ts` e teste  
**Depends on:** T30  
**Reuses:** fontes oficiais levantadas no Design e tokens do produto  
**Requirement:** CARD-CATALOG-01 AC4–AC7  
**Tools:** Local + pesquisa oficial de marca; skill `tlc-spec-driven`  
**Done when:** todas as 16 chaves têm tema/fallback estável, sem hotlink/logo copiado, contraste 4,5:1/3:1; ≥20 asserts; Quick Frontend passa.  
**Tests:** unitário  
**Gate:** Quick Frontend  
**Commit:** `feat(cards): add accessible institution themes`

### T32: Criar CardFormModal pesquisável

**What:** Implementar cadastro/edição com instituição pesquisável, Outra, bandeira, final e prévia de tema.  
**Where:** `frontend/src/components/cards/CardFormModal.tsx` e teste  
**Depends on:** T31  
**Reuses:** Modal T7, catálogo T31, members  
**Requirement:** CARD-CATALOG-01 AC1–AC5, AC8  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** catalogada/custom, troca de tema, network opcional, quatro dígitos e erros preservados são cobertos; ≥10 casos; Quick Frontend passa.  
**Tests:** unitário de componente  
**Gate:** Quick Frontend  
**Commit:** `feat(cards): add searchable card form modal`

### T33: Criar cartão visual proporcional e grade compacta

**What:** Implementar `PaymentCard` e `CardsGrid` com proporção ID-1, conteúdo compacto e ações discretas.  
**Where:** `frontend/src/components/cards/PaymentCard.tsx`, `CardsGrid.tsx`, estilos e testes  
**Depends on:** T32  
**Reuses:** temas T31 e dados estruturados T30  
**Requirement:** CARD-UX-01  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** apelido/instituição/titular/final/bandeira/datas aparecem; 1/4/12 itens e quatro viewports sem overflow; ≥8 casos; Quick Frontend passa.  
**Tests:** unitário de componente  
**Gate:** Quick Frontend  
**Commit:** `feat(cards): render compact proportional cards`

### T34: Integrar cartões e substituir diálogos de fatura

**What:** Refatorar Cards para usar grade/form e modais de fechamento/pagamento, removendo prompts remanescentes.  
**Where:** `frontend/src/pages/Cards.tsx`, componentes de ciclo e testes  
**Depends on:** T33  
**Reuses:** T7, T32, T33 e APIs de ciclos/faturas  
**Requirement:** CARD-UX-01, CARD-CATALOG-01, MODAL-01  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** CRUD e faturas preservam comportamento, preview de fechamento e pagamento usam modal, busy/erro são acessíveis; ≥9 casos; Full Frontend passa.  
**Tests:** unitário + E2E  
**Gate:** Full Frontend  
**Commit:** `refactor(cards): integrate compact cards and cycle modals`

### T35: Configurar prontidão, Compose e documentação operacional

**What:** Propagar env de email/link/rate limit, criar `/ready`, atualizar Compose/README/example e smoke sem expor chave.  
**Where:** `.env.example`, `compose.yaml`, `backend/app/config.py`, `main.py`, `deploy/tests/smoke.py`, `README.md`  
**Depends on:** T34  
**Reuses:** healthcheck, Caddy e Compose atuais  
**Requirement:** AUTH-RESET-01, INVITE-01, casos transversais  
**Tools:** Local; skill `tlc-spec-driven`  
**Done when:** config inválida falha claramente, localhost/dev e HTTPS/deploy são aceitos conforme regra, `.env` segue ignorado e smoke não envia email real; ≥5 casos; Deploy e Build/System passam.  
**Tests:** integração/config + smoke  
**Gate:** Deploy + Build/System  
**Commit:** `chore(deploy): configure email and public link readiness`

### T36: Fechar aceitação integrada dos nove requisitos

**What:** Adicionar cenários Playwright finais, atualizar documentação de rastreabilidade e executar a suíte completa em estado limpo.  
**Where:** `frontend/e2e/experience-v2.spec.ts`, artefatos `.specs`  
**Depends on:** T35  
**Reuses:** helpers E2E, dados isolados e todos os fluxos T8–T35  
**Requirement:** EDIT-01, EDIT-02, MODAL-01, FAMILY-01, INVITE-01, PROFILE-01, AUTH-RESET-01, CARD-UX-01, CARD-CATALOG-01  
**Tools:** Local + Playwright; CUA opcional para inspeção; skill `tlc-spec-driven`  
**Done when:** 9/9 requisitos têm evidência ponta a ponta, quatro viewports passam, `rg` de diálogos nativos zera, Build/System passa com contagem registrada e sem exclusão/skip de testes.  
**Tests:** E2E integrado  
**Gate:** Build/System  
**Commit:** `test(e2e): cover experience v2 acceptance`

## Phase Execution Map

```text
Fase 1               Fase 2                  Fase 3
T1→T2→T3→T4→T5→T6→T7 → T8→T9→T10→T11→T12→T13 → T14→T15→T16→T17→T18→T19

Fase 4                         Fase 5              Fase 6
→ T20→T21→T22→T23→T24→T25→T26 → T27→T28→T29 → T30→T31→T32→T33→T34→T35→T36
```

Execução estritamente sequencial. As fases têm 7, 6, 6, 7, 3 e 7 tarefas e serão empacotadas em lotes de fases inteiras; nenhum lote começa antes do anterior concluir e reportar seus commits/gates.

## Diagram-Definition Cross-Check

| Tarefa | Depends on no corpo | Seta no diagrama | Status |
| --- | --- | --- | --- |
| T1 | None | início | ✅ |
| T2–T7 | tarefa imediatamente anterior | T1→…→T7 | ✅ |
| T8–T13 | tarefa imediatamente anterior, começando em T7 | T7→…→T13 | ✅ |
| T14–T19 | tarefa imediatamente anterior, começando em T13 | T13→…→T19 | ✅ |
| T20–T26 | tarefa imediatamente anterior, começando em T19 | T19→…→T26 | ✅ |
| T27–T29 | tarefa imediatamente anterior, começando em T26 | T26→…→T29 | ✅ |
| T30–T36 | tarefa imediatamente anterior, começando em T29 | T29→…→T36 | ✅ |

Nenhuma dependência aponta para fase posterior e nenhuma seta adicional existe.

## Task Granularity Check

| Grupo | Unidade de entrega | Status |
| --- | --- | --- |
| T1 | Uma revisão de esquema/migração coerente | ✅ Granular |
| T2, T4–T7, T31 | Um primitive/serviço/contrato | ✅ Granular |
| T3, T8–T13, T20–T24, T27–T30 | Uma capacidade de backend/rota coesa | ✅ Granular |
| T14–T19, T25–T26, T32–T34 | Um componente ou fluxo visual coeso | ✅ Granular |
| T35 | Uma entrega operacional de prontidão | ✅ Granular |
| T36 | Um gate de aceitação ponta a ponta | ✅ Granular |

## Test Co-location Validation

| Tarefas | Camada modificada | Matriz exige | Campo Tests | Status |
| --- | --- | --- | --- | --- |
| T1 | modelos/migração/RLS | integração | integração PostgreSQL | ✅ |
| T2 | domínio | unitário | unitário | ✅ |
| T3 | dependências/rotas de auth | integração | integração PostgreSQL | ✅ |
| T4 | auth/domínio/persistência | integração + unitário | integração + unitário | ✅ |
| T5 | adaptador/config | unitário | unitário | ✅ |
| T6 | cliente React | unitário | unitário | ✅ |
| T7 | componente React | unitário | unitário de componente | ✅ |
| T8–T13 | domínio/rotas/persistência | integração; unitário quando há função pura | integração + unitário indicado | ✅ |
| T14–T18 | componentes React | unitário | unitário de componente | ✅ |
| T19 | componentes + fluxo | unitário + E2E | unitário + E2E | ✅ |
| T20–T24 | rotas/persistência | integração | integração PostgreSQL | ✅ |
| T25 | componentes React | unitário | unitário de componente | ✅ |
| T26 | componente + fluxo | unitário + E2E | unitário + E2E | ✅ |
| T27 | adaptador/rota/persistência | unitário + integração | integração + unitário | ✅ |
| T28 | rota/concorrência | integração | integração PostgreSQL | ✅ |
| T29 | componentes + fluxo | unitário + E2E | unitário + E2E | ✅ |
| T30 | domínio/rota | unitário + integração | integração + unitário | ✅ |
| T31 | domínio React | unitário | unitário | ✅ |
| T32–T33 | componentes React | unitário | unitário de componente | ✅ |
| T34 | componente + fluxo | unitário + E2E | unitário + E2E | ✅ |
| T35 | config/deploy | build + integração/smoke | integração/config + smoke | ✅ |
| T36 | fluxo ponta a ponta | E2E | E2E integrado | ✅ |

## Pré-condição para Execute

- Usuário aprova tarefas, matriz de testes e ferramentas propostas.
- Como são 36 tarefas em múltiplos lotes, oferecer execução por subagentes antes de iniciar, conforme `tlc-spec-driven`; nunca despachar sem confirmação.
- Antes do primeiro código, ler integralmente `references/implement.md`; após T36, sempre executar Verifier novo e independente com discrimination sensor.
