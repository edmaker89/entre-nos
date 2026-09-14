# Gestão e experiência v2 — validação independente

**Data:** 2026-09-14
**Veredicto:** PASS ✅
**Spec:** `.specs/features/gestao-e-experiencia-v2/spec.md`
**Diff:** `3b2f68e..756bd73`
**Verificador:** subagente independente; autor ≠ verificador
**Ambiente:** PostgreSQL/Compose descartáveis; nenhum acesso ao banco `127.0.0.1:55432`, ao volume `expense-flow-dev-data` ou a provedor real de email.

---

## Resultado executivo

- Os 36 itens estão presentes em commits rastreáveis e as seis fases estão concluídas.
- Os nove requisitos e seus 60 critérios de aceitação têm evidência `arquivo:linha` com resultado observável compatível com a spec.
- Gate completo: 263 testes backend, 169 testes frontend unitários e 42 Playwright; 474/474 passaram, 0 falhas e 0 skips. Ruff, import/compile, build Vite e `alembic check` passaram.
- Sensor P0 ampliado: 9 mutações semânticas independentes, 9 mortas, 0 sobreviventes contados.
- Deploy smoke descartável passou com `EMAIL_PROVIDER=memory`: portas privadas, readiness, login, papel runtime sem bypass de RLS, persistência e restauração de backup.
- Busca estática retornou zero `window.alert`, `window.prompt`, `window.confirm`, backdrop direto, `skip`/`only` e segredo Resend versionado.

## Conclusão das tarefas

| Fase | Tarefas | Estado | Evidência |
| --- | --- | --- | --- |
| 1 — Fundação | T1–T7 | ✅ | `8b00577`, `9f467b8`, `d4d2a99`, `236c399`, `0510820`, `974297e`, `cdeac1d`, correção `81b659f` |
| 2 — Financeiro backend | T8–T13 | ✅ | `6ffc008`, `d219837`, `23c957c`, `46a1587`, `67afc8e`, `90df1d5` |
| 3 — Modais financeiros | T14–T19 | ✅ | `375a17e`, `f7382bf`, `8653df2`, `d25286d`, `c274742`, `c392d7f` |
| 4 — Família/perfil | T20–T26 | ✅ | `de91404`, `f4f7fd8`, `4755380`, `27ef237`, `349aab8`, `dcec908`, `777c09b`, correções `9f3d865`, `1cc03a0` |
| 5 — Reset | T27–T29 | ✅ | `0f47691`, `35ab596`, `0f69537` |
| 6 — Cartões/release | T30–T36 | ✅ | `62535de`, `c19b256`, `4248ff7`, `a64222c`, `665a0ff`, `3c93c39`, `f8180b5` |

## Critérios de aceitação ancorados na spec

As citações abaixo apontam para assertivas, não apenas para a existência de testes. Evidência composta entre domínio, integração PostgreSQL, componente e E2E é usada quando o critério atravessa camadas.

