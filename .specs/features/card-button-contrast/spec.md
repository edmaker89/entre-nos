# Contraste dos botões dos cartões

Pedido UAT: texto de Ver faturas e ícone Editar estavam brancos sobre fundo branco.

Correção pequena: limitar estilos explícitos aos botões de .payment-card. Texto e ícone precisam ficar legíveis no cartão escuro e claro, normal e hover, em desktop e celular. Critério observável: contraste mínimo 4,5:1 entre conteúdo e fundo do botão.

Arquivos: Cards.tsx e styles.css. Gate: build frontend + inspeção real no navegador. Sem alteração financeira ou teste automatizado permanente para esta correção visual pontual.

Resultado do autor: build passou, Compose web atualizado; navegador real em390/1440px mediu9,37:1 normal e10,51:1 hover para ambos botões. Screenshot em artifacts/cards-390.png e cards-1440.png. Nenhuma gravação financeira realizada.
