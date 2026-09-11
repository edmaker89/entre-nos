# Controle familiar — validação independente, rodada 1

**Veredicto: FAIL.** Data: 2026-09-10. Autor ≠ verificador. Fonte normativa: spec.md; desenho usado apenas para contratos explícitos. Superfície: projeto novo `d57bb6a..c3130a2` (inclui arquivos iniciais do root). Correções simultâneas do autor não estão incluídas neste veredicto.

## Gates e integridade

- `./scripts/check-backend.sh`: PASS.
- `cd backend && uv run pytest -q && uv run alembic check`: 41 PASS, zero skips/falhas; sem operações novas Alembic.
- `cd frontend && npm run test:unit && npm run build && PW_CHANNEL=chrome npm run test:e2e`: 8 unitários PASS, build PASS, 10 E2E PASS. Total:59 testes, contra zero antes da implementação; nenhuma remoção de teste ou enfraquecimento identificado no projeto novo.
- PostgreSQL real local, API8000 e PlaywrightChrome. Warnings de depreciação Starlette/httpx/anyio e NO_COLOR não impediram gates.
- Smoke Compose8089/backup/restauração: execução PASS informada pelo autor; não rerodada pelo verificador, portanto não contada como teste independente. Implantação na VM/HTTPS real não verificada.
- T1–T28 estão marcadas Complete em tasks.md; essa marcação não substitui o aceite. T14,T21,T23,T25–T27 e observabilidade T4/T5 precisam correção/verificação. Spec rastreabilidade continua Pending; não alterada para evitar declarar verificação inexistente.

## Falhas priorizadas e tarefas corretivas

1. **P1 / DATA-01 AC04 — repetição de gravação pode duplicar importação/recorrência/cartão.** `frontend/src/pages/Planning.tsx:13`, `Cards.tsx:10` e ações em Commitment/Overview criam `createOperation(...)` de novo em cada tentativa. Se servidor confirmou e resposta foi perdida, o próximo clique envia chave nova. Conservar operação enquanto conteúdo não mudou; testar resposta perdida após sucesso real e retry com mesma chave/único registro. Formulário de compra já conserva sua operação; não generalizar esse resultado para outras telas.
2. **P1 / DATA-01 AC05 — erro SQL da rota não recebe tratamento sanitizado.** `backend/app/api/auth.py:28` abre transação diretamente; `unit_of_work.transaction` contém handler testado mas não usado nas rotas. Injetar IntegrityError em persist_purchase retorna500 texto `Internal Server Error`, sem contrato503/operação/código; traceback do servidor pode expor parâmetros SQL. Capturar no caminho HTTP incluindo commit, gerar código e ID correlacionados, logar sem exceção/payload e testar rollback da compra e log via rota.
3. **P1 / BILL-01 AC02 — corrigir mês antigo sobrescreve estimativa após mês confirmado posterior.** `backend/app/api/recurrences.py:143` atualiza todas futuras estimadas. Reproduzido em snapshot: novembro38000 confirmado; outubro37000 corrigido; dezembro observado37000, esperado38000. Recalcular cada estimativa pelo último confirmado anterior, preservando pago/confirmado, e testar ordem inversa de edição.
4. **P2 / MONTH-01 AC01/07 — seleção manual se perde e rótulo errado.** `Overview.tsx:6` guarda mês local; `App.tsx:22` desmonta a tela ao ir a Cartões/Planejamento. Voltar reinicia default. `Overview.tsx:20` usa Planejamento onde critério pede Próximo mês. Elevar seleção à navegação/sessão de UI e testar ida/volta, salvar e aviso corrente.
5. **P2 / MONTH-01 AC06 — projeção não mostra parcelas finais N/N.** `Planning.tsx:15` mostra apenas mês,total,estimativas apesar de API fornecer parcelas. Renderizar identificação do compromisso e posição final; testar último mês e desaparecimento subsequente.
6. **P2 / ADV-01 AC01 — detalhe persistido não exibe original/desconto.** `Commitment.tsx:16` mostra ambos só na prévia; após salvar/reabrir detalhe, histórico mostra apenas final/mês/estado. Renderizar original, desconto, competência original e identidade para cada plano usando snapshot, inclusive cancelados; teste após reload.
7. **P2 / SPLIT-01 AC04 — rateio por valores não está disponível e erro de soma não explica diferença.** `frontend/src/components/CommitmentForm.tsx:10` só constrói rateio100% ou igual; não há campos para divisão70/30 aprovada emA03. Adicionar entrada de valores por pessoa e manter atalho50/50. `commitments.py:38` gera ValueError, `main.py:36` substitui mensagem por Revise os campos informados e fields body. Retornar diferença em centavos e campo shares sem payload em log; exibir no formulário e testar divergência.
8. **P1 / cobertura — dois mutantes financeiros sobreviveram, e ACs compostos têm evidência parcial.** Acrescentar testes específicos dos bloqueios de antecipação paga e valor superior; concorrência financeira antecipar/antecipar e pagar/antecipar; RLS via endpoints com dois membros e outra família; rollback real no meio da compra; cancelamento com fatura original paga; ciclo preservando manual/conferida/paga/antecipada; toque44 e navegação. Critérios parciais abaixo não contam como cobertos integralmente. Revalidar após correções, máximo3 rodadas.

