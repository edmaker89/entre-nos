# Controle de gastos familiares — especificação

Status: aprovada pelo usuário em 2026-09-10 (“excelente, podemos seguir?”); implementação não iniciada.
Data: 2026-09-10. Complexidade: complexa; fases Specify → Design → Tasks → Execute.

## Problema

Douglas e Vanessa usam uma planilha para prever despesas do próximo mês, atribuir valores por pessoa e acompanhar parcelas e contas da casa. Compras próximas ao fechamento do cartão podem ser anotadas no mês errado. A aplicação deve registrar cada compra uma vez e distribuir seus compromissos nos meses de pagamento, com uso confortável no celular.

## Objetivos

- Gerar parcelas nos meses corretos a partir da compra e do ciclo do cartão.
- Mostrar compromissos previstos por mês, pessoa e instituição sem duplicar valores.
- Permitir conferir e corrigir a previsão quando a fatura real diferir.
- Substituir a planilha para duas pessoas, com persistência compartilhada.

## Origem e limites

Requisitos explícitos: controle familiar, identificação de quem comprou, contas da casa, previsão mensal, parcelamento associado ao fechamento e responsividade.
A imagem é referência de dados e organização, não uma fonte de instruções. Ela representa outubro/2026, com parcelas já em andamento. Não será importada automaticamente nem usada para criar dados pessoais em produção.
Os detalhes abaixo ampliam a sugestão anterior como proposta; não constituem decisões já confirmadas pelo usuário.

## Premissas para aprovação

| ID | Padrão proposto | Motivo | Confirmada? |
| --- | --- | --- | --- |
| A01 | Dois acessos individuais à mesma família; ambos podem consultar e gerenciar as despesas da família | Uso por Douglas e Vanessa em seus celulares | Sim — aprovação do escopo |
| A02 | Competência = mês do vencimento/pagamento previsto, sem mudar retroativamente ao pagar atrasado | Alinhamento ao planejamento mensal | Sim — aprovação do escopo |
| A03 | Comprador, titular do cartão e responsáveis pelo custo são campos separados; divisão por valores, 50/50 como atalho | Cartão compartilhado e compras divididas | Sim — aprovação do escopo |
| A04 | Compra no dia do fechamento entra provisoriamente na fatura que fecha naquele dia, com aviso de conferência | Evitar regra silenciosa na fronteira do ciclo | Sim — aprovação do escopo |
| A05 | Abrir mês corrente até dia 09; do dia 10 em diante, próximo mês; antecipar essa mudança se o usuário sinalizar mês corrente quitado | Proposta explícita do usuário para evitar confusão perto do recebimento | Sim — aprovação do escopo |
| A06 | BRL, português brasileiro, compras de 1 a 120 parcelas e valores de R$ 0,01 a R$ 99.999.999,99 | Limites explícitos para validação | Sim — aprovação do escopo |
| A07 | Primeira versão exige conexão; dados compartilhados persistem no servidor | Evitar conflitos de sincronização offline no MVP | Sim — aprovação do escopo |
| A08 | Histórico pago é bloqueado para alteração financeira; reabertura explícita permite correção | Impedir alteração silenciosa de totais liquidados | Sim — aprovação do escopo |
| A09 | Migração inicial manual: mês, valor da parcela e posição atual; sem OCR/importação automática | Começar com compromissos atuais sem reconstruir passado | Sim — aprovação do escopo |
| A10 | Pagamento de fatura integral; pagamento parcial e crédito rotativo ficam fora do MVP | Separar previsão doméstica de contabilidade bancária | Sim — aprovação do escopo |
| A11 | Contas variáveis repetem o último valor conhecido como estimativa até atualização | Projeção útil sem apresentar estimativa como valor confirmado | Sim — aprovação do escopo |
| A12 | Preservar número e total originais do contrato; exibir separadamente parcelas pendentes e última parcela em aberto | Antecipações não devem apagar a identidade das parcelas | Sim — aprovação do escopo |
| A13 | Antecipação seleciona parcelas inteiras, registra valor informado pelo usuário e pode começar como planejada; sem calcular desconto bancário | Atender carro e cartão sem simular regras do banco | Sim — aprovação do escopo |
| A14 | Sinalizar mês quitado exige ação explícita e nenhuma despesa aberta; novas pendências invalidam o sinal; mês vazio não é quitado automaticamente | Evitar avanço por ausência de lançamentos | Sim — aprovação do escopo |

