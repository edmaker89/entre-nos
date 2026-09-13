# Gestão familiar, edição, perfil, recuperação e cartões — especificação

**Status:** Em implementação — Fases 1–4 concluídas; próxima fase: recuperação de senha
**Data:** 2026-09-12  
**Complexidade:** complexa; somente Specify nesta etapa. Design, Tasks e Execute dependem da aprovação deste documento.

## Problema

A primeira versão já permite que Douglas e Vanessa usem a mesma família, registrem despesas e acompanhem cartões, mas a administração e a manutenção diária ficaram incompletas. Não existe uma área de gestão da família ou de perfil; a edição de lançamentos usa diálogos nativos do navegador e altera apenas poucos campos; a recuperação de senha ainda é administrativa; e os cartões não têm densidade, proporção ou identidade visual próximas de um cartão real.

O objetivo desta evolução é tornar essas rotinas seguras e fáceis sem reescrever histórico pago, expor dados de cartão sensíveis ou acoplar o produto permanentemente a um fornecedor externo.

## Evidências do estado atual

| Área | Estado encontrado | Gap |
| --- | --- | --- |
| Lançamentos | `Commitment` separa comprador (`buyer_id`) de responsáveis (`responsibility_shares`) | `PATCH /commitments/{id}` altera somente descrição; trocar responsável hoje exigiria alterar dados de forma retroativa |
| Parcelas | Responsabilidade está armazenada no compromisso, não por parcela/período | Alterar o responsável atual mudaria também a leitura de parcelas pagas; é necessária representação temporal ou snapshot por obrigação |
| Modais | Existem várias estruturas `.dialog` duplicadas e `window.prompt`/`window.confirm` em lançamentos e cartões | Falta um componente compartilhado com foco, teclado, confirmação, erros e composição padronizados |
| Família | Existem `families` e `memberships`, sem papel, criador, convite ou código gerenciável | Não é possível distinguir proprietário de membro nem convidar/remover com segurança |
| Perfil | `/auth/me` retorna apenas id e nome; o topo só oferece logout | Nome não é editável e email/perfil não têm tela própria |
| Senha | Login e sessões opacas existem; recuperação é feita pela CLI | Falta fluxo de solicitação, email, token expirável e redefinição self-service |
| Cartões | Instituição é texto livre; o card visual alterna duas cores por posição | Falta catálogo, bandeira, tema estável e proporção realista |

## Objetivos

- Permitir transferir rapidamente a responsabilidade das parcelas em aberto sem alterar valores já pagos.
- Substituir prompts/confirms do navegador por um sistema de modal acessível e reutilizável.
- Criar uma área de gestão da família no bloco “Minha família” da navegação.
- Transformar o nome no topo em acesso ao perfil do usuário.
- Permitir convite compartilhável por WhatsApp, sem integração com a conta do WhatsApp.
- Implementar recuperação de senha por email com token de uso único e expiração de 15 minutos.
- Melhorar densidade, proporção, cadastro e identidade visual dos cartões.

## Fora de escopo

| Item | Motivo |
| --- | --- |
| Integração com API do WhatsApp Business ou leitura de contatos | O compartilhamento será iniciado no dispositivo por link/mecanismo nativo |
| Importação automática de bancos, Open Finance ou faturas | Não é necessária para os ajustes solicitados |
| Armazenar número completo, validade ou CVV do cartão | Evita dados sensíveis e escopo PCI desnecessário |
| Copiar arte completa de cartões físicos ou raspar logos de terceiros | Risco de marca/licença e manutenção; a primeira entrega usa temas próprios inspirados nas cores institucionais |
| Múltiplas famílias por usuário ou alternância entre famílias | A autenticação atual escolhe uma única associação; requer produto e navegação próprios |
| MFA/passkeys | Pode ser uma evolução de segurança, mas não é requisito deste pacote |
| Recuperação por SMS | Introduziria outro fornecedor e custo |
| Troca/transferência de proprietário e dissolução da família | Fluxos destrutivos e de disputa ficam para uma evolução específica |