Reproduções somente em cópia temporária; fonte guardada em `verification-evidence/reproductions-round1.py.txt`. Nenhum código/teste da árvore real foi alterado pelo verificador.

## Critérios ancorados na spec

PASS significa resultado integral sustentado pelas asserções citadas; PARCIAL significa que há evidência útil mas falta parte do critério composto; GAP significa nenhuma evidência suficiente; FAIL identifica divergência funcional. PARCIAL/GAP contam zero para cobertura integral. Todos os caminhos/linhas referem-se a c3130a2; intervalos citados são conjuntos de asserções próximas. Sem lacuna de precisão normativa que impeça avaliar os resultados concretos: os gaps são implementação/evidência.

**Contagem independente: 58 ACs; 1 GAP, 29 PARCIAL, 20 PASS, 8 FAIL.**

| AC | Resultado definido | arquivo:linha + asserção/evidência | Resultado |
|---|---|---|---|
| FAM-01 AC01 | Duas sessões da mesma família leem despesa/valor iguais | Sem asserção entre dois clientes da mesma família. | GAP |
| FAM-01 AC02 | Leitura/escrita de despesa negada a anônimo/outra família | backend/tests/integration/test_schema.py:16 — SELECT month_closures == []; testa RLS de outra entidade, não identificador de despesa HTTP. | PARCIAL |
| FAM-01 AC03 | Lançamentos persistem após logout/login | frontend/e2e/login.spec.ts:6 — heading Resumo visível após reload; não verifica lançamento salvo. Smoke de persistência informado pelo autor. | PARCIAL |
| CARD-01 AC01 | Ciclo25/09→05/10, competência outubro | backend/tests/unit/test_cycles.py:14 — cycle[month] == date(2026,10,1) | PASS |
| CARD-01 AC02 | Dia31 em fevereiro2027 vira28 | backend/tests/unit/test_cycles.py:21 — closing_date == date(2027,2,28) | PASS |
| CARD-01 AC03 | Vencimento estritamente posterior; limites exclusivo/inclusivo | backend/tests/unit/test_cycles.py:29 — closing_date == 2026-09-05; :30 due_date == 2026-10-05; :14 fronteiras24/25/26 | PASS |
| CARD-01 AC04 | Prévia/confirmação, preservação manual/conferida/paga, datas inválidas | backend/tests/integration/test_cycle_changes.py:18 — changes[0][first_month] == 2026-11-01; :41 status409. Sem todas exclusões/ordem. | PARCIAL |
| BUY-01 AC01 | 30000/3 =10000 em out/nov/dez | backend/tests/integration/test_commitments.py:48 — amounts == [10000]*3; :50 só primeira competência é comparada. | PARCIAL |
| BUY-01 AC02 | 30000/3 =10000 em nov/dez/jan | backend/tests/integration/test_commitments.py:48 — amounts == [10000]*3; :50 só primeira competência é comparada. | PARCIAL |
| BUY-01 AC03 | Dia25 prevê outubro e Conferir fatura | backend/tests/integration/test_commitments.py:42 — first month == 2026-10-01; :43 needs_review == True; texto UI sem asserção. | PARCIAL |
| BUY-01 AC04 | 10000/3 =3334,3333,3333 | backend/tests/unit/test_money.py:8 — installments(10000,3)==[3334,3333,3333] | PASS |
| BUY-01 AC05 | Todas parcelas/competências antes de gravar | frontend/e2e/purchase.spec.ts:12 — 1/3 outubro visível; frontend/src/components/CommitmentForm.test.tsx:16 — createOperation não chamado. Não confere todas parcelas. | PARCIAL |
| BUY-01 AC06 | Compra/responsáveis/parcelas atomicamente | backend/tests/integration/test_uow.py:29 — MonthClosure rollback == []; não injeta falha na compra/parcelas real. | PARCIAL |
| SPLIT-01 AC01 | Vanessa10000 Douglas0, titularDouglas | backend/tests/unit/test_money.py:14 — allocate(10000,[0,1])==[0,10000]; test_commitments.py:49 responsável other_id; não verifica conjunto completo. | PARCIAL |
| SPLIT-01 AC02 | 5000 por pessoa, total10000 | backend/tests/unit/test_money.py:15 — allocate(10000,[1,1])==[5000,5000] | PASS |
| SPLIT-01 AC03 | 3333 dividido1667/1666 em ordem | backend/tests/unit/test_money.py:13 — allocate(3333,[1,1])==[1667,1666] | PASS |
| SPLIT-01 AC04 | Soma inválida bloqueada e diferença explicada; rateio por parcela | backend/tests/integration/test_commitments.py:67 — status422; :75 lista vazia. Resposta apenas Revise campos; não explica diferença; formulário não permite rateio por valores arbitrários. | FAIL |
| BILL-01 AC01 | Aluguel160000 único por mês | backend/tests/integration/test_recurrences.py:19 — [36000]*3 e :21 len==3, apenas variável. Sem caso aluguel fixo. | PARCIAL |
| BILL-01 AC02 | Variável estima36000, novembro38000 preserva outubro e último conhecido | backend/tests/integration/test_recurrences.py:37 — [36000,38000,38000]; reprodução independente corrige outubro37000 e dezembro cai37000 indevidamente. | FAIL |
| BILL-01 AC03 | 20000 posição2/4 só out/nov/dez | backend/tests/integration/test_imports.py:20 — [10,11,12] e :26 total13053; sem exemplo2/4. | PARCIAL |
| BILL-01 AC04 | Fim dezembro preserva anterior, bloqueia pago | backend/tests/integration/test_recurrences.py:47 — len==2 após fim; sem caso dezembro pago. | PARCIAL |
| MONTH-01 AC01 | Regra09/10, fuso, quitado, escolha persiste na navegação | backend/tests/unit/test_month_selection.py:8–13 — datas exatas; frontend/e2e/overview.spec.ts:8/10 seleção. Overview estado local é perdido ao visitar Cartões. | FAIL |
| MONTH-01 AC02 | Previsto15000 pago10000 restante5000 | backend/tests/integration/test_months.py:32 — totals == {expected:15000,paid:10000,remaining:5000}; frontend/src/pages/Overview.test.tsx:11–13 textos exatos | PASS |
| MONTH-01 AC03 | FiltroVanessa lista/total5000, família distinta15000 | backend/tests/integration/test_months.py:34 — totals=={expected:5000,paid:0,remaining:5000}; :35 len(items)==1; :36 family_total==15000 | PASS |
| MONTH-01 AC04 | 4 larguras sem overflow, compra, toque44 e labels | frontend/e2e/overview.spec.ts:11 — scrollWidth<=innerWidth em4 larguras; purchase.spec.ts:16 fluxo móvel; sem dimensão44 e cadastro em todas larguras. | PARCIAL |
| MONTH-01 AC05 | Vazio zero e ação adicionar | backend/tests/integration/test_months.py:37 — totals três zeros; frontend/e2e/overview.spec.ts:6 expected0,00; ação adicionar exercida purchase.spec.ts | PASS |
| MONTH-01 AC06 | 12 meses sem duplicação, estimativas e finaisN/N | backend/tests/integration/test_months.py:43 — len==12; Planning.test.tsx:11 estimativas; Planning.tsx não renderiza finaisN/N. | FAIL |
| MONTH-01 AC07 | Aviso persistente + mês/pendente/atalho; Próximo mês | Sem asserção de aviso; frontend/src/pages/Overview.tsx:20 usa Planejamento em vez de Próximo mês. | FAIL |
| MONTH-01 AC08 | Sinal explícito sem pendência, invalida criação/reabertura | backend/tests/integration/test_month_closure.py:19 status409; :25 paid_at is None; :32 closed True; :46 409 após reabertura. Sem antecipação planejada/default antes10. | PARCIAL |
| SETTLE-01 AC01 | Mover out/nov/dez→nov/dez/jan, valores/responsáveis; bloquear pago | backend/tests/integration/test_changes.py:15 — três meses prévia; :24 valores; :61 bloqueio pago409; sem responsáveis após shift nem meses persistidos. | PARCIAL |
| SETTLE-01 AC02 | Fatura30000 quita parcelas sem duplicar | backend/tests/integration/test_payments.py:27 — len==1; :28 amount30000; :31 pending_count0 | PASS |
| SETTLE-01 AC03 | Bloquear alterações financeiras/exclusão pago até reabrir atomicamente | backend/tests/integration/test_changes.py:61 — shift409; test_payments.py:46 pending_count1 após reopen; sem exclusão/valor/divisão pago. | PARCIAL |
| SETTLE-01 AC04 | Pagar novembro mantém outubro | backend/tests/integration/test_payments.py:29 — month2026-10-01; :30 paid_at2026-11-05 | PASS |
| SETTLE-01 AC05 | Conferir remove avisos; compra nova reabre conferência | backend/tests/integration/test_cycle_changes.py:35 — confirmed is True; não asserts needs_review/new purchase. | PARCIAL |
| SETTLE-01 AC06 | Confirmar exclusão lógica conjunta retira totais | backend/tests/integration/test_changes.py:33 —409 sem confirmação; :47 get404 e :48 listing[]; sem totais e parcelas excluídas. | PARCIAL |
| ADV-01 AC01 | 44/48 outubro108400, original191900, desconto83500 e agosto2029 histórico | backend/tests/integration/test_advances.py:35 desconto83500; :43 tuple(44,108400,out2026,ago2029); UI perde original/desconto após salvar. | FAIL |
| ADV-01 AC02 | Planejar mantém35; pagar34; repetição neutra | backend/tests/integration/test_advances.py:40 pending35; test_advance_changes.py:28 tuple(34,43,48); :33 repetição mesma resposta | PASS |
| ADV-01 AC03 | Última43 original48; regular intacta sem renumerar | backend/tests/integration/test_advance_changes.py:28 tuple(34,43,48); sem asserção regular número/valor e todos números. | PARCIAL |
| ADV-01 AC04 | Regular191900+antecipação108400=300300 duas linhas mesmo contrato | backend/tests/integration/test_advances.py:49 — soma mês300300 no contrato; sem duas linhas UI/ausência1/1. | PARCIAL |
| ADV-01 AC05 | Cartão20000/19998 destino aberto/anterior, quita pela fatura | backend/tests/integration/test_advances.py:79 mesesout*3; :80 amounts10000*3; :81 um ciclo. Sem desconto/pagamento/destinoinválido. | PARCIAL |
| ADV-01 AC06 | Agregado19999→10000/9999 e herda rateio | backend/tests/unit/test_money.py:16 — allocate(19999,[10000,10000])==[10000,9999]; sem rateio persistido por responsável. | PARCIAL |
| ADV-01 AC07 | Cancelar restaura; pago exige reopen; fatura original paga bloqueia | backend/tests/integration/test_advance_changes.py:46 planned; :52 cancelled; :55 tuple(month,amount,due) original; sem bloqueios cartão/pago. | PARCIAL |
| ADV-01 AC08 | Rejeitar paga/ativa/valor>original e piso1centavo | backend/tests/integration/test_advances.py:53 —409 duplicada ativa; mutantes M4/M5 sobrevivem41 testes. | PARCIAL |
| ADV-01 AC09 | Disputa antecipar/antecipar ou pagar/antecipar aplica apenas primeira | backend/tests/integration/test_uow.py:64 — closure genérica saved/conflict, não disputa financeira ou atomicidade do plano. | PARCIAL |
| ADV-01 AC10 | Shift ativo bloqueado e ciclo não move antecipação | backend/tests/integration/test_changes.py:80 shift409 com plano ativo; sem alteração ciclo. | PARCIAL |
| MIG-01 AC01 | 10/12 out,11/12 nov,12/12 dez total13053 sem passado | backend/tests/integration/test_imports.py:20 numbers[10,11,12]; :21 meses exatos; :26 sum13053 | PASS |
| MIG-01 AC02 | Número<1 ou>total rejeitado sem gravar | backend/tests/integration/test_imports.py:40 status422 para [0],[49],duplicado; não compara ausência gravação. | PARCIAL |
| MIG-01 AC03 | 10–44=35, original48, lacunas sem históricoinventado | backend/tests/integration/test_imports.py:36 pending35; :37 original48; :38 last44; sem exceções/lacunas/histórico. | PARCIAL |
| DATA-01 AC01 | Rejeitar limites/campos; trim1–200; total>=count | backend/tests/integration/test_commitments.py:67 status422 e :75 []; testes money limites; sem fields/trim200 e limite superior HTTP. | PARCIAL |
| DATA-01 AC02 | Mesma chave/conteúdo retorna original; diferente rejeitado | backend/tests/integration/test_uow.py:34 original; :37 count1; :38 raises AppError conteúdo diferente; test_commitments.py:51 mesmoid | PASS |
| DATA-01 AC03 | Versão concorrente primeira vence e segunda conflito | backend/tests/integration/test_uow.py:64 saved/conflict; :67 tuple(2,False); test_changes.py:25 HTTP409 | PASS |
| DATA-01 AC04 | Falha rede preserva formulário e chave para retry | frontend/src/api/client.test.ts:13 headers iguais em mesmo closure; CommitmentForm.test.tsx:19 descrição retida; Cards/Planning recriam closure a cada submit. | FAIL |
| DATA-01 AC05 | Logerro com operação/código e sem payloadsensível | backend/tests/integration/test_uow.py:85 log sanitizado apenas helper; auth.database não usa helper; reprodução rota500 genérico. | FAIL |
| AUTH-01 AC01 | Cookieopaco Secure/HttpOnly/Lax e hash apenas | backend/tests/integration/test_auth.py:35/36 flags; :57 hash!=cookie :58 len64; :95 Secure; frontend/e2e/login.spec.ts:9 localStorage[] | PASS |
| AUTH-01 AC02 | Revogada/7dias/24h=>401; atividade não prolonga7dias | backend/tests/integration/test_auth.py:60 idle401; :66 absoluto401; :103 created_at inalterado; :104 last_seen<10seg; logout:47 401 | PASS |
| AUTH-01 AC03 | Logout revogaatual; resetsenha todasusuário | backend/tests/integration/test_auth.py:47 401; test_cli.py:25 all sessions revoked | PASS |
| AUTH-01 AC04 | CSRF/origeminválidos negam gravação | backend/tests/integration/test_auth.py:38 logout403 semcsrf; :40 origem403; M6 morto. Financeiro específico sem asserção, guardacomum exercitada. | PASS |
| AUTH-01 AC05 | 11ª em60seg=>429; novajanela permite | backend/tests/integration/test_auth.py:78 status429; :117 status401 após61seg | PASS |

