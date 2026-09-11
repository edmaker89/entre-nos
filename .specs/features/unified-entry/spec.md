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
