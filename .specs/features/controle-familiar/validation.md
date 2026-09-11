# Controle familiar — validação independente, rodada 2

**Veredicto: PASS no escopo funcional automatizado.** Data: 2026-09-11. Autor ≠ verificador. Baseline de projeto novo `d57bb6a..5b36aab`, incluindo arquivos do root; revisão corretiva `c3130a2..5553b34` (T29–T35), mais revisão pontual 5553b34..5b36aab (T36). Fonte normativa: spec.md. Relatório FAIL anterior preservado em `verification-evidence/validation-round1.md`.

## Gates e integridade

Execução independente:

- `./scripts/check-backend.sh`:PASS.
- `cd backend && uv run pytest -q && uv run alembic check`:73 PASS,0 falhas,0 skips; nenhuma operação nova Alembic.
- `cd frontend && npm run test:unit && npm run build && PW_CHANNEL=chrome npm run test:e2e`:13 unitários PASS,build PASS,19 E2E PASS.
- Total: 105 testes contra 59 na rodada1 e 0 pré-implementação; nenhuma remoção ou enfraquecimento identificado. Warnings de depreciação Starlette/httpx/anyio permanecem sem falha.
- Testes usam PostgreSQL real local55432 e API8000, Chrome/Vite. Helper de provisão E2E limpa apenas janelas de login loopback do banco dev com guard explícito de URL; AUTH limite10/11 e janela continuam testados no backend. Não é mudança de autenticação em produção.

## Resultado corretivo

Os oito grupos de falhas da rodada1 foram resolvidos: idempotência centralizada mantém chave após perda de resposta; handler SQL cobre falha no flush e commit; estimativas respeitam confirmação posterior; escolha mensal vive emApp; rótuloPróximo mês correto; projeção mostra finaisN/N; histórico de antecipação conserva original/desconto/data; formulário aceita rateio por valores e explica diferença. Logout móvel também foi exercitado. T36 protege parsing da resposta interrompida com mensagem em português e mantém a chave no retry; `frontend/src/api/client.test.ts:41` verifica mensagem/status e :44 verifica headers iguais.

T1–T28 e T29–T36 têm evidência compatível com seus critérios. **58/58 ACs sustentados por composição adequada de testes unitários, integração HTTP/PostgreSQL, E2E e inspeção de caminhos compartilhados.** Não exigi replicar cada exemplo em todas camadas: resultado matemático puro, uso pela rota e exibição são evidências complementares. A rodada1 marcava esses compostos como parciais; os novos testes cobrem os elementos faltantes.

## Critérios ancorados

P = `backend/tests/integration/` quando nomes curtos seguem a citação completa na mesma célula; arquivos/linhas financeiros referem-se a5553b34, mantidos no 5b36aab. Cada PASS está ligado a asserção observável. Sem lacuna normativa de precisão impeditiva identificada.

