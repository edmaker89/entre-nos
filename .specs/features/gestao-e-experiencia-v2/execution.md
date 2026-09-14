# Evidência de execução — Gestão e experiência v2

**Data:** 2026-09-14

**Escopo:** T30–T36

**Banco de validação:** PostgreSQL efêmero em `127.0.0.1:55439`; nenhum banco persistente foi limpo ou migrado.

## Commits atômicos

| Tarefa | Commit | Gate observado |
| --- | --- | --- |
| T30 | `62535de` | Full Backend: 255 testes; lint, compilação e Alembic verdes |
| T31 | `c19b256` | Quick Frontend: 137 testes |
| T32 | `4248ff7` | Quick Frontend: 148 testes; build verde |
| T33 | `a64222c` | Quick Frontend: 158 testes; build verde |
| T34 | `665a0ff` | Full Frontend: 169 unitários, build e 33 E2E |
| T35 | `3c93c39` | 263 backend; Alembic sem operações; Compose build/healthcheck; smoke sem email real |
| T36 | `f8180b5` | Build/System: 263 backend, 169 frontend, build e 42 E2E, sem skip |

## Matriz de aceitação ponta a ponta

`frontend/e2e/experience-v2.spec.ts` contém nove testes, um para cada requisito:

| Requisito | Evidência E2E |
| --- | --- |
| EDIT-01 | prévia transfere somente duas parcelas abertas para Vanessa |
| EDIT-02 | edição completa passa pela prévia antes de salvar |
| MODAL-01 | foco dentro do modal, quatro viewports sem overflow e zero diálogo nativo |
| FAMILY-01 | código, proprietário, integrante e ações de gestão visíveis |
| INVITE-01 | link de uso único e abertura do WhatsApp somente após ação explícita |
| PROFILE-01 | nome atualizado no topo e email somente leitura |
| AUTH-RESET-01 | resposta genérica de recuperação sem revelar existência da conta |
| CARD-UX-01 | grade compacta proporcional com 1, 4 e 12 cartões em 360/390/768/1440 |
| CARD-CATALOG-01 | Neon pesquisável, instituição customizada e ausência de campos PAN/CVV |

## Evidência transversal

- `rg -n "window\\.(alert|prompt|confirm)\\s*\\(" frontend/src` retornou zero ocorrência.
- Full Backend em banco recriado: `263 passed`, sem teste excluído; dois avisos de depreciação de dependências.
- Full Frontend: `20` arquivos e `169 passed`; build TypeScript/Vite verde.
- Playwright completo: `42 passed`, incluindo `9 passed` da matriz v2; nenhum skip.
- Compose descartável: banco e API sem portas públicas, `/ready` validou banco/configuração e o smoke confirmou persistência e restauração de backup.
- Nenhuma chave foi exibida ou versionada; `EMAIL_PROVIDER=memory` impediu envio externo no smoke e nos gates.

## Risco residual conhecido

- Os temas são próprios e inspirados em cores institucionais; não incorporam logos nem arte oficial, reduzindo risco de licença, mas uma revisão de marca ainda é recomendável antes de divulgação pública.
- O build registra avisos de depreciação entre Starlette/TestClient e `httpx`; não afetam os gates atuais, mas devem ser tratados numa atualização controlada de dependências.
