#!/bin/sh
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -v runtime_password="$APP_DB_PASSWORD" <<'SQL'
CREATE ROLE expense_app NOLOGIN;
SELECT format('CREATE ROLE expense_runtime LOGIN PASSWORD %L', :'runtime_password') \gexec
GRANT expense_app TO expense_runtime;
SQL