| AC | Resultado definido na spec | arquivo:linha + asserção/evidência | Resultado |
|---|---|---|---|
| FAM-01 AC01 | Duas sessões da mesma família leem despesa/valor iguais | backend/tests/integration/test_acceptance_edges.py:63 — get(member,commitment)==c (inclui valores/parcelas). | PASS |
| FAM-01 AC02 | Leitura/escrita de despesa negada a anônimo/outra família | backend/tests/integration/test_acceptance_edges.py:75 — status in (401,404); :76 descrição não em response.text; :77 entidade original inalterada para leitura/mutação anônimo/outra família. | PASS |
| FAM-01 AC03 | Lançamentos persistem após logout/login | backend/tests/integration/test_acceptance_edges.py:80/81 — logout200 e GET401; :88 get após novo login==c. | PASS |
| CARD-01 AC01 | Ciclo25/09→05/10, competência outubro | backend/tests/unit/test_cycles.py:14 — cycle[month] == date(2026,10,1) | PASS |
| CARD-01 AC02 | Dia31 em fevereiro2027 vira28 | backend/tests/unit/test_cycles.py:21 — closing_date == date(2027,2,28) | PASS |
| CARD-01 AC03 | Vencimento estritamente posterior; limites exclusivo/inclusivo | backend/tests/unit/test_cycles.py:29 — closing_date == 2026-09-05; :30 due_date == 2026-10-05; :14 fronteiras24/25/26 | PASS |
| CARD-01 AC04 | Prévia/confirmação, preservação manual/conferida/paga, datas inválidas | backend/tests/integration/test_acceptance_edges.py:311 — preview changes==[] para manual/conferida/paga/antecipada; :313 entidade completa==before; :322 e :339 ordem/vencimento inválidos409. test_cycle_changes.py:18/25 prova remanejamento confirmado. | PASS |
| BUY-01 AC01 | 30000/3 =10000 em out/nov/dez | backend/tests/integration/test_acceptance_edges.py:102 — meses[out,nov,dez]; :103 amounts==[10000]*3. | PASS |
| BUY-01 AC02 | 30000/3 =10000 em nov/dez/jan | backend/tests/integration/test_acceptance_edges.py:102 — meses[nov,dez,jan]; :103 amounts==[10000]*3. | PASS |
| BUY-01 AC03 | Dia25 prevê outubro e Conferir fatura | backend/tests/integration/test_commitments.py:42/43 — outubro,needs_reviewTrue; frontend/e2e/acceptance.spec.ts:92 — texto Parcela1/3 · Conferir fatura visível. | PASS |
| BUY-01 AC04 | 10000/3 =3334,3333,3333 | backend/tests/unit/test_money.py:8 — installments(10000,3)==[3334,3333,3333] | PASS |
| BUY-01 AC05 | Todas parcelas/competências antes de gravar | frontend/e2e/acceptance.spec.ts:24 — todas três competências visíveis; :25 três valores100,00 antes de salvar; CommitmentForm.test.tsx:16 — createOperation não chamado pela prévia. | PASS |
| BUY-01 AC06 | Compra/responsáveis/parcelas atomicamente | backend/tests/integration/test_acceptance_edges.py:147 — falha no flush das parcelas503; :149–151 Commitment/Share/Installment todas[] após rollback. | PASS |
| SPLIT-01 AC01 | Vanessa10000 Douglas0, titularDouglas | backend/tests/integration/test_acceptance_edges.py:104 — holder_id==Douglas; :106 people=={Douglas:0,Vanessa:10000}; :110 total10000. | PASS |
| SPLIT-01 AC02 | 5000 por pessoa, total10000 | backend/tests/unit/test_money.py:15 — allocate(10000,[1,1])==[5000,5000] | PASS |
| SPLIT-01 AC03 | 3333 dividido1667/1666 em ordem | backend/tests/unit/test_money.py:13 — allocate(3333,[1,1])==[1667,1666] | PASS |
| SPLIT-01 AC04 | Soma inválida bloqueada e diferença explicada; rateio por parcela | backend/tests/integration/test_commitments.py:85 — difference_cents==esperado; :86 fields[shares]; :87 mensagem faltam/sobram; :88[]; backend/tests/integration/test_acceptance_edges.py:132 rateios exatos por parcela70/30; frontend/src/components/CommitmentForm.test.tsx:30/32 erro e pesos7000/2000 do formulário. | PASS |
| BILL-01 AC01 | Aluguel160000 único por mês | backend/tests/integration/test_acceptance_edges.py:170 — amounts==[160000]*3 em duas consultas; :171 estimated==[False]*3. | PASS |
| BILL-01 AC02 | Variável estima36000, novembro38000 preserva outubro e último conhecido | backend/tests/integration/test_recurrences.py:37 — [36000,38000,38000]; :75 — correção antiga resulta[37000,38000,38000,38000]; :76 flagsFalse,False,True,True. | PASS |
| BILL-01 AC03 | 20000 posição2/4 só out/nov/dez | backend/tests/integration/test_acceptance_edges.py:203 — tuplas(2,out,20000),(3,nov,20000),(4,dez,20000). | PASS |
| BILL-01 AC04 | Fim dezembro preserva anterior, bloqueia pago | backend/tests/integration/test_recurrences.py:47 — len2 após encerrar dezembro; backend/tests/integration/test_acceptance_edges.py:184/185 —409/codepaid; :187/188 três meses preservados e pagamento dezembro intacto. | PASS |
| MONTH-01 AC01 | Regra09/10, fuso, quitado, escolha persiste na navegação | backend/tests/unit/test_month_selection.py:8–13 — datas/fuso/quitado/virada; frontend/e2e/overview.spec.ts:19 — mês2027-02 preservado após navegar; frontend/e2e/acceptance.spec.ts:29 mêsout após salvar. App mantém estado e não há timer de mudança. | PASS |
| MONTH-01 AC02 | Previsto15000 pago10000 restante5000 | backend/tests/integration/test_months.py:32 — totals == {expected:15000,paid:10000,remaining:5000}; frontend/src/pages/Overview.test.tsx:11–13 textos exatos | PASS |
| MONTH-01 AC03 | FiltroVanessa lista/total5000, família distinta15000 | backend/tests/integration/test_months.py:34 — totals=={expected:5000,paid:0,remaining:5000}; :35 len(items)==1; :36 family_total==15000 | PASS |
| MONTH-01 AC04 | 4 larguras sem overflow, compra, toque44 e labels | frontend/e2e/acceptance.spec.ts:16 — botões visíveis width/height>=44 nas4 larguras; :24/26/30 compra com descrição longa, prévia e resumo sem overflow nas4 larguras; getByLabel valida nomes acessíveis dos campos. CSS controlesmin44 inspecionado. | PASS |
| MONTH-01 AC05 | Vazio zero e ação adicionar | backend/tests/integration/test_months.py:37 — totals três zeros; frontend/e2e/overview.spec.ts:6 expected0,00; ação adicionar exercida purchase.spec.ts | PASS |
| MONTH-01 AC06 | 12 meses sem duplicação, estimativas e finaisN/N | frontend/e2e/acceptance.spec.ts:95 —12linhas; :96 dezembro mostra Compra no fechamento3/3; :97 janeiro0,00; Planning.test.tsx:11 marcador estimativas; test_months.py:43–45 intervalo12/total. | PASS |
| MONTH-01 AC07 | Aviso persistente + mês/pendente/atalho; Próximo mês | frontend/e2e/acceptance.spec.ts:77/81 — aviso150,00 persiste após navegação; :78 Próximo mês; :83 atalho seleciona corrente; :84 Mês atual. Código inclui monthLabel(current_month) no aviso. | PASS |
| MONTH-01 AC08 | Sinal explícito sem pendência, invalida criação/reabertura | backend/tests/integration/test_acceptance_edges.py:494 — plano aberto impede fechamento409; :495 estado planned; :515–519 defaultout→nov após sinal→out após nova despesa; test_month_closure.py:25 não paga implicitamente e :46 bloqueia após reopen. | PASS |
| SETTLE-01 AC01 | Mover out/nov/dez→nov/dez/jan, valores/responsáveis; bloquear pago | backend/tests/integration/test_acceptance_edges.py:230 — mesesnov/dez/jan persistidos; :235 valores10000*3; :236 shares==originais; test_changes.py:61 shift pago409. | PASS |
| SETTLE-01 AC02 | Fatura30000 quita parcelas sem duplicar | backend/tests/integration/test_payments.py:27 — len==1; :28 amount30000; :31 pending_count0 | PASS |
| SETTLE-01 AC03 | Bloquear alterações financeiras/exclusão pago até reabrir atomicamente | backend/tests/integration/test_acceptance_edges.py:400/409 — editar e excluir pago409; :426 planned após reabrir fatura; :427 todas parcelas paid_atNone. test_changes.py:61 competência paga bloqueada. | PASS |
| SETTLE-01 AC04 | Pagar novembro mantém outubro | backend/tests/integration/test_payments.py:29 — month2026-10-01; :30 paid_at2026-11-05 | PASS |
| SETTLE-01 AC05 | Conferir remove avisos; compra nova reabre conferência | backend/tests/integration/test_acceptance_edges.py:335 — needs_reviewFalse após conferir; :337 nova compra muda confirmedFalse. | PASS |
| SETTLE-01 AC06 | Confirmar exclusão lógica conjunta retira totais | backend/tests/integration/test_changes.py:33 confirmação ausente409; backend/tests/integration/test_acceptance_edges.py:242 total0; :244 compromisso deleted_at; :245 todas parcelas deleted_at. | PASS |
| ADV-01 AC01 | 44/48 outubro108400, original191900, desconto83500 e agosto2029 histórico | frontend/e2e/acceptance.spec.ts:61–66 —3003,00,duas linhas,44/48,original1919/desconto835 e agosto2029 após reload; backend/tests/integration/test_acceptance_edges.py:487 agosto2029 total0; test_advances.py:43 snapshot original. | PASS |
| ADV-01 AC02 | Planejar mantém35; pagar34; repetição neutra | backend/tests/integration/test_advances.py:40 pending35; test_advance_changes.py:28 tuple(34,43,48); :33 repetição mesma resposta | PASS |
| ADV-01 AC03 | Última43 original48; regular intacta sem renumerar | backend/tests/integration/test_acceptance_edges.py:500 — númerosrange10..44 intactos; :501 regular(10,191900); :505 last43/count48. | PASS |
| ADV-01 AC04 | Regular191900+antecipação108400=300300 duas linhas mesmo contrato | backend/tests/integration/test_acceptance_edges.py:481–487 —total300300,duas linhas mesmo commitment_id,identidades10/48 e44/48; frontend/e2e/acceptance.spec.ts:62/63 verifica duas linhas e44/48 na UI. | PASS |
| ADV-01 AC05 | Cartão20000/19998 destino aberto/anterior, quita pela fatura | backend/tests/integration/test_acceptance_edges.py:367–372 —20000/19998 no destino,outubro apenas; :388 totais pagos sem duplicar; :441 datasinválidas422; :449 paid_cycle destino fechado. Regra mesmo mêsantesdue inspecionada em advances.prepare e fronteiraigual rejeitada. | PASS |
| ADV-01 AC06 | Agregado19999→10000/9999 e herda rateio | backend/tests/integration/test_acceptance_edges.py:367 — amounts exatos20000/19998/19999; :381 rateios por número exatos; test_money.py:16 resultado10000/9999. | PASS |
| ADV-01 AC07 | Cancelar restaura; pago exige reopen; fatura original paga bloqueia | backend/tests/integration/test_advance_changes.py:46/52/55 —planned,cancelled,cronograma original; backend/tests/integration/test_acceptance_edges.py:418 cancelpago codepaid; :426 planned sem restaurar; :459 codepaid_cycle original; :469 restauração(cycle,month,amount)exata. | PASS |
| ADV-01 AC08 | Rejeitar paga/ativa/valor>original e piso1centavo | backend/tests/integration/test_advances.py:102–105 — paga409/codepaid e inalterada; :118–121 acimaoriginal422 e inalterada; :53 ativa409; backend/tests/integration/test_acceptance_edges.py:441 zero/piso insuficiente422; M4/M5 agora mortos. | PASS |
| ADV-01 AC09 | Disputa antecipar/antecipar ou pagar/antecipar aplica apenas primeira | backend/tests/integration/test_acceptance_edges.py:270 — concorrênciaHTTP antecipar/antecipar e pagar/antecipar resulta[200,409]; :273/274 número de planos/pendentes correto; :275/276 identidade/regular intactas. | PASS |
| ADV-01 AC10 | Shift ativo bloqueado e ciclo não move antecipação | backend/tests/integration/test_changes.py:80 —shift ativo409; backend/tests/integration/test_acceptance_edges.py:311–313 guardadvance mantém preview[] e compromisso inalterado após alteração ciclo. | PASS |
| MIG-01 AC01 | 10/12 out,11/12 nov,12/12 dez total13053 sem passado | backend/tests/integration/test_imports.py:20 numbers[10,11,12]; :21 meses exatos; :26 sum13053 | PASS |
| MIG-01 AC02 | Número<1 ou>total rejeitado sem gravar | backend/tests/integration/test_acceptance_edges.py:218 —[0]/[49]422; :219 lencommitments2 inalterado após tentativas inválidas. | PASS |
| MIG-01 AC03 | 10–44=35, original48, lacunas sem históricoinventado | backend/tests/integration/test_imports.py:36–38 —35pendentes/original48/last44; backend/tests/integration/test_acceptance_edges.py:211 tuplas10/out,12/dez,44/ago2029 sem pagos; :216 original48,pending3,importedTrue. | PASS |
| DATA-01 AC01 | Rejeitar limites/campos; trim1–200; total>=count | backend/tests/integration/test_acceptance_edges.py:534–536 —422,fields específico,nenhum registro; :542 trim200; :553/554 total<count422 fieldtotal; testes existentes cobrem zero/vazio/data inválida/count121. | PASS |
| DATA-01 AC02 | Mesma chave/conteúdo retorna original; diferente rejeitado | backend/tests/integration/test_uow.py:34 original; :37 count1; :38 raises AppError conteúdo diferente; test_commitments.py:51 mesmoid | PASS |
| DATA-01 AC03 | Versão concorrente primeira vence e segunda conflito | backend/tests/integration/test_uow.py:64 saved/conflict; :67 tuple(2,False); test_changes.py:25 HTTP409 | PASS |
| DATA-01 AC04 | Falha rede preserva formulário e chave para retry | frontend/e2e/acceptance.spec.ts:44 —servidor200 antes resposta abortada; :48/49 erro/formuláriopreservado; :52 keys iguais; :53 banco umcartão. frontend/src/api/client.test.ts:29/30 reutiliza key/body entre handlers; cliente central cobre outros formulários. | PASS |
| DATA-01 AC05 | Logerro com operação/código e sem payloadsensível | backend/tests/integration/test_uow.py:109 —erro no commit HTTP503; :111 code database_unavailable; :112 operation_id no log; :114 sentinela financeira ausente em log/resposta; :115 lista[] após rollback. | PASS |
| AUTH-01 AC01 | Cookieopaco Secure/HttpOnly/Lax e hash apenas | backend/tests/integration/test_auth.py:35/36 flags; :57 hash!=cookie :58 len64; :95 Secure; frontend/e2e/login.spec.ts:9 localStorage[] | PASS |
| AUTH-01 AC02 | Revogada/7dias/24h=>401; atividade não prolonga7dias | backend/tests/integration/test_auth.py:60 idle401; :66 absoluto401; :103 created_at inalterado; :104 last_seen<10seg; logout:47 401 | PASS |
| AUTH-01 AC03 | Logout revogaatual; resetsenha todasusuário | backend/tests/integration/test_auth.py:47 401; test_cli.py:25 all sessions revoked | PASS |
| AUTH-01 AC04 | CSRF/origeminválidos negam gravação | backend/tests/integration/test_auth.py:38 logout403 semcsrf; :40 origem403; M6 morto. Financeiro específico sem asserção, guardacomum exercitada. | PASS |
| AUTH-01 AC05 | 11ª em60seg=>429; novajanela permite | backend/tests/integration/test_auth.py:78 status429; :117 status401 após61seg | PASS |

