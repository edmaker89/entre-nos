# Evidências por tarefa

## T3 — migração

Gate: alembic upgrade head, alembic check, pytest: 2 passed; lint/importação passaram.

| AC / resultado esperado | Evidência | Cobertura |
| --- | --- | --- |
| FAM-01 AC02: sem contexto não lê dados | tests/integration/test_schema.py:14 — assert ...all() == [] | Sim |
| FAM-01 AC02: família a somente ca | tests/integration/test_schema.py:16 — assert ...scalars().all() == ['ca'] | Sim |
| FAM-01 AC02: outra família não altera cb | tests/integration/test_schema.py:17 — assert ...all() == [] | Sim |
| T3: vínculo externo negado | tests/integration/test_schema.py:24 — pytest.raises(IntegrityError) | Sim |

Mapa reverso: todas as asserções acima pertencem a FAM-01 AC02/constraint T3; nenhuma testa requisito externo. Adequação: resultados de leitura/escrita e falha real de constraint, sem mocks. T1/T2 são configuração/schema e usaram gate de lint/importação, sem testes de comportamento exigidos.