| Critério | Resultado definido | Evidência `arquivo:linha` + assertiva | Resultado |
| --- | --- | --- | --- |
| EDIT-01 AC1 | Prévia mostra atual, destino, quantidade e meses abertos | `backend/tests/integration/test_responsibility_transfer_preview.py:62-68` — versão, total, `open_installment_count == 2`, meses e before/after; `frontend/src/components/commitments/TransferResponsibilityModal.test.tsx:19-20` — Douglas/Vanessa, meses e antecipação visíveis | ✅ |
| EDIT-01 AC2 | Apenas abertas passam 100% a Vanessa; pagas intactas | `backend/tests/integration/test_responsibility_transfer_apply.py:97-105` — shares das duas pagas permanecem Douglas, duas abertas passam a Vanessa e datas pagas permanecem | ✅ |
| EDIT-01 AC3 | Atalho 100% e divisão exata | `frontend/src/components/commitments/TransferResponsibilityModal.test.tsx:21-23` — payload 100%, rateio 50/150 e diferença bloqueada; `backend/tests/integration/test_responsibility_transfer_preview.py:85-89` — linhas/colunas fecham exatamente | ✅ |
| EDIT-01 AC4 | Antecipação planejada aparece e acompanha abertas | `backend/tests/integration/test_responsibility_transfer_preview.py:131-133` — lista exata do plano; `test_responsibility_transfer_apply.py:198-203` — totais e estados planejados após transferência | ✅ |
| EDIT-01 AC5 | Pagamento/antecipação paga preservados | `backend/tests/integration/test_responsibility_transfer_apply.py:97-105` — responsáveis e `paid_at` históricos preservados | ✅ |
| EDIT-01 AC6 | Mudança entre prévia/confirmação conflita sem parcial | `backend/tests/integration/test_responsibility_transfer_apply.py:145-149,158-171` — 409 `version_conflict` e snapshots permanecem originais | ✅ |
| EDIT-01 AC7 | Transferência atômica atualiza leituras sem duplicar | `backend/tests/integration/test_responsibility_transfer_apply.py:111-134,198-204` — replay idempotente, meses reabertos, auditoria, total e filtros por pessoa | ✅ |
| EDIT-02 AC1 | Edição em modal do produto, sem diálogo nativo | `frontend/e2e/experience-v2.spec.ts:62-69` — dialog e prévia “Antes e depois”; `:72-86` — zero eventos de diálogo nativo | ✅ |
| EDIT-02 AC2 | Sem pagamentos permite todos os campos e cronograma | `backend/tests/integration/test_commitment_edit_preview.py:78-99` — lista completa de campos, comprador, valores e meses; `test_commitment_edit_apply.py:47-59` — persistência exata | ✅ |
| EDIT-02 AC3 | Com pagamento bloqueia recálculo e permite descrição/categoria | `backend/tests/integration/test_commitment_edit_preview.py:116-125` — allowed fields exatos e 409 para total; `test_commitment_edit_apply.py:102-110` — parcela paga intacta | ✅ |
| EDIT-02 AC4 | Prévia mostra antes/depois, ciclos e planos | `frontend/src/components/commitments/EditCommitmentModal.test.tsx:22` e `backend/tests/integration/test_commitment_edit_preview.py:148-154` — cronogramas, faturas e antecipações | ✅ |
| EDIT-02 AC5 | Descarte sujo exige confirmação interna | `frontend/src/components/commitments/EditCommitmentModal.test.tsx:20` — close não ocorre antes de “Descartar alterações” | ✅ |
| EDIT-02 AC6 | Erro preserva e destaca campos | `frontend/src/components/commitments/EditCommitmentModal.test.tsx:23-24` — valor mantido, `aria-invalid` e mensagem acionável | ✅ |
| EDIT-02 AC7 | Aplicação tudo-ou-nada e auditoria | `backend/tests/integration/test_commitment_edit_apply.py:60-75,147-165` — ids antigos removidos, ator/campos auditados e falha/hash inválido sem mudança | ✅ |
| MODAL-01 AC1 | Primitive e subcomponentes compartilhados | `frontend/src/components/modal/Modal.test.tsx:22-25,107-131` — header/body, erro focado, confirmação e guarda; `frontend/src/components/modal/index.tsx:44-83` — exports ModalHeader/Body/Footer/Close/FormError/ConfirmStep/Guard | ✅ |
| MODAL-01 AC2 | Foco, Tab, Escape e restauração | `frontend/src/components/modal/Modal.test.tsx:30-60,83-90` — foco inicial/ref, retorno, Escape e ciclo Tab/Shift+Tab | ✅ |
| MODAL-01 AC3 | Fundo modal e scroll bloqueado | `frontend/src/components/modal/Modal.test.tsx:23-25,74-76` — dialog modal aberto, body `overflow=hidden` e restauração; `index.tsx:27` usa `showModal()` nativo | ✅ |
| MODAL-01 AC4 | 360/390/768/1440 sem overflow | `frontend/e2e/modal-responsiveness.spec.ts:3-20` — caixa dentro da viewport, sem scroll horizontal e sem backdrop legado em quatro larguras | ✅ |
| MODAL-01 AC5 | Busy anunciado e ações duplicáveis desabilitadas | `frontend/src/components/modal/Modal.test.tsx:93-97`; `frontend/src/components/commitments/TransferResponsibilityModal.test.tsx:26` | ✅ |
| MODAL-01 AC6 | Confirmação destrutiva interna e específica | `frontend/src/components/modal/Modal.test.tsx:113-119`; `frontend/e2e/experience-v2.spec.ts:72-86` — impacto explícito e zero diálogo nativo | ✅ |
| FAMILY-01 AC1 | Bloco Minha família abre área responsiva | `frontend/src/layout/FamilyAndProfile.test.tsx:18-19`; `frontend/e2e/experience-v2.spec.ts:89-96` | ✅ |
| FAMILY-01 AC2 | Nome, código, owner, membros, convites e papéis | `backend/tests/integration/test_family.py:61-74,111-114`; `frontend/src/layout/FamilyAndProfile.test.tsx:24` | ✅ |
| FAMILY-01 AC3 | Backfill Douglas owner/Vanessa member preserva financeiro | `backend/tests/integration/test_schema.py:185-190` — papéis, cartão e snapshots exatos após upgrade | ✅ |
| FAMILY-01 AC4 | Member vê dados e não recebe ações owner | `backend/tests/integration/test_family.py:82-87`; `frontend/src/layout/FamilyAndProfile.test.tsx:26` | ✅ |
| FAMILY-01 AC5 | Owner renomeia 1–100, versionado | `backend/tests/integration/test_family.py:169-177,193-194` — resposta/auditoria exatas e limites 422 | ✅ |
| FAMILY-01 AC6 | Owner não remove a si | `backend/tests/integration/test_family.py:259-271` — member recebe 403 e rota de remoção do owner inexiste (404) | ✅ |
| FAMILY-01 AC7 | Família externa não é revelada/alterada | `backend/tests/integration/test_family.py:122-125`; `backend/tests/integration/test_schema.py:135-140` — resposta isolada e RLS bloqueia leitura/escrita estrangeira | ✅ |
| INVITE-01 AC1 | Token aleatório, hash-only, 7 dias e link configurável | `backend/tests/integration/test_family_invites.py:35-44` — 201, one-time, URL, SHA-256, segredo ausente e janela de 7 dias | ✅ |
| INVITE-01 AC2 | WhatsApp abre somente após ação com mensagem/link | `frontend/src/components/family/InviteFlow.test.tsx:14`; `frontend/e2e/experience-v2.spec.ts:99-108` | ✅ |
| INVITE-01 AC3 | Fallback copiar e Web Share | `frontend/src/components/family/InviteFlow.test.tsx:13,15` — payload do share e clipboard/status | ✅ |
| INVITE-01 AC4 | Localhost avisa; deploy usa configuração | `frontend/src/components/family/InviteFlow.test.tsx:16`; `backend/tests/unit/test_config.py:25-45` — localhost aceito e HTTP externo rejeitado/HTTPS aceito | ✅ |
| INVITE-01 AC5 | Conta existente/nova entra exatamente na família convidada | `backend/tests/integration/test_invite_auth.py:70-74,116-124`; `frontend/src/components/family/InviteFlow.test.tsx:23-24` | ✅ |
| INVITE-01 AC6 | Usado/revogado/expirado recusados de forma clara | `backend/tests/integration/test_invite_auth.py:179-180,196-197`; `frontend/src/components/family/InviteFlow.test.tsx:25` | ✅ |
| INVITE-01 AC7 | Consumo concorrente tem um vencedor | `backend/tests/integration/test_invite_auth.py:212-219` — status `[200,410]` e uma associação | ✅ |
| INVITE-01 AC8 | Revogar/renovar invalida anterior | `backend/tests/integration/test_family_invites.py:100-106,128-132,150-153` — revoke/audit, antigo revogado e conflito de versão | ✅ |
| PROFILE-01 AC1 | Nome/avatar abre perfil próprio | `frontend/src/layout/FamilyAndProfile.test.tsx:20`; `frontend/e2e/experience-v2.spec.ts:111-116` | ✅ |
| PROFILE-01 AC2 | Nome propaga sem trocar identidade | `backend/tests/integration/test_profile.py:37-46`; `frontend/src/layout/FamilyAndProfile.test.tsx:32-33` — `/me`, membros, topbar e seletor atualizados | ✅ |
| PROFILE-01 AC3 | Email somente leitura e explicado | `backend/tests/integration/test_profile.py:17-18,74-76`; `frontend/src/layout/FamilyAndProfile.test.tsx:31` | ✅ |
| PROFILE-01 AC4 | Só o próprio perfil pode ser alterado | `backend/tests/integration/test_profile.py:113-115` — tentativa sobre outro id 404 e Vanessa intacta | ✅ |
| AUTH-RESET-01 AC1 | Resposta pública igual para conta existente/inexistente | `backend/tests/integration/test_password_reset_request.py:70-72`; `frontend/e2e/password-recovery.spec.ts:3-14` | ✅ |
| AUTH-RESET-01 AC2 | Token aleatório hash-only, HTTPS e 15 min | `backend/tests/integration/test_password_reset_request.py:87-95` — hash, segredo ausente, TTL, status, idempotência e URL HTTPS | ✅ |
| AUTH-RESET-01 AC3 | Argon2, token usado e revogação atômica de sessões/tokens | `backend/tests/integration/test_password_reset_complete.py:160-176` — senha verificada, token used/revoked e todas sessões revogadas | ✅ |
| AUTH-RESET-01 AC4 | Usado/expirado/desconhecido normalizados | `backend/tests/integration/test_password_reset_complete.py:118-128,207-220` — 410 e corpo público igual sem alteração de senha | ✅ |
| AUTH-RESET-01 AC5 | Concorrência aceita exatamente uma redefinição | `backend/tests/integration/test_password_reset_complete.py:223-246` — respostas `[200,410]`, um hash vencedor e token marcado usado | ✅ |
| AUTH-RESET-01 AC6 | 3/email e 10/origem por hora sem enumeração | `backend/tests/integration/test_password_reset_request.py:141-167` — todas respostas genéricas, apenas 3/10 entregas; `:247-252` — concorrência limita a três tokens | ✅ |
| AUTH-RESET-01 AC7 | Falha do provedor é genérica e sem segredo | `backend/tests/integration/test_password_reset_request.py:180-185,196-213` — failed, `operation_id`, 202 genérico e email/token ausentes dos logs | ✅ |
| AUTH-RESET-01 AC8 | Senha 15–200, Unicode/espaços, diferente da atual | `backend/tests/unit/test_passwords.py:9-27,38-45`; `backend/tests/integration/test_password_reset_complete.py:184-199` | ✅ |
| AUTH-RESET-01 AC9 | Token sai da URL/histórico e referrer é bloqueado | `frontend/src/pages/PasswordRecovery.test.tsx:55-67`; `frontend/e2e/password-recovery.spec.ts:17-34` | ✅ |
| CARD-UX-01 AC1 | Proporção 85,60:53,98 e largura compacta | `frontend/src/components/cards/PaymentCard.test.tsx:12`; `frontend/e2e/experience-v2.spec.ts:135-149` | ✅ |
| CARD-UX-01 AC2 | Grade 1/4/12 responsiva e sem corte | `frontend/src/components/cards/PaymentCard.test.tsx:17-18`; `frontend/e2e/experience-v2.spec.ts:138-149` | ✅ |
| CARD-UX-01 AC3 | Apelido, instituição, titular, final, bandeira e datas com contraste | `frontend/src/components/cards/PaymentCard.test.tsx:11,13`; `frontend/src/domain/cardInstitutions.test.ts:15-19` — conteúdo e razões WCAG mínimas | ✅ |
| CARD-UX-01 AC4 | Ações discretas acessíveis | `frontend/src/components/cards/PaymentCard.test.tsx:16` — botões nomeados e callbacks separados; `:12` mantém altura por aspect-ratio | ✅ |
| CARD-CATALOG-01 AC1 | Catálogo pesquisável e Outra | `backend/tests/integration/test_cards.py:55-60`; `frontend/src/components/cards/CardFormModal.test.tsx:17-21` | ✅ |
| CARD-CATALOG-01 AC2 | Outra exige/persiste nome custom e tema genérico | `frontend/src/components/cards/CardFormModal.test.tsx:23-24`; `backend/tests/integration/test_cards.py:88-90` | ✅ |
| CARD-CATALOG-01 AC3 | Bandeiras opcionais aprovadas | `backend/tests/unit/test_card_catalog.py:38`; `frontend/src/components/cards/CardFormModal.test.tsx:25` | ✅ |
| CARD-CATALOG-01 AC4 | Tema estável por institution_key | `frontend/src/domain/cardInstitutions.test.ts:8-11`; `frontend/src/components/cards/PaymentCard.test.tsx:13-14` | ✅ |
| CARD-CATALOG-01 AC5 | Mudança atualiza prévia antes de salvar | `frontend/src/components/cards/CardFormModal.test.tsx:22` — Neon altera cor e rótulo na prévia | ✅ |
| CARD-CATALOG-01 AC6 | Sem hotlink/scraping/logo copiado | `frontend/src/domain/cardInstitutions.test.ts:23-24` — catálogo não contém URL/logo e cores são tokens hex locais | ✅ |
| CARD-CATALOG-01 AC7 | Temas mantêm contraste/foco | `frontend/src/domain/cardInstitutions.test.ts:15-19` — texto ≥4,5:1 e accent/focus ≥3:1 para toda instituição | ✅ |
| CARD-CATALOG-01 AC8 | Apenas apelido/últimos 4; PAN/CVV rejeitados | `backend/tests/integration/test_cards.py:107-129` — campos sensíveis 422 e `last_four` exatamente quatro dígitos; `frontend/src/components/cards/CardFormModal.test.tsx:26` | ✅ |

