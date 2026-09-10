# Entre Nós — controle familiar

React/TypeScript + FastAPI + PostgreSQL, com migrações Alembic. Aplicação web responsiva para compras, faturas, responsabilidades por pessoa, despesas recorrentes e antecipação de parcelas.

## Desenvolvimento

Pré-requisitos: Docker, Python 3.12 com `uv`, Node 22+ e npm.

Banco isolado de desenvolvimento (não use estas credenciais em produção):

```sh
docker run -d --name expense-flow-postgres \
  -e POSTGRES_USER=expense -e POSTGRES_PASSWORD=expense_dev -e POSTGRES_DB=expense \
  -p 127.0.0.1:55432:5432 -v expense-flow-dev-data:/var/lib/postgresql/data postgres:16
cd backend
uv sync --python 3.12
uv run alembic upgrade head
uv run python -m app.cli create-user --email seu-email --name Douglas
# Use o family_id retornado para criar o segundo integrante:
uv run python -m app.cli create-user --email outro-email --name Vanessa --family-id ID
APP_ORIGIN=http://127.0.0.1:5173 uv run uvicorn app.main:app --reload
```

Em outro terminal, na pasta `frontend`:

```sh
npm ci
npm run dev -- --port 5173
```

Abra http://127.0.0.1:5173. Senhas administrativas são solicitadas interativamente. Credenciais e banco de produção são separados do desenvolvimento.

## Testes

Usam o PostgreSQL de desenvolvimento migrado. Os testes de navegador provisionam famílias exclusivas no banco local; nunca apontar testes para produção.

```sh
./scripts/check-backend.sh
cd backend
uv run pytest -q
uv run alembic check
```

Frontend, com API rodando em 8000:

```sh
cd frontend
npm run test:unit
npm run build
npx playwright install chromium
npm run test:e2e
# Alternativa local se Google Chrome estiver instalado:
PW_CHANNEL=chrome npm run test:e2e
```

## Docker Compose na VM

VM dedicada: 2 GB RAM, 4 vCPUs. Três serviços persistentes (`web`, `api`, `db`) e um serviço pontual (`migrate`). Banco sem porta pública, API na rede interna. Limites iniciais: banco 768 MB, API 512 MB, web 128 MB; ajustar após medir carga. Builds ocorrem fora da VM.

1. Copie `.env.example` para `.env`, configure senhas aleatórias diferentes para dono e usuário da API, domínio e origem HTTPS. Senhas usadas nas URLs devem ser alfanuméricas ou corretamente codificadas. Nunca versionar `.env`.
2. Na máquina de build/CI, execute `docker compose build api web`. Se a VM usa outra arquitetura, gere imagens para a arquitetura correta com Buildx antes de transferi-las. Não há deploy remoto configurado.
3. Transfira as imagens (ou use registry), `compose.yaml`, `.env` e `deploy/` para a VM. Configure DNS e portas 80/443. O Caddy emite certificado quando o domínio está válido e alcançável.
4. Execute `docker compose up -d --no-build`. A API aguarda a conclusão bem-sucedida de `alembic upgrade head`.
5. Crie os usuários usando o serviço administrativo:

```sh
docker compose run --rm migrate python -m app.cli create-user --email seu-email --name Douglas
docker compose run --rm migrate python -m app.cli create-user --email outro-email --name Vanessa --family-id ID
```

A API conecta como `expense_runtime`, sem superuser/BYPASSRLS. Migrações e CLI usam `expense_owner`. O init do PostgreSQL cria o papel de runtime somente no primeiro volume vazio; trocar a variável de senha depois não altera automaticamente usuários de um volume existente.

Atualizações: faça backup, carregue as novas imagens, execute `docker compose run --rm migrate alembic upgrade head` e só então recrie API/web. Não executar downgrade destrutivo automaticamente. Sessões têm limite absoluto de 7 dias e expiram após 24 horas sem atividade; logout revoga a sessão e redefinição de senha revoga todas as sessões do usuário.

## Migrações

```sh
cd backend
uv run alembic revision --autogenerate -m "describe change"
# Revise o arquivo gerado, constraints e políticas RLS.
uv run alembic upgrade head
uv run alembic check
```

As migrações são a fonte de criação do banco; não há `create_all` no startup. Atualize `requirements.txt` a partir de `uv.lock` com `uv export --no-dev --format requirements-txt --output-file requirements.txt` quando dependências mudarem.

## Backup e restauração

`./deploy/backup.sh` gera dump em `backups/`, com acesso restrito. Copie o arquivo para armazenamento fora da VM. Frequência inicial recomendada: diário e antes de migrações; destino externo e agenda devem ser configurados na implantação.

Para testar uma restauração sem sobrescrever produção:

```sh
docker compose exec db createdb -U expense_owner expense_restore
cat backups/ARQUIVO.dump | docker compose exec -T db pg_restore -U expense_owner -d expense_restore --exit-on-error
# Confira as tabelas e os totais antes de usar os dados restaurados.
```

O dump depende dos papéis `expense_owner` e `expense_app` existentes; em um servidor novo, provisione-os pelo init do projeto. Volume persistente não substitui cópia externa. O teste `deploy/tests/smoke.py` verifica restauração em banco temporário do Compose isolado de validação.

## Documentação e estado

Especificação, design, tarefas e evidências em `.specs/features/controle-familiar/`. O relatório de verificação final informa o que foi validado e eventuais limitações. Nenhuma integração bancária ou pagamento real é executado: os valores de desconto e pagamentos são informados pelo usuário.