## Decisões aprovadas

As decisões D01–D12 foram aprovadas pelo usuário em 2026-09-12; D11 recebeu Neon antes da aprovação final.

| ID | Decisão | Padrão recomendado | Motivo | Confirmada? |
| --- | --- | --- | --- | --- |
| D01 | O que significa “mudar para outra pessoa” | Transferir a **responsabilidade financeira**; o campo “quem comprou” permanece separado e pode ser editado em ação própria | Evita confundir autoria da compra com quem paga | Sim |
| D02 | Alcance da transferência | Aplicar somente a parcelas/obrigações abertas, inclusive antecipações apenas planejadas; parcelas pagas preservam o responsável histórico | É o comportamento explicitamente pedido e evita reescrever histórico | Sim |
| D03 | Divisão ao transferir | Atalho principal “Transferir 100% para…”; edição avançada permite divisão por valores entre membros | Mantém o caso comum em poucos toques sem perder o recurso de divisão existente | Sim |
| D04 | Papéis familiares | `owner` e `member`; Douglas será migrado como owner da família atual | É suficiente para convite e gestão sem criar uma matriz de permissões prematura | Sim |
| D05 | Código da família | Código curto, estável e rotacionável serve como identificação, **não concede entrada sozinho**; adesão exige convite assinado de uso único | Código permanente como credencial seria fácil de vazar ou adivinhar | Sim |
| D06 | Validade do convite | 7 dias, uso único, revogável pelo owner; novo envio gera novo convite | Dá tempo para compartilhar por WhatsApp sem criar acesso permanente | Sim |
| D07 | Perfil nesta entrega | Editar nome; exibir email como somente leitura. Troca de email exige verificação e fica para uma próxima feature | Evita trocar a identidade de login sem confirmar o novo endereço | Sim |
| D08 | Serviço de email | Adaptador próprio `EmailSender` com Resend como primeiro provedor | Resend tem API Python/HTTP simples e plano gratuito compatível; adaptador evita lock-in | Sim |
| D09 | Política de nova senha | Mínimo 15 caracteres, máximo ≥64, aceitar espaços/Unicode, sem regra obrigatória de maiúscula/número/símbolo | Alinha a autenticação de fator único às recomendações atuais do NIST | Sim |
| D10 | Aparência dos cartões | Tema próprio por instituição + bandeira separada; logos somente se houver ativo oficial com uso permitido | Instituição (Nubank/Itaú) e bandeira (Visa/Mastercard/Elo) são conceitos diferentes | Sim |
| D11 | Catálogo inicial | Nubank, Itaú, Bradesco, Santander, Banco do Brasil, Caixa, Inter, C6, BTG Pactual, XP, PicPay, Mercado Pago, Neon, Sicoob, Sicredi e “Outra” | Cobertura prática inicial, com escape para qualquer instituição | Sim |
| D12 | Cadastro por convite | Link válido permite criar uma conta nova ou entrar com conta existente; não haverá cadastro público fora de convite | Preserva o modelo familiar fechado | Sim |

**Questões abertas:** nenhuma.

## Histórias e critérios de aceitação

### P1 — EDIT-01: Transferir responsabilidade das parcelas abertas

**História:** Como integrante, quero mover uma despesa lançada para a pessoa correta sem corrigir parcela por parcela.

