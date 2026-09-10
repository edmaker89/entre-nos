#!/bin/sh
set -eu
cd "$(dirname "$0")/../backend"
uv run ruff check app tests
uv run python -m compileall -q app
uv run python -c 'from app.main import app; assert app.title == "Expense Flow"'