Questões abertas sem padrão escolhido: nenhuma. As premissas acima integram o escopo aprovado; mudanças posteriores devem ser registradas.

## Histórias e critérios de aceitação

Os critérios usam WHEN/THEN/SHALL, com resultados definidos para orientar testes independentes.

### P1 — FAM-01: Família e persistência

Como integrante, quero acessar os mesmos dados com minha própria sessão.

- AC01: WHEN um integrante salva uma despesa e outro recarrega a mesma família THEN o sistema SHALL apresentar a mesma despesa e o mesmo valor.
- AC02: WHEN uma sessão não autenticada ou de outra família tenta ler ou alterar um identificador de despesa THEN o sistema SHALL negar acesso sem retornar os dados da despesa.
- AC03: WHEN o usuário encerra e reabre sua sessão THEN o sistema SHALL preservar os lançamentos salvos.

Teste independente: duas sessões da mesma família e uma de família distinta, com uma despesa de R$ 100.

### P1 — CARD-01: Cartões e ciclos

Como usuário, quero cadastrar titular, instituição, identificação do cartão, fechamento e vencimento.

- AC01: WHEN um ciclo tem fechamento em 25/09/2026 e vencimento em 05/10/2026 THEN o sistema SHALL atribuir à competência outubro/2026 as compras elegíveis desse ciclo.
- AC02: WHEN um dia cadastrado não existe no mês THEN o sistema SHALL usar o último dia desse mês; dia 31 em fevereiro/2027 resulta em 28/02/2027.
- AC03: WHEN gera ciclos pelo cadastro habitual THEN o sistema SHALL usar o primeiro vencimento estritamente posterior ao fechamento e limites de ciclo exclusivos no fechamento anterior e inclusivos no fechamento atual.
- AC04: WHEN o usuário altera o fechamento efetivo de um ciclo THEN o sistema SHALL mostrar a proposta de remanejamento das compras não conferidas e não pagas; aplicar somente após confirmação, sem mexer em compras ajustadas manualmente, conferidas ou pagas. Datas que invertam a ordem dos ciclos ou coloquem vencimento antes/no fechamento SHALL ser rejeitadas.

Teste independente: cadastrar ciclos setembro/outubro e fevereiro com dia inexistente.

### P1 — BUY-01: Compra e parcelas automáticas

Como usuário, quero informar compra, data, cartão, total e parcelas uma única vez.

- AC01: WHEN registra R$ 300 em 3 parcelas em 24/09/2026 com fechamento 25/09 e vencimento 05/10 THEN o sistema SHALL gerar R$ 100 em outubro, novembro e dezembro/2026.
- AC02: WHEN a mesma compra ocorre em 26/09/2026 THEN o sistema SHALL gerar R$ 100 em novembro e dezembro/2026 e janeiro/2027.
- AC03: WHEN a compra ocorre em 25/09/2026 THEN o sistema SHALL prever outubro como primeira competência e sinalizar “Conferir fatura”.
- AC04: WHEN o total não divide igualmente THEN o sistema SHALL distribuir centavos restantes nas primeiras parcelas; R$ 100/3 gera R$ 33,34, R$ 33,33 e R$ 33,33, sem perda de centavos.
- AC05: WHEN preenche uma compra válida THEN o sistema SHALL mostrar valores e competências de todas as parcelas antes de salvar.
- AC06: WHEN confirma a gravação THEN o sistema SHALL persistir compra, responsáveis e todas as parcelas como uma única operação: ou todos são salvos ou nenhum.

