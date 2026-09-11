# Validação: contraste dos botões dos cartões

- Resultado: **PASS**.
- Data: 2026-09-11.
- Verificador: subagente independente, diferente do autor.
- Spec: `spec.md` nesta pasta.
- Diff: `28d6266c9e8dee95708c1b84aa51ada608a6d95b..22f9f840429f9b93badc75e91ab4c1a53890e1aa`.

## Evidência por critério

| Critério | Evidência e verificação | Resultado |
| --- | --- | --- |
| Conteúdo legível nos cartões claro e escuro | `frontend/src/pages/Cards.tsx:13` aplica `payment-card` aos dois fundos alternados. Chrome/Playwright independente, DOM descartável com CSS real completo, verificou texto e stroke SVG com `assert(ratio >= 4.5)` | PASS |
| Normal e hover com contraste mínimo 4,5:1 | `frontend/src/styles.css:5` e `:6`; 9,37:1 normal e 10,51:1 hover nos quatro botões (Editar e Ver faturas de cada fundo) | PASS |
| Desktop e celular | Mesmo ensaio em 390 e 1440 px: 16 combinações aprovadas. O gate existente `frontend/card-qa.mjs:13`–`:20` também compara cores computadas com o limite definido pela spec | PASS |
| Escopo local, sem mudança financeira | Diff inspecionado integralmente: apenas classe do artigo e duas regras CSS, além da spec. Seletores limitados a `.payment-card button`; handlers permanecem idênticos | PASS |

O autor registrou inspeção da página autenticada e screenshots em `artifacts/cards-390.png` e `artifacts/cards-1440.png`. O verificador reproduziu independentemente as medições usando Chrome em uma página estática descartável; não acessou credenciais nem gravou dados. O ícone foi medido pelo `stroke` computado do SVG com `currentColor`, além do texto pelo `color` computado.

## Gate e sensor

- `cd frontend && npm run build`: exit 0; TypeScript e Vite aprovados, 1749 módulos transformados.
- Sensor proporcional: remover somente as duas regras `.payment-card` da CSSOM descartável restaura branco sobre branco no cartão escuro. Medição: **1,00:1**, abaixo de 4,5:1; a condição de aceitação rejeita a mutação. 1 mutação morta, 0 sobreviventes. A árvore real não foi modificada pelo sensor.
- Nenhum teste permanente alterado; nenhuma suíte financeira ou seed executados. Sem alterações de banco.
- Mudança mínima, padrões existentes preservados, nenhuma lacuna encontrada. Nenhuma lição de falha a registrar.