## Sensor e limites

Sensor manual P0 ampliado:6 mutações semânticas independentes no snapshot 5553b34 obtido por git archive. Backend não mudou entre 5553b34 e 5b36aab; o gate frontend foi repetido integralmente no 5b36aab. Cada execução removeu __pycache__ e usou Python-B, sem tocar implementação/testes reais. Cada mutante executou os73 testes backend. Resultado final e logs em `verification-evidence/mutations-round2.json`.

| Mutante | Local | Falha introduzida | Resultado |
|---|---|---|---|
| M1 | backend/app/domain/money.py:8 | Remover centavos extras das parcelas | MORTO |
| M2 | backend/app/domain/money.py:19 | Remover resto do rateio | MORTO |
| M3 | backend/app/api/commitments.py:108 | Contar parcelas pagas como pendentes | MORTO |
| M4 | backend/app/api/advances.py:37 | Permitir antecipar parcela paga | MORTO |
| M5 | backend/app/api/advances.py:52 | Permitir valorfinal>original | MORTO |
| M6 | backend/app/api/auth.py:65 | Ignorar diferença deCSRF | MORTO |

**6/6 mortos, 0 sobreviventes.** As duas reproduções independentes da rodada1 (correção histórica de estimativa e falha SQL na rota), mantidas exclusivamente no scratch, agora passaram 2/2; são verificações extras e não entram na contagem de 105 do repositório. Testes novos discriminam os dois mutantes sobreviventes da rodada1. Não é cobertura exaustiva de todas combinações de estados nem auditoria formal de segurança.