## Sensor de discriminação

Snapshot obtido por git archive c3130a2, dependências existentes referenciadas externamente; seis mutações semânticas independentes. Cada uma executou `python -B -m pytest -q` (41 testes), removendo __pycache__ antes para evitar bytecode antigo. Uma tentativa preliminar contaminada por cache foi descartada e não conta. Profundidade P0 manual ampliada; não equivale a exaustão de todas as combinações de estados.

| Mutante | Local | Alteração | Resultado |
|---|---|---|---|
| M1 | backend/app/domain/money.py:8 | Eliminar centavos extras nas parcelas | MORTO: test_money.py:8, 1fail40pass |
| M2 | backend/app/domain/money.py:19 | Eliminar centavo de resto no rateio | MORTO: test_money.py:13, 1fail40pass |
| M3 | backend/app/api/commitments.py:104 | Contar todas parcelas como pendentes | MORTO: advance_changes/payment, 2fail39pass |
| M4 | backend/app/api/advances.py:37 | Não rejeitar parcela já paga | SOBREVIVEU:41pass |
| M5 | backend/app/api/advances.py:52 | Aceitar valor final acima do original | SOBREVIVEU:41pass |
| M6 | backend/app/api/auth.py:65 | Comparar hashCSRF consigo mesmo | MORTO: auth.py:38, 1fail40pass |

