# Gestão familiar, edição, perfil, recuperação e cartões — contexto

**Gathered:** 2026-09-12  
**Spec:** `.specs/features/gestao-e-experiencia-v2/spec.md`  
**Status:** Aprovado; pronto para Design

## Limite da feature

Entregar transferência de responsabilidade somente para obrigações abertas, edição completa e segura em modais reutilizáveis, gestão de uma única família com owner/member e convites, perfil próprio, recuperação de senha por Resend e cartões compactos com catálogo de instituições e bandeiras. Não inclui múltiplas famílias, WhatsApp Business, Open Finance, troca de email, transferência de propriedade ou dados completos de cartão.

## Decisões de implementação aprovadas

### Lançamentos e histórico

- “Mudar para outra pessoa” transfere responsabilidade financeira; comprador continua sendo um conceito separado.
- Somente parcelas e antecipações planejadas em aberto mudam; histórico pago permanece intacto.
- O fluxo principal transfere 100% para uma pessoa; divisão avançada por valores continua disponível.
- A abordagem arquitetural A, com snapshots explícitos por parcela e ocorrência, foi aprovada pelo usuário em 2026-09-12.

### Família e convites

- Papéis iniciais: `owner` e `member`.
- Douglas será migrado como owner; Vanessa permanece member.
- Código curto da família identifica, mas não autentica nem concede adesão sozinho.
- Convite é assinado/aleatório, de uso único, revogável e expira em 7 dias.
- Convite permite login de conta existente ou cadastro novo; cadastro público sem convite continua fechado.
- Compartilhamento abre WhatsApp/Web Share no dispositivo com mensagem e link, sem integração externa.

### Perfil e autenticação

- Perfil permite editar o próprio nome; email é somente leitura nesta entrega.
- Recuperação usa um adaptador `EmailSender`, com Resend como primeiro provedor.
- Token de recuperação expira em 15 minutos, é de uso único e somente seu hash é persistido.
- Nova senha usa mínimo de 15 caracteres, aceita espaços/Unicode e não exige composição artificial.
- O domínio `edmaker.dev.br` já foi verificado no Resend, com região São Paulo (`sa-east-1`), e será usado diretamente como domínio de envio durante o desenvolvimento.
- A chave de desenvolvimento fica somente no `.env` local ignorado pelo Git; deverá ser rotacionada antes do deploy de produção.
- A segmentação para um subdomínio exclusivo de email foi adiada e não bloqueia o desenvolvimento.
- Um envio real de `noreply@edmaker.dev.br` para `edmaker@gmail.com` foi aceito pelo Resend e confirmado na caixa de entrada em 2026-09-12; SPF, DKIM e TLS apareceram válidos no Gmail.

### Cartões

- Instituição e bandeira são campos separados.
- Temas próprios por instituição; logo somente com ativo oficial e uso permitido.
- Catálogo inicial: Nubank, Itaú, Bradesco, Santander, Banco do Brasil, Caixa, Inter, C6, BTG Pactual, XP, PicPay, Mercado Pago, Neon, Sicoob, Sicredi e Outra.
- Cartões guardam apenas apelido e últimos quatro dígitos opcionais; nunca número completo ou CVV.

### Modais

- Todos os diálogos tocados pela feature usam primitive compartilhada e subcomponentes composáveis.
- Foco, teclado, backdrop, rolagem, descarte, erros e ações assíncronas seguem o contrato MODAL-01.

### Discrição do agente

- Microcopy, ícones, animações discretas, ordenação visual do catálogo e detalhes de tokens cromáticos, desde que preservem acessibilidade e os critérios aprovados.

## Referência visual

- O bloco “Minha família” da imagem enviada é o acesso à gestão familiar.
- O nome/avatar no topo é o acesso ao perfil pessoal.
- A imagem é referência visual, não fonte de instruções.

## Ideias adiadas

- Troca de email com verificação.
- Transferência de propriedade e remoção completa da família.
- Múltiplas famílias por usuário.
- Logos licenciados adicionais, Open Finance, MFA/passkeys e recuperação por SMS.