## Qualidade e fronteira do aceite

Revisão de correções e módulos financeiros confirma mudanças focadas no pedido, sem novas abstrações desnecessárias ou alterações externas ao domínio. Centavos inteiros, RLS, bloqueio por família, versões e transações mantêm padrões consistentes. Testes novos se vinculam aosACs/Donewhen; não foram adicionados apenas para espelhar implementação. Nenhuma diretriz adicional de projeto além de spec/design/tasks foi identificada; padrões da skill aplicados. JSX em linhas extensas e uso de any continuam observações de manutenção, não defeitos funcionais demonstrados.

Happy/edge/error financeiro está exercitado nos caminhos compartilhados com resultados concretos, incluindo concorrência entre sessõesHTTP, falha no commit, invalidação, bloqueiospago/antecipado, dataslimite e rollback. Testes unitários matemáticos são discriminantes. A composição oferece evidência proporcional; não se afirma cobertura de cada combinação possível de rota e estado.

UAT humano não executado pelo verificador. QA visual local e Compose8089 pertencem à execução do autor; resultados de smoke/backup/restauração reportados anteriormente não foram contados como gates independentes nesta rodada. Deploy na VM, domínio HTTPS e capacidade de 2 GB não foram validados aqui. PASS funcional não afirma implantação em produção.

Requisitos FAM,CARD,BUY,SPLIT,BILL,MONTH,SETTLE,ADV,MIG,DATA,AUTH podem ser marcados Verified pelo orquestrador com referência a este relatório. Spec não foi alterada pelo verificador. Sem novas falhas ou sinais de lessons nesta rodada; lições fundamentadas da rodada1 permanecem registradas, sem promoção artificial por revalidação da mesma feature.