**Status:** 60/60 critérios ancorados, 0 gap de precisão impeditivo.

## Casos de borda transversais

| Caso | Evidência | Resultado |
| --- | --- | --- |
| Identidade histórica de membro | Snapshots têm FK para membership e migração preserva Douglas/Vanessa (`test_schema.py:185-190`); remoção está fora de escopo | ✅ |
| Spam/revogação de convites | `test_family_invites.py:85-88,100-106` — limite e revoke | ✅ |
| Config de produção inválida | `backend/tests/unit/test_config.py:25-45` e `/ready`; HTTP externo/Resend sem chave falham | ✅ |
| Email indisponível não derruba o produto | `test_password_reset_request.py:180-213`; smoke financeiro com provider memory | ✅ |
| Ciclo conferido afetado | `test_commitment_edit_preview.py:148-154` e transfer apply reabre meses | ✅ |
| Modal empilhado/dirty guard | `Modal.test.tsx:122-131` substitui conteúdo por confirmação controlada | ✅ |
| Instituição custom com HTML/URL | React renderiza como texto; backend limita 100 caracteres; E2E não cria campo sensível | ✅ |

## Gate de build/sistema

### Comandos independentes

1. Migração em PostgreSQL 16 descartável em `127.0.0.1:65436`; aplicação de testes em `127.0.0.1:8001`, `EMAIL_PROVIDER=memory`.
2. `./scripts/check-backend.sh`.
3. `cd backend && uv run pytest -q && uv run alembic check`.
4. `cd frontend && npm run test:unit && npm run build`.
5. Playwright com Vite isolado em `5174` e `API_TARGET=http://127.0.0.1:8001`: `npm run test:e2e -- --config=playwright.verifier.config.ts`; a configuração temporária foi removida.
6. `docker compose --env-file .env.compose-test -p expense-flow-validation config --quiet`, build/up, `python3 deploy/tests/smoke.py`, seguido de `down -v --remove-orphans`.