Teste independente: os quatro exemplos anteriores com conferência exata dos valores e datas.

### P1 — SPLIT-01: Responsabilidade independente do cartão

Como casal, queremos identificar quem comprou e quem arca com cada valor.

- AC01: WHEN Vanessa compra R$ 100 no cartão de Douglas e assume 100% THEN o sistema SHALL mostrar R$ 100 para Vanessa e R$ 0 para Douglas, mantendo Douglas como titular.
- AC02: WHEN divide uma parcela de R$ 100 igualmente THEN o sistema SHALL atribuir R$ 50 para cada um e manter apenas R$ 100 no total familiar.
- AC03: WHEN divide R$ 33,33 igualmente THEN o sistema SHALL atribuir R$ 16,67 ao primeiro responsável selecionado e R$ 16,66 ao segundo. Cada parcela é dividida independentemente, com resto em centavos na ordem dos responsáveis.
- AC04: WHEN os valores informados para os responsáveis não somam o total da compra THEN o sistema SHALL impedir gravação e explicar a diferença. As proporções dos valores escolhidos SHALL ser aplicadas a cada parcela com divisão inteira e distribuição do resto pela ordem dos responsáveis.

Teste independente: compra no cartão de outra pessoa e divisão com centavo indivisível.

### P1 — BILL-01: Contas recorrentes e compromissos finitos

Como usuário, quero prever aluguel, energia e financiamento sem cadastrar cada mês.

- AC01: WHEN cadastra aluguel de R$ 1.600 mensal a partir de outubro/2026 THEN o sistema SHALL exibir uma ocorrência de R$ 1.600 por mês consultado, sem duplicar ao recarregar.
- AC02: WHEN uma conta variável tem último valor conhecido de R$ 360 THEN o sistema SHALL projetar R$ 360 com marcador “Estimado”; atualizar novembro para R$ 380 SHALL preservar outubro.
- AC03: WHEN registra um compromisso de R$ 200 por parcela, posição 2/4 em outubro THEN o sistema SHALL gerar somente outubro, novembro e dezembro, identificados 2/4, 3/4 e 4/4.
- AC04: WHEN encerra uma recorrência a partir de dezembro THEN o sistema SHALL preservar meses anteriores e remover ocorrências não pagas de dezembro em diante. Havendo ocorrência paga nesse intervalo, SHALL bloquear e solicitar reabertura.

Teste independente: aluguel, conta variável e financiamento sem cartão.

### P1 — MONTH-01: Painel mensal responsivo

Como usuário, quero ver total previsto, pago e restante por mês, pessoa e cartão.

