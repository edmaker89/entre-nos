#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
umask 077
mkdir -p backups
output="backups/expense-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose exec -T db pg_dump -U expense_owner -d expense -Fc > "$output"
printf 'Backup criado em %s. Copie para armazenamento externo à VM.\n' "$output"