### Resultados

| Gate | Resultado |
| --- | --- |
| Ruff + compile/import | PASS |
| Backend | 263 passed, 0 failed, 0 skipped; 2 warnings de depreciação Starlette/httpx/anyio |
| Alembic | “No new upgrade operations detected” |
| Frontend unitário | 20 arquivos, 169 passed, 0 failed, 0 skipped |
| Build | TypeScript/Vite PASS; 1.772 módulos |
| E2E | 42 passed, 0 failed, 0 skipped, quatro viewports |
| Compose/deploy smoke | PASS: portas privadas, readiness, login, runtime sem bypass de RLS, persistência e backup/restore |

O primeiro ensaio do backend com `expense_runtime` direto nas fixtures administrativas gerou 23 falhas de setup/RLS e foi descartado: a suíte cria e inspeciona fixtures como owner e troca para `expense_app` dentro dos próprios testes. Um ensaio E2E inicial também foi descartado porque `reuseExistingServer:true` encontrou um Vite preexistente em `5173`; a repetição isolada em `5174`, com `APP_ORIGIN` correspondente, passou 42/42. Esses eventos são riscos de runbook, não falhas do produto.

### Integridade da suíte

| Métrica | Base `3b2f68e` | Atual `756bd73` | Delta |
| --- | ---: | ---: | ---: |
| Backend | 76 coletados | 263 passed | +187 |
| Frontend unitário | 15 passed | 169 passed | +154 |
| E2E | 26 listados | 42 passed | +16 |
| Total | 117 | 474 | +357 |