1. WHEN o usuário abre um lançamento parcelado e escolhe “Transferir responsabilidade” THEN o sistema SHALL mostrar o responsável atual, a pessoa de destino, a quantidade de parcelas abertas afetadas e os meses envolvidos antes de salvar.
2. WHEN confirma a transferência de Douglas para Vanessa THEN o sistema SHALL atribuir 100% de cada parcela aberta a Vanessa e manter intactos responsável, valor e pagamento de cada parcela paga.
3. WHEN o lançamento possui divisão entre pessoas THEN o sistema SHALL oferecer “Transferir 100%” como atalho e “Editar divisão” para valores que somem exatamente a obrigação aberta.
4. WHEN existe uma antecipação planejada e não paga vinculada às parcelas selecionadas THEN o sistema SHALL atualizar sua responsabilidade junto com as demais obrigações abertas e mostrá-la na prévia.
5. WHEN existe pagamento ou antecipação paga THEN o sistema SHALL preservá-lo no histórico, mesmo que o compromisso ainda tenha parcelas abertas transferíveis.
6. WHEN outro integrante altera o lançamento entre a prévia e a confirmação THEN o sistema SHALL rejeitar com conflito de versão e solicitar recarregamento, sem aplicar parte da mudança.
7. WHEN a transferência é confirmada THEN o sistema SHALL salvar todas as alterações em uma transação e atualizar resumo, lançamentos e planejamento sem duplicar valores.

**Teste independente:** compra de 4 parcelas, 2 pagas por Douglas e 2 abertas; transferir para Vanessa e conferir histórico e projeção.

### P1 — EDIT-02: Editar lançamento em modal completo

**História:** Como integrante, quero corrigir um lançamento em uma interface clara e previsível.

1. WHEN abre “Editar lançamento” THEN o sistema SHALL usar modal do produto, pré-preencher os campos e não chamar `window.alert`, `window.prompt` ou `window.confirm`.
2. WHEN nenhuma obrigação está paga THEN o sistema SHALL permitir editar descrição, categoria, comprador, responsáveis, data, forma de pagamento/cartão, valor total, quantidade de parcelas e primeira competência aplicável, sempre com prévia do cronograma antes de confirmar.
3. WHEN há qualquer obrigação paga THEN o sistema SHALL permitir descrição/categoria e a transferência apenas das obrigações abertas; campos que recalculariam o contrato SHALL ficar bloqueados com explicação e ação de reabertura quando aplicável.
4. WHEN a edição recalcula parcelas, faturas ou competências THEN a prévia SHALL mostrar antes/depois, valores, meses e avisos de faturas afetadas.
5. WHEN o usuário cancela ou fecha o modal com alterações não salvas THEN o sistema SHALL pedir confirmação dentro do sistema antes de descartar.
6. WHEN a validação falha THEN o sistema SHALL manter os dados digitados, destacar os campos e apresentar mensagem acionável.
7. WHEN a edição é confirmada THEN o sistema SHALL persistir tudo ou nada e registrar evento de auditoria com ator e campos alterados.

**Teste independente:** editar uma compra não paga e outra parcialmente paga; conferir campos permitidos, bloqueados e totais.

### P1 — MODAL-01: Sistema de modal reutilizável

**História:** Como usuário, quero diálogos consistentes, acessíveis e confortáveis no celular.

1. WHEN qualquer fluxo desta feature abre um modal THEN o sistema SHALL compô-lo a partir de um componente compartilhado, com `Modal`, `ModalHeader`, `ModalBody`, `ModalFooter`, `ModalClose`, formulário/erro e confirmação reutilizáveis.
2. WHEN abre o modal THEN o foco SHALL ir para o título ou primeiro controle útil; Tab/Shift+Tab SHALL permanecer dentro dele; Escape SHALL fechar quando a ação não for destrutiva; ao fechar, o foco SHALL voltar ao acionador.
3. WHEN o modal está aberto THEN o fundo SHALL ficar inacessível à navegação e a rolagem da página SHALL ser bloqueada sem impedir a rolagem interna.
4. WHEN usado a 360, 390, 768 ou 1440 px THEN o modal SHALL caber na viewport, ter ações alcançáveis e não causar rolagem horizontal.
5. WHEN uma ação está em andamento THEN os botões que poderiam duplicá-la SHALL ficar desabilitados e o estado SHALL ser anunciado de forma acessível.
6. WHEN houver confirmação destrutiva THEN o sistema SHALL usar um subcomponente de confirmação com texto específico sobre o impacto, nunca um prompt nativo.

