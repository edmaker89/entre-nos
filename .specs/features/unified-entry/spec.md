# Cadastro unificado e navegação

Solicitação aprovada: um ponto de entrada para despesas, salvar e adicionar outra, Resumo e Lançamentos com funções distintas.

- ENTRY AC01: botão Adicionar despesa disponível em Resumo, Lançamentos, Cartões e Planejamento abre escolha Compra ou despesa / Conta recorrente / Parcelas em andamento. Nenhum cadastro depende de enviar planilha.
- ENTRY AC02: os três tipos usam fluxos existentes, preservam prévias/validação/idempotência. Salvar fecha; Salvar e adicionar outra mantém o tipo aberto, limpa dados do lançamento concluído, informa sucesso e permite trocar tipo. Falha mantém dados sem declarar sucesso.
- ENTRY AC03: competência selecionada inicia cadastro recorrente/em andamento e compra fora do cartão. Compras no cartão continuam calculadas pelo fechamento.
- NAV AC01: Resumo mostra totais, responsabilidades e até cinco pendências, com acesso à lista completa; Lançamentos mostra todos os itens da competência selecionada, pesquisa por descrição, filtros pessoa/situação, detalhes/edição e pagamentos. Seleção mensal persiste na navegação.
- NAV AC02: Planejamento mostra projeção. Gestão de recorrências fica em Lançamentos. Retirar entradas espalhadas de criação em Planejamento.
- UI AC01: fluxos novos funcionam em360/390/768/1440px sem overflow; ações nomeadas e feedback de gravação visível.

## Tarefas atômicas
1. Cadastro unificado: extrair formulários recorrente/em andamento, seleção global, salvar e adicionar outra. Gate: unitários/build e teste navegador dos três tipos/continuidade.
2. Separar Resumo/Lançamentos e limpar Planejamento. Gate: build e navegador pesquisa/filtros/persistência mensal.
3. Verificação integrada e Compose local; Verifier independente após implementação.

Os testes existentes serão adaptados somente nos cliques/rótulos alterados pela solicitação aprovada. Asserções financeiras e de segurança serão preservadas. Banco/backend sem alterações; não limpar nem semear o banco de uso local8089.

### Execução T1
Build e13 unitários passaram; e2e/unified-entry.spec.ts:13–40 verifica os três tipos, limpeza após sucesso, continuidade na telaCartões, competência herdada e total1743,51. Novos formulários reutilizam APIs existentes. T1 concluída.

### Solicitação adicional — excluir recorrência cadastrada por engano
REC AC01: ação Excluir recorrência em Lançamentos exige confirmação, exclui logicamente regra e ocorrências em uma transação, removendo projeções; não altera outros registros. REC AC02: qualquer ocorrência paga bloqueia exclusão até reabertura, versões conflitantes não sobrescrevem. REC AC03: cancelar confirmação não grava; erro permanece visível e cadastro é mantido.

Tarefa adicional independente: API de exclusão + ação na gestão de recorrências, testes PostgreSQL e navegador. Não excluir dados reais automaticamente.

### Execução T2
Build e13 unitários passaram. e2e/unified-entry.spec.ts:56–79 verifica total700, cinco pendências noResumo, sete itens emLançamentos, pesquisa/filtro resultando1/0/6 itens, mês preservado e ausência das antigas entradas noPlanejamento. T2 concluída.

### Execução REC
75 testes backend e13 unitários frontend passaram, build/lint passaram. test_recurrence_deletion.py verifica confirmação, versão, softdelete regra/ocorrências, projeção zerada e bloqueio até reabrir pagamento; unified-entry.spec.ts:75 confirma cancelamento sem exclusão e sucesso removendo a recorrência e zerando o mês. Nenhum registro real foi excluído.

### Gate integrado T3
75 testes backend,15 unitários frontend e22 E2E passaram; lint/build/Alembic check passaram. Total112. Nos testes antigos, somente entrada/rótulo de cadastro foi atualizado conforme a nova navegação aprovada; asserções financeiras foram preservadas.

| Critério | Evidência de resultado | Resultado esperado |
| --- | --- | --- |
| ENTRY AC01/02/03 | unified-entry.spec.ts:13–39: competência2026-10, statusDespesa salva, campos vazios após salvar, total1743,51 | Fluxo consecutivo de três tipos sem sair da tela |
| ENTRY AC02 falha | ScheduledExpenseForm.test.tsx:25–31: alertFalha de conexão, descrição/valor mantidos, onSaved somente após sucesso | Sem falso sucesso/perda de formulário |
| NAV AC01/02 | unified-entry.spec.ts:56–73: total700, linhas5/7/1/0/6 e mês2026-10 | Resumo distinto da lista pesquisável; Planejamento sem cadastros |
| REC AC01/02 | test_recurrence_deletion.py: confirmação/versão409, exclusão200, projeção[0,0,0], pagamento preservado até reabrir | Exclusão atômica protegida |
| REC AC03 | unified-entry.spec.ts:75–96: cancelar mantém regra, aceitar remove regra/lista e total0 | Confirmação controlada pelo usuário |
| UI AC01 | acceptance.spec.ts:12–32 (quatro larguras), unified-entry.spec.ts:5/39 | Cadastro responsivo com prévia e sem overflow |

Mapa reverso: cada cenário acima deriva de ENTRY/NAV/REC/UI ou dos critérios financeiros já aprovados; nenhuma asserção financeira foi removida ou enfraquecida. Sem alteração no esquema ou nos dados de uso local.