- `git diff --name-status 3b2f68e..HEAD`: nenhum arquivo de teste removido.
- `git diff --check 3b2f68e..HEAD`: limpo.
- Busca por `pytest.skip`, `test.skip`, `describe.skip`, `it.skip` e `.only(`: zero.
- Busca por `window.(alert|prompt|confirm)` e `.dialog-backdrop` direto em `frontend/src`: zero.
- Busca em arquivos rastreados por padrão de chave Resend/token bruto: zero ocorrência relevante.

## Discrimination sensor P0

Cada mutação foi aplicada em worktree destacado de `756bd73`, executou o teste indicado e o worktree foi removido. A mutação RLS usou banco descartável próprio. Nenhuma alteração chegou ao working tree real.

| # | Área | Mutação semântica | Teste discriminante / falha observada | Resultado |
| --- | --- | --- | --- | --- |
| M1 | Reset/auth | Inverter `expires_at <= now()` | `test_invalid_token_states_are_normalized[expired]`: esperava 410, recebeu 200 | ✅ Morta |
| M2 | Convite | Não marcar `used_at` após aceite | `test_token_is_one_time...`: inspeção esperava 410, recebeu 200 | ✅ Morta |
| M3 | Pagamento/snapshot | Transferir parcelas pagas em vez das abertas | `test_transfer_changes_two_open...`: responsáveis históricos divergiram | ✅ Morta |
| M4 | Idempotência | Gerar nova chave a cada retry do cliente | `client.test.ts`: headers tinham UUIDs diferentes | ✅ Morta |
| M5 | Autorização familiar | Permitir papel member em `require_owner` | `test_require_owner...`: member recebeu permissão | ✅ Morta |
| M6 | RLS | Política de `family_invites` alterada para `USING/WITH CHECK true` | `test_family_invite_rls...`: retornou `ia` e `ib` antes do contexto | ✅ Morta |
| M7 | Modal | Remover foco inicial | `Modal.test.tsx`: `document.activeElement` permaneceu no body | ✅ Morta |
| M8 | Token URL | Não executar `history.replaceState` no reset | `PasswordRecovery.test.tsx`: URL ainda continha `raw-secret` antes da validação | ✅ Morta |
| M9 | Cartão | Aceitar qualquer quatro caracteres no final | `CardFormModal.test.tsx`: `12x4` foi submetido sem alerta | ✅ Morta |