**Teste independente:** abrir, navegar por teclado, fechar e restaurar foco em três fluxos diferentes.

### P1 — FAMILY-01: Gerir a família

**História:** Como criador da família, quero ver integrantes, código e convites em um único lugar.

1. WHEN o usuário seleciona o bloco “Minha família” na navegação THEN o sistema SHALL abrir a área de gestão familiar, preservando a navegação responsiva no celular.
2. WHEN a área abre THEN o sistema SHALL exibir nome da família, código, owner, integrantes ativos, convites pendentes e papéis.
3. WHEN a família atual existente é migrada THEN Douglas SHALL ser owner e Vanessa SHALL continuar membro, sem alteração de dados financeiros.
4. WHEN um member acessa a área THEN o sistema SHALL permitir visualizar integrantes e dados não sensíveis, mas SHALL ocultar/desabilitar ações exclusivas do owner com explicação.
5. WHEN o owner renomeia a família THEN o sistema SHALL atualizar o nome exibido após confirmação e validar 1–100 caracteres.
6. WHEN o owner tenta remover a si próprio THEN o sistema SHALL bloquear, pois transferência de propriedade está fora desta entrega.
7. WHEN um usuário ou família diferente tenta consultar/alterar a gestão THEN o sistema SHALL responder sem revelar os dados da família alvo.

**Teste independente:** sessões de Douglas, Vanessa e uma terceira família verificam permissões e isolamento.

### P1 — INVITE-01: Convidar e compartilhar por WhatsApp

**História:** Como owner, quero enviar um convite pelo WhatsApp sem configurar uma integração externa.

1. WHEN o owner cria um convite THEN o sistema SHALL gerar token aleatório, armazenar apenas seu hash, definir expiração de 7 dias e mostrar link baseado em `PUBLIC_APP_URL` configurável.
2. WHEN seleciona “Enviar pelo WhatsApp” THEN o sistema SHALL abrir o compartilhamento do dispositivo/WhatsApp com mensagem pronta contendo nome da família e link, sem enviar nada silenciosamente nem acessar contatos.
3. WHEN WhatsApp não pode ser aberto THEN o sistema SHALL oferecer copiar link e compartilhar pelo mecanismo nativo do navegador quando disponível.
4. WHEN a aplicação usa localhost THEN o sistema SHALL avisar que o link só funciona no mesmo dispositivo/ambiente; após deploy SHALL usar o domínio público configurado, sem alteração de código.
5. WHEN um convidado abre link válido THEN o sistema SHALL permitir entrar com conta existente ou criar conta e, após autenticação, aderir exatamente à família do convite.
6. WHEN o token já foi usado, revogado ou expirou THEN o sistema SHALL recusar a adesão com mensagem clara e opção de pedir novo convite.
7. WHEN duas solicitações tentam consumir o mesmo convite THEN somente uma SHALL criar a associação; a outra SHALL receber estado de convite já usado.
8. WHEN o owner revoga ou renova um convite THEN o token anterior SHALL deixar de conceder entrada imediatamente.

**Teste independente:** compartilhar link, criar terceiro usuário, consumir uma vez e validar expiração/revogação/concorrência.

### P1 — PROFILE-01: Perfil do usuário

**História:** Como usuário, quero acessar e corrigir meus dados pelo meu nome no topo.

1. WHEN seleciona o nome/avatar no topo THEN o sistema SHALL abrir o perfil do usuário autenticado.
2. WHEN edita o nome válido THEN o sistema SHALL atualizar o topo, integrantes, seletores e lançamentos sem alterar sua identidade interna.
3. WHEN visualiza o email THEN o sistema SHALL mostrá-lo como somente leitura nesta entrega e explicar que é o email de acesso.
4. WHEN outro usuário tenta editar o perfil THEN o sistema SHALL permitir alterar somente o próprio perfil.

