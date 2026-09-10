# Controle familiar — escolha de arquitetura

Spec: spec.md, aprovada em 2026-09-10.
Status: Approved — usuário autorizou continuidade após aceitar sessão por cookie.

## Stack e implantação

- **Decidido pelo usuário:** PostgreSQL diretamente na VM, sem Supabase. Capacidade informada: 2 GB RAM e 4 vCPUs.
- **Preferência explícita:** frontend React e backend separado, sem Next.js; mantenedor especializado em Python.
- **Base confirmada:** React + Vite + TypeScript; FastAPI; Alembic para migrações. SQLAlchemy proposto para acesso ao banco; proxy HTTPS e PostgreSQL na rede privada da VM.
- **Em definição:** autenticação, contratos, esquema relacional e configuração final de produção.

A opção de PostgreSQL direto reduz os serviços necessários em comparação com a plataforma Supabase. Backup externo e restauração devem fazer parte do plano operacional. O frontend será compilado fora da VM de produção e servido como arquivos estáticos. A implantação usará Docker Compose, conforme direcionamento do usuário. A VM é dedicada exclusivamente a este serviço.

O orçamento de memória é a principal restrição conhecida. Ponto de partida proposto: um processo da API e pool pequeno de conexões; ajustar após medir uso real. Não assumir quatro processos porque existem quatro vCPUs. Não há outros serviços na VM; capacidade e limites dos containers serão validados com a aplicação real. Não há necessidade identificada de Redis, filas ou servidor Node para servir o frontend em produção.

## Fluxo arquitetural proposto

Celular/computador → aplicação web autenticada → operações do domínio → PostgreSQL.

O navegador apresenta a prévia, mas o servidor valida e recalcula antes de gravar. A identidade da família é derivada da sessão e da associação do usuário. A compra é a origem; parcelas mantêm identidade e vencimento original; antecipações registram a alteração e seu estado. Relatórios somam a obrigação efetiva uma única vez.

## Invariantes que qualquer alternativa deve preservar

- Valores em centavos inteiros; produtos intermediários de rateio usam aritmética inteira sem perda de precisão.
- Datas civis e competências separadas de timestamps; relógio de abertura usa America/Sao_Paulo.
- Identidade da parcela e total original não mudam ao antecipar.
- Planejamento não equivale a pagamento; cancelamento pode restaurar o cronograma.
- Operações compostas são transacionais e idempotentes, com controle de versão para conflitos.
- Associação à família verificada em todas as leituras e gravações; banco também deve impor isolamento.
- Serviços de domínio testáveis sem navegador; testes de integração exercitam o banco real.

## Estratégia de testes proposta

Testes unitários para cada resultado do domínio; integração para persistência, isolamento, rollback, repetição e concorrência; testes de navegador para os fluxos completos e larguras 360/390/768/1440. Ferramentas propostas: pytest para backend/domínio e integração PostgreSQL; Vitest para frontend e Playwright para navegador. Comandos ainda não definidos, pois não há manifesto nem infraestrutura de testes; serão concretizados no plano de tarefas após a escolha da stack.

## Reuso e pesquisa

A pasta não possui implementação, dependências, testes ou diretrizes de código; apenas os documentos de Specify. Nenhuma base existente a reutilizar. STATE.md foi consultado; não existe armazenamento de lições. Context7 não está disponível nesta sessão, portanto a pesquisa prosseguiu para documentação oficial.

Referências consultadas em 2026-09-10:

- [Next.js: Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components): divisão entre renderização/execução no servidor e interatividade no cliente.
- [Supabase: Database](https://supabase.com/docs/guides/database/overview): PostgreSQL como base relacional.
- [Supabase: Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security): políticas de acesso combinadas com autenticação.
- [Supabase: Securing your data](https://supabase.com/docs/guides/database/secure-data): fronteiras de acesso a dados.

## Risks & Concerns

| Risco | Localização | Mitigação proposta |
| --- | --- | --- |
| Gravar compra e parcelas em requisições independentes causa estado parcial | BUY-01 AC06 / ADV-01 AC09 | Uma transação por operação composta |
| Confiar no family_id recebido do navegador expõe outra família | FAM-01 AC02 | Autorização de sessão mais políticas no banco |
| Contar antecipação como nova compra duplica despesas | ADV-01 AC01–04 | Projeção única por parcela e histórico separado |
| Plano de antecipação aparentar quitação | ADV-01 AC02 | Estado planejado distinto de pago na interface e persistência |
| Mudança automática de mês ocultar contas abertas | MONTH-01 AC01/07/08 | Regra do dia 10, seleção estável e aviso de pendências |
| Integração de infraestrutura ainda não configurada | Projeto novo | Desenvolvimento/testes locais; configurar ambiente compartilhado antes da validação de produção |

## Próxima etapa

Detalhar modelo relacional, componentes, operações e autenticação com PostgreSQL na VM. Nenhuma instalação ou implantação foi executada.

## Alternativas avaliadas

Next.js no backend foi descartado conforme preferência do usuário. Fastify segue tecnicamente viável, mas FastAPI é recomendado pela experiência em Python. Supabase foi avaliado como compatível com ambos, porém PostgreSQL direto foi escolhido pelo usuário considerando a VM de 2 GB.


## Topologia Docker Compose

Formato de implantação confirmado pelo usuário. Três serviços propostos:

- `web`: proxy HTTPS e arquivos compilados do React; encaminha `/api` para a API. Único serviço publicado externamente (HTTP/HTTPS).
- `api`: FastAPI na rede interna, inicialmente com um processo; configuração de banco por segredo de ambiente, sem credenciais na imagem.
- `db`: PostgreSQL na rede interna, sem porta pública e com volume persistente.

Build do frontend e da imagem da API fora da VM de produção. Healthchecks para prontidão, política de reinício e migrações como comando pontual antes de liberar a nova API, sem executá-las em cada worker. Backups devem ter cópia fora da VM e procedimento de restauração; volume Docker preserva dados entre recriações, mas não substitui backup. Domínio, destino do backup e segredos de produção serão configurados na etapa de implantação. Nenhum acesso à VM ou deploy foi realizado.

## Componentes e organização

Monólito modular: uma API e um banco, com frontend separado no mesmo repositório.

| Componente | Localização proposta | Interface e responsabilidade |
| --- | --- | --- |
| Domínio financeiro | `backend/app/domain/` | Funções puras para ciclos, centavos, rateio e projeções; sem FastAPI ou SQLAlchemy |
| Casos de uso | `backend/app/services/` | Cadastro, pagamento, reabertura e antecipação; delimitam transações e validam estados |
| Persistência | `backend/app/db/` | Modelos SQLAlchemy, sessão por requisição e consultas restritas à família |
| API | `backend/app/api/` | Rotas FastAPI, contratos Pydantic, autenticação e tradução de erros |
| Migrações | `backend/alembic/versions/` | Evolução do esquema e políticas de acesso |
| Interface | `frontend/src/` | React/TypeScript; páginas Resumo, Lançamentos, Cartões e Planejamento |
| Operação | `compose.yaml`, `deploy/` | Imagens, proxy, healthchecks, migração pontual e procedimentos de backup/restauração |

Nenhum componente existente a reutilizar. As prévias financeiras vêm da API para evitar implementar duas regras distintas em Python e TypeScript. O frontend formata BRL, coleta os campos e apresenta os resultados; o servidor recalcula ao salvar.

## Modelo relacional proposto

Todas as entidades financeiras têm UUID, family_id, versão inteira, timestamps e, quando cabível, deleted_at. Chaves estrangeiras compostas com family_id impedem relacionamentos entre famílias. Valores são BIGINT em centavos; datas civis usam DATE; competências usam DATE no primeiro dia do mês; timestamps usam timezone.

| Entidade | Campos principais / relação |
| --- | --- |
| users | email normalizado único, nome, password_hash, ativo |
| families / memberships | família e associação de usuário, única por par família/usuário |
| sessions | hash do token opaco, usuário, expiração, revogação |
| cards | família, titular, instituição, nome, dia de fechamento, dia de vencimento |
| invoice_cycles | cartão, fechamento previsto/efetivo, vencimento, competência, conferida, versão; único por cartão/competência |
| commitments | descrição, categoria opcional, comprador, tipo (compra/financiamento/avulsa), data, cartão opcional, total original de parcelas, origem migrada |
| responsibility_shares | compromisso, responsável, peso inteiro e ordem determinística do rateio |
| installments | compromisso, número original, valor original, vencimento/competência original, valor e competência efetivos, ciclo original/efetivo opcional, pago_em, modo de quitação, versão; único por compromisso/número original |
| recurring_rules | descrição, responsáveis, início, fim opcional, vencimento e natureza fixa/variável |
| recurring_occurrences | regra, competência única, valor, estimado, vencimento, pago_em e versão |
| advance_plans / advance_items | plano, destino, valor final; itens vinculados às parcelas e snapshot anterior; estados planejado/pago/cancelado |
| month_closures | família, competência, sinalizado_em, sinalizado_por; sinal invalidado por nova pendência |
| idempotency_records | família, chave, tipo de operação, hash do conteúdo, resultado; único por família/chave |
| audit_events | ator, operação, entidade, data e mudanças necessárias à restauração; dados internos, sem expor no log operacional |
| login_attempt_windows | origem normalizada, janela de 60 s e contador atômico para limite de login |

Parcelas migradas não criam histórico fictício: intervalos importados produzem somente obrigações conhecidas. O contador de pendentes soma parcelas abertas conhecidas; o contrato preserva o total original e informa que o histórico anterior não foi importado.

Recorrências são materializadas para o intervalo consultado (até 12 meses por consulta), com unicidade regra/competência e inserção idempotente. Mudança de estimativa aplica-se à competência escolhida e às futuras ainda estimadas e abertas, nunca às confirmadas ou pagas. Encerramento atua sobre ocorrências materializadas e o limite da regra.

## Autenticação proposta

Login por email e senha com hash Argon2 por biblioteca mantida; sessão opaca aleatória armazenada no navegador somente em cookie HttpOnly, Secure em produção e SameSite=Lax. Banco guarda somente o hash do token; validade proposta de 7 dias, revogação no logout e na redefinição de senha. Origem validada e token CSRF exigido nas mutações; respostas autenticadas não recebem cache público.

Primeiro casal cadastrado por comando administrativo na implantação; sem cadastro público, serviço de email ou recuperação automática no MVP. Redefinição administrativa por comando que solicita senha sem registrá-la no histórico do shell. Isso permite o acesso de duas pessoas sem introduzir infraestrutura de email; esse comportamento é proposta técnica para confirmação no Design.

Autorização verifica associação à família em cada requisição; família recebida não é confiada sem essa verificação. Sessão SQL recebe contexto de família com SET LOCAL dentro da transação; tabelas financeiras têm RLS forçada, usuário da API não é proprietário, superusuário nem BYPASSRLS. Papel de migração separado. Políticas e privilégios são gerenciados por Alembic. Consultas de sessão/associação têm fronteira própria antes da definição do contexto financeiro.

## Contratos da API

Prefixo `/api/v1`. Datas ISO, competências YYYY-MM, dinheiro em centavos inteiros. Respostas de erro: `{code, message, fields?, operation_id}`; sem detalhes internos. 401 para sessão ausente/expirada; 404 para recurso ausente ou de outra família; 409 para conflito de versão/estado/idempotência; 422 para validação; 429 para limite de login; 503 para indisponibilidade temporária de banco.

| Área | Operações |
| --- | --- |
| Sessão | POST /auth/login, POST /auth/logout, GET /auth/me, GET /auth/csrf |
| Cartões | GET/POST /cards; PATCH /cards/{id} |
| Ciclos | GET /cards/{id}/cycles; POST /cycles/{id}/preview-close; PATCH /cycles/{id}/close; POST /cycles/{id}/confirm |
| Compras e contratos | POST /commitments/preview; POST /commitments; GET /commitments/{id}; PATCH /commitments/{id}; DELETE /commitments/{id} |
| Migração manual | POST /commitments/import-preview; POST /commitments/import |
| Competência | POST /commitments/{id}/preview-shift; POST /commitments/{id}/shift |
| Recorrências | GET/POST /recurrences; PATCH /recurrences/{id}; PATCH /occurrences/{id}; POST /recurrences/{id}/end |
| Pagamentos | POST /invoices/{id}/pay e /reopen; POST /installments/{id}/pay e /reopen; POST /occurrences/{id}/pay e /reopen |
| Antecipação | POST /advances/preview; POST /advances; POST /advances/{id}/pay, /reopen e /cancel |
| Painel | GET /months/{month}; GET /forecast?from=YYYY-MM&months=12; POST /months/{month}/close |

Gravações financeiras exigem Idempotency-Key; edições exigem versão esperada. Prévia informa efeitos sem gravar; confirmação revalida todos os estados. Antecipação no cartão não aceita pagamento isolado: o endpoint de pagamento orienta pagar a fatura destino. Endpoint de edição de cartão altera padrões futuros; não reescreve silenciosamente ciclos existentes.

## Transações e conflitos

Uma Session SQLAlchemy por requisição, nunca compartilhada entre requisições. Proposta inicial síncrona com psycopg e endpoints `def` para manter o acesso bloqueante fora do event loop; regras puras executam dentro dos casos de uso. Uma transação por mutação composta.

Inicialmente, serializar mutações financeiras por família com bloqueio da linha da família e validar versões após adquirir o bloqueio. Para duas pessoas, isso simplifica consistência de faturas, parcelas e sinal de mês quitado. Todas as mutações seguem a mesma ordem: família → compromisso/ciclo → parcelas ordenadas por ID. Requisição repetida consulta a chave e retorna resultado já confirmado; chave com payload diferente produz conflito.

Não gravar valores derivados por caminhos independentes. Pagamento de fatura opera sobre suas parcelas; não cria nova despesa. Antecipação mantém snapshot para restauração e altera as obrigações efetivas; não duplica linhas financeiras.

## Migrações Alembic

- Alembic é a única via de criação/evolução do esquema, inclusive em testes de integração; não usar create_all como substituto.
- Revisões versionadas no repositório; autogenerate produz rascunho revisado, incluindo verificação manual de constraints, índices, dados e políticas RLS.
- Deploy executa `alembic upgrade head` como etapa pontual com papel de migração, após banco pronto e antes da nova API. Falha interrompe a atualização.
- CI aplica todas as revisões em PostgreSQL vazio e roda `alembic check`; testa também upgrades com dados representativos quando uma mudança afeta dados existentes.
- Cada revisão documenta reversibilidade. Não executar downgrade destrutivo automaticamente; recuperação depende de migração corretiva ou restauração testada.
- Uma única head no fluxo normal; conflitos de branches de migração resolvidos explicitamente antes da entrega.

Fontes: [Alembic autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) e [SQLAlchemy Session](https://docs.sqlalchemy.org/en/20/orm/session_basics.html).

## Experiência e verificação

Resumo mensal com mês/ano destacado, total familiar, parte por pessoa, previsto/pago/restante, aviso de pendências do mês corrente e seletor manual estável. Desktop usa tabela; celular usa lista em cartões com botões de pelo menos 44 px. Formulário de compra e de antecipação mostram prévia exata antes da confirmação. Tela de contrato mostra total original, parcelas pendentes, última aberta e histórico de antecipações.

Backend: pytest, testes unitários ancorados nos exemplos da spec e integração com PostgreSQL real para transações/RLS/concorrência/migração. Frontend: Vitest para comportamento isolado e Playwright para fluxos completos nos quatro tamanhos de viewport. Verificador independente ao fim de Execute conforme skill. Comandos serão materializados e validados na fase Tasks/Execute, não são gates já executados.

## Pontos de aprovação do desenho

Stack, VM dedicada, Compose e Alembic estão confirmados. A proposta detalhada acrescenta sessão por cookie, provisionamento administrativo inicial dos dois usuários, SQLAlchemy síncrono e autorização por família com RLS. Não há implementação, dependências instaladas ou testes executados nesta fase.

Autenticação por sessão opaca aceita pelo usuário. Prazo absoluto proposto de 7 dias e expiração por 24 horas de inatividade, ambos impostos no servidor; atividade não estende o prazo absoluto. Prazos são parâmetros do produto, não garantias gerais de segurança.