**Resultado:** 9/9 mortas, 0 sobreviventes contados — PASS ✅.

Controle exploratório adicional: remover apenas o `FOR UPDATE` da linha do convite não mudou o resultado porque `family_context(..., lock=True)` já serializa a família inteira. O teste concorrente permaneceu verde e a alteração não foi contada como mutação comportamental; isso evidencia redundância defensiva, não falha de discriminação.

## Qualidade de código

| Princípio | Estado | Evidência |
| --- | --- | --- |
| Escopo mínimo / sem feature extra | ✅ | Diff corresponde aos nove requisitos e prontidão solicitada |
| Mudanças cirúrgicas | ✅ | 36 commits por tarefa + correções explícitas; nenhum teste removido |
| Padrões existentes | ✅ | FastAPI/SQLAlchemy/UoW, React/Vitest e Playwright mantidos |
| Integridade de testes | ✅ | +357 testes, 0 skip/only, 9/9 mutantes mortos |
| Outcome ancorado na spec | ✅ | 60/60 ACs acima têm assertiva observável |
| Cobertura por camada | ✅ | Funções puras, PostgreSQL/RLS/concorrência, componentes e E2E |
| Testes reivindicáveis | ✅ | Arquivos novos nomeiam EDIT/MODAL/FAMILY/INVITE/PROFILE/AUTH-RESET/CARD ou Done-when da tarefa |
| Diretrizes do projeto | ✅ | `README.md`, `backend/pyproject.toml`, `frontend/package.json`, `frontend/playwright.config.ts`; defaults TLC onde não havia regra adicional |