**Teste independente:** Vanessa altera o próprio nome; Douglas vê o novo nome na família e não consegue editar o perfil dela.

### P1 — AUTH-RESET-01: Recuperar senha por email

**História:** Como usuário sem acesso à senha, quero redefini-la por um link temporário enviado ao meu email.

1. WHEN informa qualquer email em “Esqueci minha senha” THEN o sistema SHALL responder com a mesma mensagem e comportamento observável, exista ou não uma conta.
2. WHEN existe usuário ativo e o limite não foi excedido THEN o sistema SHALL gerar token criptograficamente aleatório, armazenar somente o hash, enviar link HTTPS e expirar em 15 minutos.
3. WHEN o link válido é usado com uma nova senha aceita THEN o sistema SHALL atualizar o hash Argon2, marcar o token como usado e revogar todas as sessões e tokens de recuperação do usuário na mesma transação.
4. WHEN o token foi usado, expirou ou não existe THEN o sistema SHALL recusar sem revelar detalhes internos e permitir solicitar outro.
5. WHEN duas redefinições usam o mesmo token simultaneamente THEN somente uma SHALL ter sucesso.
6. WHEN há mais de 3 solicitações por email ou 10 por origem em uma hora THEN o sistema SHALL limitar novas emissões, mantendo resposta pública genérica e registro operacional sem token/email completo.
7. WHEN o provedor de email falha THEN o sistema SHALL não expor a falha ao solicitante, registrar `operation_id` e permitir nova tentativa controlada; nenhum token SHALL aparecer em logs.
8. WHEN a nova senha é informada THEN o sistema SHALL aceitar 15–200 caracteres, espaços e Unicode, sem regra de composição, e SHALL rejeitar valor idêntico à senha atual.
9. WHEN a página de redefinição carrega THEN o sistema SHALL evitar vazamento do token por referrer e remover o token da URL/histórico após validá-lo.

**Teste independente:** entrega simulada, token válido, expirado, reutilizado, concorrente e email inexistente, verificando revogação de sessões.

### P1 — CARD-UX-01: Cartões compactos e proporcionais

**História:** Como usuário, quero reconhecer meus cartões rapidamente sem que dominem a tela.

1. WHEN a lista é exibida THEN cada cartão SHALL usar proporção 85,60:53,98 (aprox. 1,586:1), largura máxima compacta e grade responsiva, sem tentar reproduzir tamanho físico em pixels.
2. WHEN exibido em desktop THEN a grade SHALL acomodar mais cartões por linha conforme espaço; em 360/390 px SHALL usar largura disponível sem corte ou rolagem horizontal.
3. WHEN o cartão é renderizado THEN SHALL exibir apelido, instituição, titular, final opcional de 4 dígitos, bandeira, fechamento e vencimento com contraste WCAG AA.
4. WHEN existem muitos cartões THEN ações secundárias SHALL permanecer discretas e acessíveis por teclado/toque, sem aumentar a altura do cartão.

**Teste independente:** catálogo com 1, 4 e 12 cartões nas quatro viewports.

### P1 — CARD-CATALOG-01: Instituições, bandeiras e tema visual

**História:** Como usuário, quero escolher uma instituição conhecida ou cadastrar outra e ver um cartão reconhecível.

