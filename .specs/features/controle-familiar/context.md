# Contexto — controle familiar

Data: 2026-09-10. Status: aprovado pelo usuário em 2026-09-10; pronto para Design.

## Limite da funcionalidade

Substituir a planilha de despesas futuras por aplicação responsiva com cartão, parcelas por competência, contas domésticas e totais por pessoa. Ver spec.md para critérios e exclusões.

## Confirmado pelo usuário

- Uso familiar; esposa costuma usar o cartão do marido.
- Registrar quem comprou, parcelas e contas da casa.
- O mês correto depende do fechamento do cartão.
- A imagem representa valores previstos do mês seguinte.
- A aplicação deve funcionar no celular.
- Usar tlc-spec-driven para conduzir o projeto.
- Ajustar a competência inicial para o próximo mês somente a partir do dia 10 ou quando sinalizado que o mês corrente foi pago.
- Incluir antecipação de parcelas do financiamento e cartão, com valor após desconto e identificação da parcela antecipada.
- O carro foi originalmente financiado em 48 parcelas; o total 44 na planilha já reflete redução de prazo. A linha 1/1 de adiantamento representa intenção de antecipar a parcela 44, não uma nova compra.

## Áreas não discutidas e premissas propostas

- Compartilhamento: duas contas e uma família, acesso simétrico (A01/A07).
- Competência e fechamento: mês de vencimento; fronteira do fechamento com aviso e correção manual (A02/A04).
- Responsabilidade: comprador separado do pagador; divisão por valores (A03).
- Experiência: mês corrente até dia 09; próximo mês a partir do dia 10 ou quando sinalizado quitado. Detalhes de aviso de pendências e sinal explícito propostos em MONTH-01. Interface em pt-BR e BRL (A05/A06/A14).
- Histórico e migração: bloquear pagos; cadastro manual das parcelas restantes (A08/A09).
- Pagamentos e estimativas: quitação integral de fatura e conta variável estimada (A10/A11).

Essas premissas não são respostas atribuídas ao usuário. A aprovação da proposta as estabelece como base; ajustes devem atualizar a especificação antes do desenho técnico.

## Antecipação — representação proposta

Manter número original, vencimento original e total contratado; mostrar separadamente parcelas pendentes e última parcela aberta. Plano de antecipação entra na previsão do mês escolhido; somente pagamento confirmado reduz o contador de pendentes. Desconto é informado, sem cálculo bancário. Cancelar plano restaura o cronograma. A12/A13 registram os detalhes aprovados com o escopo.

Esta ampliação foi solicitada explicitamente pelo usuário durante revisão de Specify e passa a integrar o MVP em ADV-01.

## Referências

Imagem da planilha CONTROLE DE GASTOS, aba OUTUBRO/2026: instituição, descrição, parcela atual, total de parcelas, pessoa e valor; resumo separado por Douglas e Vanessa. Não armazenar a imagem temporária como dependência do aplicativo.

## Discrição técnica

PostgreSQL diretamente na VM foi escolhido pelo usuário (2 GB RAM, 4 vCPUs), sem Supabase. Frontend React e backend separado são preferências explícitas; FastAPI é a recomendação pelo domínio de Python. Autenticação e detalhes técnicos continuam em definição. Não há implementação existente.

## Ideias adiadas

PWA instalável, notificações, exportação e integrações automáticas; nenhuma necessária ao aceite inicial.

## Implantação confirmada

VM dedicada exclusivamente ao serviço, com 2 GB de RAM e 4 vCPUs. Entrega de implantação em Docker Compose, conforme orientação do usuário.