- AC01: WHEN abre o painel de 01 a 09/10/2026 sem sinal de mês quitado THEN o sistema SHALL selecionar outubro/2026; WHEN abre a partir de 10/10/2026 ou com outubro explicitamente sinalizado como quitado THEN SHALL selecionar novembro/2026. Usar America/Sao_Paulo; em 01/11 reiniciar a regra para novembro. A escolha manual SHALL permanecer durante a navegação atual, sem troca automática à meia-noite ou após salvar.
- AC07: WHEN o mês corrente tem despesas abertas e a abertura seleciona o próximo mês pelo dia 10 THEN o sistema SHALL exibir aviso persistente com mês, total pendente e atalho para o mês corrente. O título SHALL mostrar mês/ano e “Mês atual” ou “Próximo mês”, conforme a competência selecionada.
- AC08: WHEN o usuário sinaliza “Tudo deste mês foi pago” e existe alguma despesa aberta, inclusive antecipação planejada, THEN o sistema SHALL rejeitar o sinal e mostrar as pendências, sem marcar pagamentos automaticamente; sem pendências SHALL gravar o sinal e oferecer abrir o próximo mês. Mês vazio SHALL permanecer sem sinal até ação explícita. Nova despesa ou reabertura no mês SHALL invalidar o sinal; antes do dia 10 a próxima abertura SHALL voltar ao mês corrente.
- AC02: WHEN o mês contém R$ 100 de Douglas e R$ 50 de Vanessa, com R$ 100 pagos THEN o painel SHALL mostrar previsto R$ 150, pago R$ 100 e restante R$ 50.
- AC03: WHEN filtra Vanessa THEN a lista e os totais filtrados SHALL mostrar somente a responsabilidade de Vanessa, preservando a identificação do total familiar como informação distinta, se exibida.
- AC04: WHEN usa telas de 360, 390, 768 e 1440 pixels de largura THEN o sistema SHALL permitir cadastrar uma compra e consultar o painel sem rolagem horizontal da página; controles principais SHALL ter área de toque mínima de 44×44 pixels e campos com rótulos acessíveis.
- AC05: WHEN não há lançamentos no mês THEN o painel SHALL exibir totais zero e ação de adicionar despesa.
- AC06: WHEN consulta projeção de 12 meses THEN o sistema SHALL somar somente parcelas, compromissos e recorrências conhecidos, identificar estimativas e indicar parcelas finais com sua posição N/N.

Teste independente: dados controlados e fluxo de cadastro em viewport móvel.

### P1 — SETTLE-01: Conferência, correção e pagamento

Como usuário, quero corrigir a fatura prevista sem cadastrar novamente a compra.

- AC01: WHEN uma compra com parcelas outubro/novembro/dezembro é deslocada para novembro THEN o sistema SHALL mostrar e aplicar novembro/dezembro/janeiro, preservando valores e responsáveis; somente compras sem parcelas pagas podem ser deslocadas.
- AC02: WHEN paga uma fatura de R$ 300 THEN o sistema SHALL marcar seus R$ 300 em parcelas como pagos sem adicionar uma segunda despesa de R$ 300.
- AC03: WHEN tenta alterar valor, competência, divisão ou excluir despesa paga THEN o sistema SHALL bloquear a operação até reabertura explícita. Reabrir uma fatura SHALL reabrir suas parcelas atomicamente.
- AC04: WHEN paga em novembro uma conta de competência outubro THEN o sistema SHALL preservar outubro como competência e guardar a data real de pagamento em novembro.
- AC05: WHEN confere uma fatura THEN o sistema SHALL remover avisos de conferência das compras atribuídas a ela. Novas compras no ciclo SHALL voltar a exigir conferência desse ciclo.
- AC06: WHEN exclui uma compra sem parcelas pagas THEN o sistema SHALL pedir confirmação e excluir logicamente a compra e todas as suas parcelas juntas, retirando-as dos totais.

Teste independente: deslocamento de três parcelas, pagamento e reabertura sem dupla contagem.

### P1 — ADV-01: Planejar e registrar antecipações de parcelas

Como usuário, quero trazer uma ou mais parcelas futuras para o mês em que pretendo antecipá-las, registrar o valor com desconto e acompanhar a redução dos compromissos futuros, tanto em financiamento quanto em cartão.

Identidade: o número original e o total original do contrato são imutáveis. “Parcela 44 de 48” é diferente de “44 parcelas restantes”. A interface mostra quantidade pendente e última parcela em aberto separadamente. Valores e datas de exemplos são fictícios.