1. WHEN cria/edita cartão THEN o sistema SHALL oferecer instituição pesquisável do catálogo e a opção “Outra instituição”.
2. WHEN escolhe “Outra instituição” THEN o sistema SHALL solicitar nome válido e permitir tema genérico; a instituição personalizada SHALL permanecer selecionável naquele cartão sem alterar o catálogo global.
3. WHEN cadastra um cartão THEN o sistema SHALL solicitar bandeira opcional entre Visa, Mastercard, Elo, American Express, Hipercard e Outra/Não informar.
4. WHEN escolhe instituição catalogada THEN o sistema SHALL aplicar um tema estável por chave da instituição, e não pela posição do cartão na lista.
5. WHEN a instituição muda THEN o sistema SHALL atualizar a prévia do tema antes de salvar.
6. WHEN um ativo de marca não tiver permissão verificável THEN o sistema SHALL usar texto e tema cromático próprio, sem hotlink, scraping ou cópia do cartão real.
7. WHEN qualquer tema é aplicado THEN nome, botões e estados de foco SHALL manter contraste e leitura acessível.
8. WHEN o usuário informa identificação do cartão THEN o sistema SHALL aceitar apenas apelido e últimos 4 dígitos opcionais; SHALL rejeitar tentativa de armazenar número completo ou CVV.

**Teste independente:** Nubank/Visa, Itaú/Mastercard e instituição personalizada, incluindo contraste e persistência.

## Casos de borda transversais

- WHEN um membro é removido futuramente mas possui histórico financeiro THEN o sistema SHALL preservar a identidade histórica; remoção completa não faz parte desta entrega.
- WHEN o owner cria convites repetidamente THEN o sistema SHALL impedir spam por limite e permitir revogar convites pendentes.
- WHEN `PUBLIC_APP_URL` ou credenciais de email não estão configurados em produção THEN a checagem de prontidão/deploy SHALL falhar claramente; a aplicação não deve gerar links localhost silenciosamente.
- WHEN o serviço de email está indisponível THEN login e uso financeiro existentes SHALL continuar funcionando.
- WHEN a edição afeta ciclo já conferido mas não pago THEN a prévia SHALL sinalizar e a confirmação SHALL reabrir a conferência do ciclo afetado.
- WHEN um modal é empilhado THEN o sistema SHALL evitar dois diálogos interativos simultâneos; confirmação interna substitui o conteúdo ou usa uma camada controlada.
- WHEN nomes de instituição personalizados contêm HTML ou URLs THEN o sistema SHALL tratá-los como texto e limitar tamanho.

## Sweep de requisitos implícitos

| Dimensão | Tratamento nesta spec |
| --- | --- |
| Validação e limites | Definidos para perfil, família, senha, convite, cartão e divisão |
| Falha/estado parcial | Edições, adesão, redefinição e revogação são transacionais; email falho é registrado sem expor enumeração |
| Idempotência/retry/duplicidade | Mutação financeira mantém Idempotency-Key; convite/token são uso único; envio usa chave idempotente no provedor quando disponível |
| Autorização/rate limit | Owner/member, próprio perfil, isolamento por família e limites de convite/recuperação |
| Concorrência/ordenação | Versão em edição e consumo atômico de convite/reset |
| Ciclo de vida/expiração | Reset 15 min; convite 7 dias; ambos revogáveis/uso único; expiração limpa por rotina periódica ou consulta |
| Observabilidade | `operation_id`, eventos de auditoria e logs sem tokens, senha, email completo ou dados de cartão |
| Dependência externa | Adaptador de email; falha não derruba autenticação existente; compartilhamento possui fallback de cópia |
| Integridade de estados | Pago não reescrito; planejado ≠ pago; owner não pode se remover; convites e resets têm transições explícitas |

## Riscos e melhorias técnicas