Resultado: **4 mortos / 2 sobreviventes — FAIL**. Evidência detalhada: `verification-evidence/mutations-round1.json`. Scratch limpo `/var/folders/tj/2hr1s3rn7zdc5xs5bv02xxmw0000gn/T/expense-verifier-9uaqx2ca`; nenhuma mutação aplicada à árvore real.

## Qualidade, limites e próximos passos

Código usa centavos inteiros, RLS e lockporfamília de forma coerente, migração Alembic e transações SQLAlchemy; padrões de estado/versionamento ajudam integridade. A revisão focalizou todos módulos financeiros e páginas alteradas, mas não é auditoria formal de cada linha ou pentest. Frontend concentra JSX extenso em poucas linhas e `any`, dificultando revisão; isso é observação de manutenção, não falha autônoma de aceite. Não identifiquei escopo funcional estranho ao pedido. Não há guideline de projeto adicional além da spec/design/tasks; defaults da skill aplicados.

Mapeamento por camada não atende integralmente: unitários matemáticos são precisos e matam alterações, porém testes de rotas não cobrem happy+edge+error em todas as rotas e alguns testes do helper são apresentados como evidência de endpoints que não o utilizam. Não encontrei testes sem relação com AC/Donewhen; bootstrap/build são rastreados aT21.

UAT humano não realizado pelo verificador; autor realiza QA visual separado. Não declarar aceite visual a partir de Playwright de tela vazia. Falta verificar ações44×44, conteúdo longo e todos fluxos financeiros móveis. O autor relatou logout escondido no celular e corrigirá separadamente.

Estado de requisitos: FAM/CARD/BUY/SPLIT/BILL/MONTH/SETTLE/ADV/MIG/DATA precisam completar evidências ou correções; AUTH tem evidência suficiente dos cinco ACs no escopo testado. Nenhum requisito foi promovido silenciosamente no spec. Reexecutar gates e sensor após tarefas corretivas; preservar este resultado como rodada1.

Lições:40 sinais registrados pelo script oficial (candidatos deduplicados em `.specs/lessons.json` e `.specs/LESSONS.md`); nenhuma promoção manual.