- AC01: WHEN seleciona a parcela original 44/48 de R$ 1.919, originalmente em agosto/2029, e planeja antecipá-la em outubro/2026 por R$ 1.084 THEN o sistema SHALL mostrar em outubro “Carro · Antecipação da parcela 44/48 · Planejada · R$ 1.084”, com valor original R$ 1.919, desconto informado R$ 835 e competência original nos detalhes. O valor SHALL contar uma única vez em outubro e sair da projeção ativa de agosto/2029; o histórico do vencimento original SHALL continuar acessível.
- AC02: WHEN planeja essa antecipação THEN o sistema SHALL manter a parcela não quitada e exibir a redução futura como planejada, sem reduzir o contador de parcelas efetivamente pendentes. WHEN confirma o pagamento de R$ 1.084 THEN SHALL marcar a parcela como quitada por antecipação e reduzir o contador de pendentes em exatamente 1. Repetir a confirmação SHALL não alterar novamente contador ou totais.
- AC03: WHEN paga antecipadamente a última parcela aberta, de número 44, e a anterior aberta é 43 THEN o sistema SHALL mostrar “Última parcela em aberto: 43”, mantendo “Contrato original: 48 parcelas”. A parcela regular do mês SHALL conservar seu número e valor; nenhuma parcela remanescente SHALL ser renumerada.
- AC04: WHEN outubro já inclui a parcela regular do carro de R$ 1.919 e a antecipação de R$ 1.084 THEN o painel SHALL exibir duas linhas vinculadas ao mesmo contrato, total R$ 3.003. A antecipação SHALL nunca aparecer como compra independente 1/1.
- AC05: WHEN antecipa no cartão duas parcelas de R$ 100 para uma fatura escolhida, com valor final total de R$ 200 ou R$ 199,98 THEN o sistema SHALL aceitar ambos, manter vínculo à compra, retirar as parcelas das faturas futuras e incluir somente R$ 200 ou R$ 199,98 na fatura destino. A quitação SHALL ocorrer pelo pagamento dessa fatura, sem outra despesa paralela. Destino SHALL estar aberto e não ser posterior a nenhuma das competências originais selecionadas; mover para o mesmo mês só é permitido com data prevista anterior ao vencimento original.
- AC06: WHEN seleciona múltiplas parcelas e informa um valor final agregado THEN o sistema SHALL distribuir o valor proporcionalmente aos valores originais, truncar em centavos e distribuir os centavos restantes na ordem crescente do número original; R$ 199,99 para duas parcelas originais iguais resulta R$ 100 e R$ 99,99. O rateio por responsável SHALL herdar as proporções da compra usando SPLIT-01.
- AC07: WHEN cancela antecipação ainda não paga THEN o sistema SHALL restaurar competências, valores e faturas originais atomicamente, retirar o lançamento antecipado e preservar registro do cancelamento. Se uma fatura original já estiver paga SHALL bloquear restauração até reabertura. Para antecipação paga SHALL exigir reabertura antes do cancelamento; reabrir pagamento SHALL voltar ao estado planejado sem restaurar silenciosamente o cronograma.
- AC08: WHEN seleciona parcela já paga ou com antecipação ativa THEN o sistema SHALL impedir uma segunda antecipação. Valor final SHALL ser maior que zero, no máximo igual à soma original e suficiente para alocar ao menos um centavo por parcela. Valor superior ao original SHALL ser rejeitado como ajuste com encargos fora deste fluxo.
- AC09: WHEN duas sessões tentam antecipar a mesma parcela ou uma tenta pagá-la enquanto outra a antecipa THEN somente a primeira alteração válida SHALL ser aplicada; a segunda SHALL receber conflito. Compra, parcelas, faturas e projeções SHALL mudar em uma única transação e usar DATA-01 para repetição segura.
- AC10: WHEN corrige ciclo ou desloca compra com antecipação ativa THEN o sistema SHALL bloquear o deslocamento coletivo e orientar cancelar a antecipação planejada ou reabrir/cancelar a paga antes de reorganizar. Alterações de ciclo SHALL não mover parcelas com antecipação ativa.

Teste independente: financiamento com parcela regular e última antecipada, plano cancelado, pagamento confirmado, cartão com e sem desconto e disputa concorrente. Nenhum cálculo de juros é necessário; o valor final vem do usuário.