| Risco/gap | Impacto | Direção recomendada para Design |
| --- | --- | --- |
| Responsabilidade no nível do compromisso | Transferência seria retroativa | Criar atribuição por parcela/ocorrência ou histórico com vigência; migrar os pesos atuais como snapshot inicial |
| `Membership` sem papel/created_at | Owner não pode ser inferido genericamente | Migração explícita da família atual com Douglas como owner; novos owners definidos na criação |
| API escolhe a primeira família do usuário | Convites podem criar ambiguidade futura | Bloquear adesão se usuário já pertence a outra família enquanto múltiplas famílias estiverem fora de escopo |
| Prompts espalhados em componentes grandes | Fluxos difíceis de testar e manter | Extrair primitive de modal e modais de domínio pequenos; remover todos os prompts dos arquivos tocados |
| Instituição em texto livre | Renomear quebraria tema | Persistir `institution_key` estável e `institution_name`; temas no frontend por chave |
| Confusão entre banco e bandeira | Identidade incorreta | Modelar `institution_key/custom_name` e `network` separadamente |
| Uso de marcas de terceiros | Risco jurídico e de atualização | Primeira versão sem logos copiados; avaliar kits oficiais/licença separadamente |
| Token em URL | Pode vazar em logs/referrer/histórico | Hash no banco, HTTPS, Referrer-Policy, troca rápida por estado efêmero e limpeza da URL |
| Resend requer domínio verificado | Localhost não entrega para terceiros | Mock/sink nos testes; produção só habilita após DNS; subdomínio dedicado recomendado |
| Não há política de senha no cadastro atual | Regras divergentes | Centralizar `PasswordPolicy` e aplicá-la a convite, reset e futuros cadastros |

## Rastreabilidade

| Requisito | Prioridade | Estado |
| --- | --- | --- |
| EDIT-01 | P1 | Backend T1/T2/T6/T8–T11 concluído; interface T14/T16/T19 pendente |
| EDIT-02 | P1 | Backend T6/T8/T12/T13 concluído; interface T15/T16/T19 pendente |
| MODAL-01 | P1 | Em implementação; primitive T7 concluído |
| FAMILY-01 | P1 | Concluído em T1/T3/T20/T21/T25; backend, autorização e interface verificados |
| INVITE-01 | P1 | Concluído em T1/T3/T4/T22/T23/T26; hash-only, uso único, concorrência e compartilhamento verificados |
| PROFILE-01 | P1 | Concluído em T1/T3/T24/T25; perfil próprio e propagação visual verificados |
| AUTH-RESET-01 | P1 | Em implementação; fundação T1/T4/T5 concluída |
| CARD-UX-01 | P1 | Planejada; começa na Fase 6 |
| CARD-CATALOG-01 | P1 | Em implementação; esquema T1 concluído |

**Cobertura:** 9 requisitos, todos mapeados; 0 sem tratamento.

## Critérios de sucesso

- Um lançamento com parcelas pagas e abertas pode ser transferido em menos de 1 minuto, preservando o histórico pago e os totais familiares.
- Nenhum fluxo tocado por esta feature usa diálogo nativo do navegador.
- Douglas consegue visualizar e gerir a família; Vanessa vê a família com permissões de membro.
- Um convite pode ser compartilhado e consumido uma única vez sem integração com WhatsApp Business.
- Uma senha pode ser redefinida com token de 15 minutos sem permitir enumeração de contas ou reutilização.
- Cartões ficam reconhecíveis por instituição/bandeira, compactos, proporcionais e legíveis em 360–1440 px.
- Testes unitários, integração PostgreSQL, frontend e Playwright derivados dos critérios passam antes da entrega.

## Referências técnicas consultadas

- [Resend Pricing](https://resend.com/pricing): plano Free informado em 2026 como 3.000 emails/mês, limite de 100/dia e até 3 domínios.
- [Resend Domains](https://resend.com/docs/dashboard/domains/introduction) e [Send Email API](https://resend.com/docs/api-reference/emails/send-email): envio a terceiros requer domínio próprio verificado; API suporta `Idempotency-Key`.
- [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html): resposta uniforme, token aleatório, seguro, de uso único, expirável e protegido por rate limit.
- [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html): senha de fator único com mínimo de 15 caracteres, máximo aceito de pelo menos 64 e sem regras de composição obrigatórias.
- [ISO/IEC 7810 ID-1](https://www.iso.org/standard/31432.html): proporção física de referência de 85,60 × 53,98 mm; usada apenas como `aspect-ratio` visual.
