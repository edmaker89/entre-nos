# Controle familiar — tarefas

## Execution Protocol (MANDATORY -- do not skip)

Executar com a skill tlc-spec-driven e suas regras: testes por critérios de aceite, gate antes de concluir, commit atômico por tarefa e Verifier independente no final. Se a skill estiver indisponível, parar e informar. Nenhuma tarefa implementada.

Design: design.md. Status: In Progress — plano, ferramentas e execução no agente principal aprovados. Stack e autenticação já aprovadas; não solicitar novamente.

## Test Coverage Matrix

Origem: inspeção da pasta em 2026-09-10 encontrou somente .specs; nenhuma diretriz de testes, manifesto ou teste existente. Padrões fortes da skill aplicados à spec. Comandos abaixo são PROPOSTOS para criar no bootstrap, não descobertos nem executados. Confirmar estratégia com o usuário por se tratar de projeto novo.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| domain | unit | Cada AC e fronteira do domínio, resultados exatos da spec | backend/tests/unit/test_*.py | cd backend && python -m pytest tests/unit |
| API/persistência | integration | Caminho válido, cada erro especificado, isolamento, rollback e concorrência em PostgreSQL real migrado | backend/tests/integration/test_*.py | cd backend && python -m pytest tests/integration |
| UI/cliente HTTP | unit + e2e | Interação, erros e ACs visuais/fluxos completos | frontend/src/**/*.test.ts*; frontend/e2e/*.spec.ts | cd frontend && npm run test:unit && npm run test:e2e |
| config/schema | none | Importação, lint e build; migração com integração na própria tarefa que a cria | — | gate Build aplicável |
| deploy | integration | Subida local, healthchecks, volume, migração e restauração descartável | deploy/tests/ | comando de smoke a definir no bootstrap |

## Gate Check Commands

Propostos, pendentes de materialização nos manifestos do projeto. Nunca reportar como executados antes disso.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Domínio | cd backend && python -m pytest tests/unit |
| Full | API ou UI | Todos os testes unitários e de integração existentes; UI acrescenta npm run test:unit e npm run test:e2e |
| Build | Configuração e fim de fase | Ruff, importação backend, gates existentes, build TypeScript/Vite quando disponível e docker compose config quando disponível |

A ausência temporária de uma camada ainda não criada não permite ignorar testes da tarefa atual. Full/Build crescem com os componentes existentes. Os comandos exatos serão registrados assim que os manifestos forem criados.

## Execution Plan

Quatro fases, sete tarefas por fase, execução sequencial. Dependência do predecessor indica ordem de execução e disponibilidade cumulativa dos componentes anteriores.

### Fase 1: Fundação e acesso

T1 → T2 → T3 → T4 → T5 → T6 → T7

### Fase 2: Compras e cronogramas

T8 → T9 → T10 → T11 → T12 → T13 → T14

### Fase 3: Pagamentos e projeção

T15 → T16 → T17 → T18 → T19 → T20 → T21

### Fase 4: Interface e implantação

T22 → T23 → T24 → T25 → T26 → T27 → T28

Fronteiras: T7 → T8; T14 → T15; T21 → T22.

## Task Breakdown

### T1: Base executável do backend

- **What**: Entregar o componente base executável do backend com verificação co-localizada.
- **Where**: `backend/pyproject.toml; backend/app/main.py` e testes correspondentes conforme matriz.
- **Depends on**: Nenhuma.
- **Reuses**: Nenhum código existente.
- **Requirement**: DATA-01.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: API inicia; contrato de erro e dependências declarados; lint/importação passam. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Build passa.
- **Tests**: none. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Build.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — gate de importação/compilação/lint passou; sem testes de regra nesta tarefa.

### T2: Modelo relacional financeiro

- **What**: Entregar o componente modelo relacional financeiro com verificação co-localizada.
- **Where**: `backend/app/db/models.py` e testes correspondentes conforme matriz.
- **Depends on**: T1.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: FAM-01,CARD-01,BUY-01,SPLIT-01,BILL-01,SETTLE-01,ADV-01,MIG-01,DATA-01.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Modelos e constraints representam as entidades do design, valores em centavos e identidade original das parcelas. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Build passa.
- **Tests**: none. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Build.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — lint/compilação/importação passaram; 17 tabelas carregadas.

### T3: Migração inicial Alembic

- **What**: Entregar o componente migração inicial alembic com verificação co-localizada.
- **Where**: `backend/alembic/` e testes correspondentes conforme matriz.
- **Depends on**: T2.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: FAM-01,DATA-01.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Upgrade de banco vazio e alembic check passam; constraints e RLS negam relações/acesso de outra família. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — Alembic upgrade/check e 2 testes PostgreSQL passaram.

### T4: Unidade transacional por família

- **What**: Entregar o componente unidade transacional por família com verificação co-localizada.
- **Where**: `backend/app/db/unit_of_work.py` e testes correspondentes conforme matriz.
- **Depends on**: T3.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: DATA-01 AC02–05; BUY-01 AC06; ADV-01 AC09.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Rollback não deixa gravação parcial; repetição não duplica; payload diferente conflita; concorrência preserva primeira gravação; log sem dados financeiros. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 5 testes passaram; rollback, repetição, concorrência e log verificados.

### T5: Sessões autenticadas

- **What**: Entregar o componente sessões autenticadas com verificação co-localizada.
- **Where**: `backend/app/api/auth.py` e testes correspondentes conforme matriz.
- **Depends on**: T4.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: FAM-01 AC01–03; AUTH-01.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Login/logout/me/CSRF funcionam; cookie protegido; expiração e revogação negam acesso; 11ª tentativa na janela retorna 429; mutação sem CSRF é negada. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 10 testes passaram; cookies, CSRF, expiração, logout e rate limit.

### T6: Provisionamento administrativo

- **What**: Entregar o componente provisionamento administrativo com verificação co-localizada.
- **Where**: `backend/app/cli.py` e testes correspondentes conforme matriz.
- **Depends on**: T5.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: FAM-01; AUTH-01.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Criar família e dois usuários sem senha no log; redefinir senha revoga sessões; repetir cadastro não duplica email. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 11 testes passaram; provisionamento e redefinição com revogação.

### T7: Cálculo de ciclos

- **What**: Entregar o componente cálculo de ciclos com verificação co-localizada.
- **Where**: `backend/app/domain/cycles.py` e testes correspondentes conforme matriz.
- **Depends on**: T6.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: CARD-01 AC01–03; BUY-01 AC01–03.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: 25/09 fecha outubro, compra 26/09 vai a novembro; dia 31 em fevereiro/2027 vira 28; fronteira marcada para conferir. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Build passa.
- **Tests**: unit. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Build.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 16 testes passaram; fechamento e ano/meses curtos; Alembic check limpo.

### T8: Distribuição de centavos

- **What**: Entregar o componente distribuição de centavos com verificação co-localizada.
- **Where**: `backend/app/domain/money.py` e testes correspondentes conforme matriz.
- **Depends on**: T7.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: BUY-01 AC04; SPLIT-01 AC01–04; ADV-01 AC06.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: 10000/3 resulta 3334,3333,3333; divisão de 3333 resulta 1667,1666; rateio de 19999 em parcelas iguais resulta 10000,9999; limites rejeitados. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Quick passa.
- **Tests**: unit. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Quick.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 13 testes unitários passaram; rateio e limites exatos.

### T9: Cadastro de cartões

- **What**: Entregar o componente cadastro de cartões com verificação co-localizada.
- **Where**: `backend/app/api/cards.py` e testes correspondentes conforme matriz.
- **Depends on**: T8.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: CARD-01; FAM-01 AC02.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Listar/criar/editar cartão válido; negar campos/dias inválidos e titular externo; edição não reescreve ciclos existentes. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 25 testes passaram; cadastro, edição, repetição e validação de cartão.

### T10: Prévia e cadastro de compras

- **What**: Entregar o componente prévia e cadastro de compras com verificação co-localizada.
- **Where**: `backend/app/api/commitments.py` e testes correspondentes conforme matriz.
- **Depends on**: T9.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: BUY-01 AC01–06; SPLIT-01 AC01–04; DATA-01 AC01.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Prévia e gravação produzem competências e valores exatos; salvar compra/divisão/parcelas é atômico; erros não gravam. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 29 testes passaram; prévia e compra persistida nos ciclos previstos.

### T11: Migração manual de compromissos

- **What**: Entregar o componente migração manual de compromissos com verificação co-localizada.
- **Where**: `backend/app/api/imports.py` e testes correspondentes conforme matriz.
- **Depends on**: T10.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: MIG-01 AC01–03; BILL-01 AC03.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: 10/12 gera apenas 3 parcelas total 13053; contrato 48 com intervalo 10–44 gera 35 obrigações e nenhum histórico fictício; intervalos inválidos negados. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 30 testes passaram; migração parcial preserva total original.

### T12: Edição e deslocamento de compra

- **What**: Entregar o componente edição e deslocamento de compra com verificação co-localizada.
- **Where**: `backend/app/api/commitment_changes.py` e testes correspondentes conforme matriz.
- **Depends on**: T11.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: SETTLE-01 AC01,AC03,AC06; ADV-01 AC10.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Prévia desloca outubro/novembro/dezembro a novembro/dezembro/janeiro; pagos e antecipação ativa bloqueiam; exclusão lógica atômica com confirmação. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 32 testes passaram; deslocamento, exclusão e bloqueios de pagos/antecipações.

### T13: Conferência e fechamento de ciclo

- **What**: Entregar o componente conferência e fechamento de ciclo com verificação co-localizada.
- **Where**: `backend/app/api/cycles.py` e testes correspondentes conforme matriz.
- **Depends on**: T12.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: CARD-01 AC04; SETTLE-01 AC05; ADV-01 AC10.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Prévia e confirmação remanejam somente elegíveis; datas inválidas rejeitadas; conferir limpa avisos e novo item invalida conferência. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 33 testes passaram; fechamento efetivo, remanejamento e conferência.

### T14: Regras e ocorrências recorrentes

- **What**: Entregar o componente regras e ocorrências recorrentes com verificação co-localizada.
- **Where**: `backend/app/api/recurrences.py` e testes correspondentes conforme matriz.
- **Depends on**: T13.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: BILL-01 AC01–04.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Aluguel 160000 uma vez por mês; energia estimada 36000 atualizada sem reescrever pago; encerramento preserva anteriores e bloqueia pagos futuros. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Build passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Build.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 34 testes passaram; recorrências idempotentes e estimativas; Alembic check limpo.

### T15: Pagamento e reabertura

- **What**: Entregar o componente pagamento e reabertura com verificação co-localizada.
- **Where**: `backend/app/api/payments.py` e testes correspondentes conforme matriz.
- **Depends on**: T14.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: SETTLE-01 AC02–04; ADV-01 AC02,AC07; MONTH-01 AC08.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Pagar fatura 30000 liquida parcelas sem duplicar gasto; reabertura atômica; atraso mantém competência; reabertura invalida mês quitado. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 35 testes passaram; fatura liquidada sem dupla contagem e reabertura.

### T16: Planejamento de antecipação

- **What**: Entregar o componente planejamento de antecipação com verificação co-localizada.
- **Where**: `backend/app/api/advances.py` e testes correspondentes conforme matriz.
- **Depends on**: T15.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: ADV-01 AC01,AC04–06,AC08–10.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: 44/48 por 108400 sai da competência original e entra em outubro; regular+antecipação=300300; cartão aceita desconto zero; inválidos e disputa negados. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 37 testes passaram; antecipação do carro e cartão preserva identidade e totais.

### T17: Ciclo de vida da antecipação

- **What**: Entregar o componente ciclo de vida da antecipação com verificação co-localizada.
- **Where**: `backend/app/api/advance_changes.py` e testes correspondentes conforme matriz.
- **Depends on**: T16.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: ADV-01 AC02–03,AC05,AC07–09.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Planejar não reduz pendentes; pagar reduz 1; último aberto 44 vira 43 sem renumerar; cancelar restaura valores/datas; cartão quita pela fatura. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 38 testes passaram; pagamento reduz pendentes e cancelamento restaura cronograma.

### T18: Seleção de competência inicial

- **What**: Entregar o componente seleção de competência inicial com verificação co-localizada.
- **Where**: `backend/app/domain/month_selection.py` e testes correspondentes conforme matriz.
- **Depends on**: T17.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: MONTH-01 AC01,AC08.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Dia 09 seleciona corrente; dia 10 próximo; quitado antecipa; virada de mês reinicia; timezone São Paulo. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Quick passa.
- **Tests**: unit. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Quick.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 14 testes unitários passaram; regra do dia 10 e timezone.

### T19: Consulta mensal e projeção

- **What**: Entregar o componente consulta mensal e projeção com verificação co-localizada.
- **Where**: `backend/app/api/months.py` e testes correspondentes conforme matriz.
- **Depends on**: T18.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: MONTH-01 AC02–03,AC05–07; ADV-01 AC01–04.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Previsto 15000, pago 10000, restante 5000; filtro por responsável exato; vazio zero; projeção de 12 meses identifica estimativas sem duplicação. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 40 testes passaram; totais mensais, filtros e previsão de 12 meses.

### T20: Sinalização de mês quitado

- **What**: Entregar o componente sinalização de mês quitado com verificação co-localizada.
- **Where**: `backend/app/api/month_closure.py` e testes correspondentes conforme matriz.
- **Depends on**: T19.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: MONTH-01 AC08.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Pendências impedem sinal e não são pagas automaticamente; vazio exige ação; nova obrigação/reabertura invalida sinal. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 41 testes passaram; mês quitado exige pagamentos e invalida com pendências.

### T21: Base do frontend e cliente HTTP

- **What**: Entregar o componente base do frontend e cliente http com verificação co-localizada.
- **Where**: `frontend/src/api/; frontend/package.json` e testes correspondentes conforme matriz.
- **Depends on**: T20.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: DATA-01 AC04; FAM-01.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Frontend compila; cliente envia cookie/CSRF; repetição mantém chave; erro não descarta formulário e sessão expirada exige login. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Build passa.
- **Tests**: unit + e2e. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Build.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 2 testes frontend e 1 navegador passaram; build concluído; npm audit sem vulnerabilidades.

### T22: Tela de login

- **What**: Entregar o componente tela de login com verificação co-localizada.
- **Where**: `frontend/src/pages/Login.tsx` e testes correspondentes conforme matriz.
- **Depends on**: T21.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: FAM-01; AUTH-01.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Login válido abre resumo; inválido/limite mostra erro; logout encerra acesso; credencial não é gravada em localStorage. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: unit + e2e. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 3 testes unitários frontend e 2 E2E passaram; build concluído.

### T23: Painel mensal responsivo

- **What**: Entregar o componente painel mensal responsivo com verificação co-localizada.
- **Where**: `frontend/src/pages/Overview.tsx` e testes correspondentes conforme matriz.
- **Depends on**: T22.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: MONTH-01 AC01–08.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Mês destacado e seleção estável; totais/pendências/filtros corretos; larguras 360/390/768/1440 sem overflow; alvos de toque 44px. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: unit + e2e. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 4 testes unitários frontend e 6 E2E passaram; quatro larguras sem overflow após correção.

### T24: Formulário de compra

- **What**: Entregar o componente formulário de compra com verificação co-localizada.
- **Where**: `frontend/src/components/CommitmentForm.tsx` e testes correspondentes conforme matriz.
- **Depends on**: T23.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: BUY-01 AC05; SPLIT-01; DATA-01 AC01,AC04.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Campos e rateio validados; prévia antes de salvar; responsável independente do titular; erro preserva valores; fluxo móvel completo. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: unit + e2e. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 5 testes unitários frontend e 7 E2E passaram; compra em viewport móvel salva após prévia.

### T25: Tela de cartões e faturas

- **What**: Entregar o componente tela de cartões e faturas com verificação co-localizada.
- **Where**: `frontend/src/pages/Cards.tsx` e testes correspondentes conforme matriz.
- **Depends on**: T24.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: CARD-01; SETTLE-01 AC02–05.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Cadastro/cartão, prévia de fechamento, conferência, pagamento e reabertura funcionam com erros e bloqueios visíveis. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: unit + e2e. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 6 testes unitários frontend e 8 E2E passaram; cadastro de cartão e consulta de faturas.

### T26: Tela de contrato e antecipações

- **What**: Entregar o componente tela de contrato e antecipações com verificação co-localizada.
- **Where**: `frontend/src/pages/Commitment.tsx` e testes correspondentes conforme matriz.
- **Depends on**: T25.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: ADV-01 AC01–10; SETTLE-01 AC01,AC03,AC06.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Detalhes preservam identidade; selecionar antecipação e conferir desconto; pagar/reabrir/cancelar refletem estados corretos e bloqueios. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: unit + e2e. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 7 testes unitários frontend; 8 E2E passaram e teste de antecipação passou após recarregar fixture inserida por API; asserções preservadas.

### T27: Tela de recorrências e migração

- **What**: Entregar o componente tela de recorrências e migração com verificação co-localizada.
- **Where**: `frontend/src/pages/Planning.tsx` e testes correspondentes conforme matriz.
- **Depends on**: T26.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: BILL-01; MIG-01; MONTH-01 AC06.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Cadastrar/encerrar recorrência e importar intervalo com prévia; projeção mostra parcelas finais e estimativas; erros acessíveis. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Full passa.
- **Tests**: unit + e2e. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Full.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — 8 testes unitários frontend e 10 E2E passaram; importação e projeção completas.

### T28: Implantação Compose

- **What**: Entregar o componente implantação compose com verificação co-localizada.
- **Where**: `compose.yaml; deploy/; README.md` e testes correspondentes conforme matriz.
- **Depends on**: T27.
- **Reuses**: Base e contratos dos componentes anteriores; evitar regras duplicadas.
- **Requirement**: AD-002–004; FAM-01 AC03.
- **Tools**: terminal, apply_patch e navegador para UI; skill tlc-spec-driven. Ferramentas adicionais somente conforme necessidade técnica.
- **Done when**: Compose sobe web/api/db; migração pontual funciona; somente web publica portas; healthchecks e persistência verificados; procedimento de backup/restauração testado em ambiente descartável. Todos os ACs citados têm evidência de asserção em arquivo:linha; gate Build passa.
- **Tests**: integration. Contagem exata será registrada antes de implementar e comparada após o gate, sem remoção/skip para passar.
- **Gate**: Build.
- **Commit**: um commit convencional do componente e seus testes após gate e revisão de adequação.
- **Status**: Complete — Compose build/up passaram; smoke validou portas privadas, login, role restrita, persistência e restauração real; 41 testes backend e gates frontend da T27.

## Task Granularity Check

| Task | Scope | Status |
| --- | --- | --- |
| T1 | Um componente: Base executável do backend; testes no mesmo commit | OK |
| T2 | Um componente: Modelo relacional financeiro; testes no mesmo commit | OK |
| T3 | Um componente: Migração inicial Alembic; testes no mesmo commit | OK |
| T4 | Um componente: Unidade transacional por família; testes no mesmo commit | OK |
| T5 | Um componente: Sessões autenticadas; testes no mesmo commit | OK |
| T6 | Um componente: Provisionamento administrativo; testes no mesmo commit | OK |
| T7 | Um componente: Cálculo de ciclos; testes no mesmo commit | OK |
| T8 | Um componente: Distribuição de centavos; testes no mesmo commit | OK |
| T9 | Um componente: Cadastro de cartões; testes no mesmo commit | OK |
| T10 | Um componente: Prévia e cadastro de compras; testes no mesmo commit | OK |
| T11 | Um componente: Migração manual de compromissos; testes no mesmo commit | OK |
| T12 | Um componente: Edição e deslocamento de compra; testes no mesmo commit | OK |
| T13 | Um componente: Conferência e fechamento de ciclo; testes no mesmo commit | OK |
| T14 | Um componente: Regras e ocorrências recorrentes; testes no mesmo commit | OK |
| T15 | Um componente: Pagamento e reabertura; testes no mesmo commit | OK |
| T16 | Um componente: Planejamento de antecipação; testes no mesmo commit | OK |
| T17 | Um componente: Ciclo de vida da antecipação; testes no mesmo commit | OK |
| T18 | Um componente: Seleção de competência inicial; testes no mesmo commit | OK |
| T19 | Um componente: Consulta mensal e projeção; testes no mesmo commit | OK |
| T20 | Um componente: Sinalização de mês quitado; testes no mesmo commit | OK |
| T21 | Um componente: Base do frontend e cliente HTTP; testes no mesmo commit | OK |
| T22 | Um componente: Tela de login; testes no mesmo commit | OK |
| T23 | Um componente: Painel mensal responsivo; testes no mesmo commit | OK |
| T24 | Um componente: Formulário de compra; testes no mesmo commit | OK |
| T25 | Um componente: Tela de cartões e faturas; testes no mesmo commit | OK |
| T26 | Um componente: Tela de contrato e antecipações; testes no mesmo commit | OK |
| T27 | Um componente: Tela de recorrências e migração; testes no mesmo commit | OK |
| T28 | Um componente: Implantação Compose; testes no mesmo commit | OK |

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | Nenhuma | Nenhuma | Match |
| T2 | T1 | T1 | Match |
| T3 | T2 | T2 | Match |
| T4 | T3 | T3 | Match |
| T5 | T4 | T4 | Match |
| T6 | T5 | T5 | Match |
| T7 | T6 | T6 | Match |
| T8 | T7 | T7 | Match |
| T9 | T8 | T8 | Match |
| T10 | T9 | T9 | Match |
| T11 | T10 | T10 | Match |
| T12 | T11 | T11 | Match |
| T13 | T12 | T12 | Match |
| T14 | T13 | T13 | Match |
| T15 | T14 | T14 | Match |
| T16 | T15 | T15 | Match |
| T17 | T16 | T16 | Match |
| T18 | T17 | T17 | Match |
| T19 | T18 | T18 | Match |
| T20 | T19 | T19 | Match |
| T21 | T20 | T20 | Match |
| T22 | T21 | T21 | Match |
| T23 | T22 | T22 | Match |
| T24 | T23 | T23 | Match |
| T25 | T24 | T24 | Match |
| T26 | T25 | T25 | Match |
| T27 | T26 | T26 | Match |
| T28 | T27 | T27 | Match |

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1 | config | none | none | OK |
| T2 | schema | none | none | OK |
| T3 | integration | integration | integration | OK |
| T4 | integration | integration | integration | OK |
| T5 | integration | integration | integration | OK |
| T6 | integration | integration | integration | OK |
| T7 | unit | unit | unit | OK |
| T8 | unit | unit | unit | OK |
| T9 | integration | integration | integration | OK |
| T10 | integration | integration | integration | OK |
| T11 | integration | integration | integration | OK |
| T12 | integration | integration | integration | OK |
| T13 | integration | integration | integration | OK |
| T14 | integration | integration | integration | OK |
| T15 | integration | integration | integration | OK |
| T16 | integration | integration | integration | OK |
| T17 | integration | integration | integration | OK |
| T18 | unit | unit | unit | OK |
| T19 | integration | integration | integration | OK |
| T20 | integration | integration | integration | OK |
| T21 | ui | unit + e2e | unit + e2e | OK |
| T22 | ui | unit + e2e | unit + e2e | OK |
| T23 | ui | unit + e2e | unit + e2e | OK |
| T24 | ui | unit + e2e | unit + e2e | OK |
| T25 | ui | unit + e2e | unit + e2e | OK |
| T26 | ui | unit + e2e | unit + e2e | OK |
| T27 | ui | unit + e2e | unit + e2e | OK |
| T28 | deploy | integration | integration | OK |

## Fechamento

Após T28, Verifier independente obrigatório: ler spec, conferir evidências por AC, executar gates e mutações em cópia descartável, registrar validation.md. Falhas geram correções com novos commits; máximo de três ciclos antes de escalar. Nenhuma cobertura foi verificada ainda.

## Estratégia de execução a confirmar

28 tarefas em quatro lotes de sete. Oferta da skill: delegar lotes sequenciais a subagentes, ou executar no agente principal; nenhum worker foi iniciado. O Verifier final é obrigatório independentemente dessa escolha.

Ferramentas propostas para todas as tarefas: terminal/edição local; navegador/Playwright na UI; tlc-spec-driven para condução. Testes propostos: pytest (unitários e integração PostgreSQL), Vitest e Playwright (frontend). Não há comandos legados a preservar.

## Correções da verificação independente

### T29: Preservar a referência temporal de estimativas
- **Requirement**: BILL-01 — último valor conhecido antes da competência.
- **Files**: recurrences.py, test_recurrences.py, tasks.md, execution.md.
- **Done when**: confirmar novembro em 380 e corrigir outubro para 370 mantém dezembro/janeiro em 380, estimados.
- **Gate**: backend full + lint.
- **Status**: Complete — 42 backend tests passed; lint passed.

### T30: Preservar idempotência em tentativas de gravação na interface
- **Requirement**: DATA AC04.
- **Done when**: resposta perdida mantém a mesma chave para a mesma operação; sucesso encerra a tentativa.
- **Status**: Complete — 9 frontend unit tests and production build passed.

### T31: Completar navegação móvel e informações de planejamento
- **Requirement**: MONTH AC01/06/07, ADV AC01, responsividade.
- **Done when**: mês persiste na navegação, logout acessível no celular, detalhes mostram desconto/original, projeção mostra parcelas finais.
- **Status**: Complete — 11 frontend unit and 11 E2E tests passed; build passed.

### T32: Tratar falhas de banco nas rotas e cobrir proteções de antecipação
- **Requirement**: DATA AC05, ADV proteções de valor e estado.
- **Done when**: falhas reais de rota geram erro sanitizado, testes detectam antecipação paga e acima do original.
- **Status**: Complete — 45 backend tests passed; lint and Alembic check passed.

### T33: Explicar e permitir divisão por valores
- **Requirement**: SPLIT-01 AC04.
- **Done when**: formulário aceita valores por pessoa e informa diferença exata quando soma diverge.
- **Status**: Complete — 47 backend, 12 frontend unit, 11 E2E passed; lint and build passed.

### T34: Completar evidências dos fluxos financeiros
- **Requirement**: FAM, CARD, BUY, BILL, SETTLE, ADV, MIG, DATA — lacunas da rodada 1.
- **Done when**: asserções dos resultados compostos, isolamento, rollback e concorrência passam nas rotas reais.
- **Status**: Complete — 73 backend tests passed; lint and Alembic check passed.

### T35: Completar evidências de interface móvel
- **Requirement**: MONTH, BUY, ADV — lacunas da rodada 1.
- **Done when**: dimensões de toque, prévia completa, aviso e histórico persistido têm verificação de interface.
- **Status**: Complete — 12 frontend unit, 19 E2E passed; build passed.

## Correções — gates finais

T35 usa suíte completa de navegador e build; fixture de origem local isolada entre testes, sem alterar o rate limit de produção. AUTH AC05 permanece testado no backend.