### P1 — MIG-01: Trazer parcelas em andamento

Como usuário, quero começar pelos valores futuros da planilha.

- AC01: WHEN informa outubro/2026, parcela 10/12 de R$ 43,51 THEN o sistema SHALL criar outubro 10/12, novembro 11/12 e dezembro 12/12, totalizando R$ 130,53, sem inventar pagamentos anteriores.
- AC02: WHEN posição atual é maior que o total ou menor que 1 THEN o sistema SHALL rejeitar o cadastro sem gravar parcelas.

- AC03: WHEN migra financiamento originalmente em 48 parcelas, com parcela corrente 10 e última aberta 44 THEN o sistema SHALL permitir registrar intervalo pendente 10–44, total 35 parcelas, preservando total original 48. Parcelas fora do intervalo SHALL ficar sem histórico detalhado importado, sem inventar datas, descontos ou pagamentos; o usuário pode informar intervalos adicionais/exceções se houver lacunas. O número 44 da planilha SHALL não ser interpretado automaticamente como total original nem como quantidade restante.

Teste independente: lançamento manual de saldo de parcelamento e contrato com prazo já reduzido, sem depender da imagem.

### P1 — DATA-01: Integridade das operações

- AC01: WHEN recebe valor zero/negativo, data inválida, descrição vazia ou mais de 120 parcelas THEN o sistema SHALL rejeitar sem gravar dados e identificar o campo inválido. Descrições SHALL ter 1–200 caracteres após remoção de espaços nas extremidades; total em centavos SHALL ser pelo menos a quantidade de parcelas.
- AC02: WHEN a mesma operação é reenviada com a mesma chave de idempotência e mesmo conteúdo THEN o sistema SHALL retornar o resultado original sem duplicar dados. A mesma chave com conteúdo diferente SHALL ser rejeitada.
- AC03: WHEN duas sessões editam a mesma versão THEN somente a primeira gravação SHALL vencer; a segunda SHALL receber aviso de conflito e solicitar recarregamento sem sobrescrever silenciosamente.
- AC04: WHEN falha a rede ao salvar THEN o sistema SHALL manter o formulário, informar que a gravação não foi confirmada e permitir repetir com a mesma chave.
- AC05: WHEN ocorre erro de gravação THEN o sistema SHALL registrar identificador de operação e código de erro sem registrar credenciais, descrição da compra ou valores no log operacional.

Teste independente: repetição de requisição, falha transacional e conflito de duas sessões.

### P1 — AUTH-01: Sessão opaca aprovada

Estratégia aceita pelo usuário; prazos concretos propostos para fechar a precisão dos testes: absoluto 7 dias, inatividade 24 horas.

- AC01: WHEN login é válido THEN o sistema SHALL emitir token opaco em cookie HttpOnly/Secure/SameSite=Lax em produção e guardar somente seu hash no banco; não emitir JWT nem guardar sessão em localStorage.
- AC02: WHEN sessão foi revogada, atingiu 7 dias da emissão ou 24 horas sem atividade THEN o sistema SHALL negar acesso com 401; uma requisição válida atualiza atividade sem estender os 7 dias.
- AC03: WHEN logout ou redefinição administrativa de senha ocorre THEN o sistema SHALL revogar respectivamente a sessão atual ou todas as sessões desse usuário.
- AC04: WHEN mutação autenticada não apresenta CSRF válido ou vem de origem não permitida THEN o sistema SHALL negar a operação sem gravação financeira.
- AC05: WHEN a 11ª tentativa de login chega na mesma janela de 60 segundos por origem THEN o sistema SHALL responder 429; nova janela permite tentativas novamente.

Teste independente: relógio controlado, revogação, cookies, CSRF e limitação de tentativas; nenhuma senha em logs.

## Varredura de requisitos implícitos