Observações não impeditivas:

- Componentes TSX permanecem densos em linhas longas e usam `any` em áreas antigas; não houve defeito funcional demonstrado.
- O Playwright principal pode reutilizar um servidor `5173` de outro processo e mascarar a configuração do gate; CI deve reservar a porta ou usar configuração que não reutilize servidor.
- Os warnings de depreciação Starlette/TestClient e anyio devem ser tratados numa atualização controlada.
- A inspeção do Graphify estava desatualizada para esta feature (o grafo ainda apontava principalmente para `controle-familiar`); a evidência final veio do diff e dos testes atuais.

## UAT e limites da validação

Não houve UAT humano interativo nesta rodada. A validação automatizada cobriu os fluxos visuais em Chromium nas quatro larguras aprovadas e o smoke Compose, mas não substitui revisão visual humana de marca nem deploy real HTTPS. Nenhum email real foi enviado e nenhuma licença de marca foi afirmada; os temas são próprios, sem logos/hotlinks.

O backup do usuário `backups/before-gestao-experiencia-v2-20260912-144607.dump` foi somente verificado por existência/tamanho (2.242.617 bytes) e não foi lido, restaurado, alterado ou removido. Todos os bancos, containers, volumes, APIs e worktrees efêmeros da verificação foram removidos.

## Rastreabilidade final

| Requisito | Estado anterior | Estado verificado |
| --- | --- | --- |
| EDIT-01 | implementação concluída | ✅ Verified |
| EDIT-02 | implementação concluída | ✅ Verified |
| MODAL-01 | implementação concluída | ✅ Verified |
| FAMILY-01 | implementação concluída | ✅ Verified |
| INVITE-01 | implementação concluída | ✅ Verified |
| PROFILE-01 | implementação concluída | ✅ Verified |
| AUTH-RESET-01 | implementação concluída | ✅ Verified |
| CARD-UX-01 | implementação concluída | ✅ Verified |
| CARD-CATALOG-01 | implementação concluída | ✅ Verified |

## Resumo

**Overall:** ✅ Ready no escopo especificado. Não há fix task funcional nem lesson nova: a rodada terminou limpa, sem AC descoberto, spec-precision gap ou mutante sobrevivente.