| Dimensão | Resolução |
| --- | --- |
| Validação e limites | DATA-01, BUY-01, MIG-01 |
| Falhas parciais | BUY-01 AC06, DATA-01 AC04 |
| Repetição e duplicação | DATA-01 AC02; chave mantida enquanto o registro existir, inclusive exclusão lógica |
| Autenticação e limites | FAM-01; proposta: login limitado a 10 tentativas por minuto por origem, resposta de bloqueio na 11ª, nova janela após 60 segundos; mecanismo detalhado no Design |
| Concorrência | DATA-01 AC03 |
| Ciclo de vida | Exclusão lógica explícita, sem expiração automática dos dados da família; SETTLE-01 AC06 |
| Observabilidade | DATA-01 AC05 |
| Dependências externas | Sem integração bancária; falha de servidor/rede coberta por DATA-01 AC04; sessão inválida exige autenticação antes de repetir |
| Transições | Previsto/conferido e aberto/pago são estados distintos; SETTLE-01; antecipação planejada/paga/cancelada por ADV-01; sinal de mês quitado por MONTH-01; mudanças financeiras pagas exigem reabertura |

## Fora de escopo da primeira versão

| Item | Motivo |
| --- | --- |
| Open Finance, leitura de faturas e OCR | Cadastro manual resolve o fluxo central |
| Movimentar dinheiro ou pagar boletos | Aplicação registra planejamento e pagamentos realizados externamente |
| Cálculo bancário de juros/descontos, crédito rotativo, pagamento parcial e amortização que recalcula o valor de todas as prestações | O MVP registra antecipação de parcelas identificadas com valor final informado; recálculo contratual exige outra especificação |
| Operação offline e sincronização posterior | Evitar ampliar resolução de conflitos no MVP |
| Aplicativos nativos e publicação em lojas | Web responsiva atende celular e computador |
| PWA instalável, notificações e exportação | P2, após validar o fluxo principal; não fazem parte do aceite inicial |
| Importação automática da imagem/planilha e integração com bancos | Migração manual de parcelas restantes no MVP |
| Orçamento por categoria, receitas e investimentos | Escopo atual é previsão de despesas |

## Rastreabilidade

| ID | Prioridade | Estado | Tarefas |
| --- | --- | --- | --- |
| FAM-01 | P1 | Pending | T2–T6,T21,T22 |
| CARD-01 | P1 | Pending | T2,T7,T9,T13,T25 |
| BUY-01 | P1 | Pending | T2,T4,T7,T8,T10,T24 |
| SPLIT-01 | P1 | Pending | T2,T8,T10,T24 |
| BILL-01 | P1 | Pending | T2,T11,T14,T27 |
| MONTH-01 | P1 | Pending | T15,T18–T20,T23,T27 |
| SETTLE-01 | P1 | Pending | T2,T12,T13,T15,T25,T26 |
| ADV-01 | P1 | Pending | T2,T4,T8,T12,T13,T15–T17,T19,T26 |
| MIG-01 | P1 | Pending | T2,T11,T27 |
| DATA-01 | P1 | Pending | T1,T4,T10,T21 |
| AUTH-01 | P1 | Pending | T5,T6,T22 |

Cobertura planejada: 11 requisitos mapeados a tarefas; execução e verificação pendentes. Nenhum está implementado ou verificado.

## Critério de sucesso e fechamento da fase

Demonstrar cadastro único, projeção exata de parcelas antes/depois/no fechamento, divisão por pessoa, migração 10/12, pagamento sem duplicidade, abertura nos dias 09/10 e com mês quitado, antecipação planejada/paga/cancelada com e sem desconto e uso móvel. Testes devem derivar dos resultados acima. Execute exige gates e commits atômicos por tarefa, seguidos de Verifier independente.

Gate de especificação: resultados exemplificados, ambiguidades registradas como premissas e dimensões implícitas cobertas. Aprovação do usuário recebida; avançar para Design. Escolha de stack e hospedagem pertence ao Design.
