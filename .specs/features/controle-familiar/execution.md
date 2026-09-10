# Evidências por tarefa

## T3 — migração

Gate: alembic upgrade head, alembic check, pytest: 2 passed; lint/importação passaram.

| AC / resultado esperado | Evidência | Cobertura |
| --- | --- | --- |
| FAM-01 AC02: sem contexto não lê dados | tests/integration/test_schema.py:11 — assert ...all() == [] | Sim |
| FAM-01 AC02: família a somente ca | tests/integration/test_schema.py:13 — assert ...scalars().all() == ['ca'] | Sim |
| FAM-01 AC02: outra família não altera cb | tests/integration/test_schema.py:14 — assert ...all() == [] | Sim |
| T3: vínculo externo negado | tests/integration/test_schema.py:21 — pytest.raises(IntegrityError) | Sim |

Mapa reverso: todas as asserções acima pertencem a FAM-01 AC02/constraint T3; nenhuma testa requisito externo. Adequação: resultados de leitura/escrita e falha real de constraint, sem mocks. T1/T2 são configuração/schema e usaram gate de lint/importação, sem testes de comportamento exigidos.

## T4

Gate: 5 testes passaram; rollback, repetição, concorrência e log verificados.
- **Requirement**: DATA-01 AC02–05; BUY-01 AC06; ADV-01 AC09.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_uow.py:21 — `with pytest.raises(RuntimeError):` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:26 — `assert s.scalars(select(MonthClosure)).all() == []` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:27 — `assert mutate(s, family, 'key', {'amount':10000}, lambda: change(s)) == {'amount_cents':10000}` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:29 — `assert mutate(s, family, 'key', {'amount':10000}, lambda: change(s)) == {'amount_cents':10000}` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:30 — `assert len(s.scalars(select(MonthClosure)).all()) == 1` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:31 — `with pytest.raises(AppError, match='conteúdo diferente'):` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:51 — `assert sorted(pool.map(lambda _:update(),range(2))) == ['conflict','saved']` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:54 — `assert (row.version,row.closed) == (2,False)` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:59 — `with pytest.raises(AppError) as error:` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:62 — `assert error.value.status == 404` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:67 — `with pytest.raises(AppError) as error:` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:70 — `assert error.value.status == 503` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:71 — `assert 'database_error operation_id=' in caplog.text` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_uow.py:72 — `assert 'secret-financial-value' not in caplog.text` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T5

Gate: 10 testes passaram; cookies, CSRF, expiração, logout e rate limit.
- **Requirement**: FAM-01 AC01–03; AUTH-01.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_auth.py:34 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:35 — `assert "HttpOnly" in r.headers["set-cookie"]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:36 — `assert "SameSite=lax" in r.headers["set-cookie"]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:37 — `assert c.get("/api/v1/auth/me").json()["user"]["id"] == user` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:38 — `assert c.post("/api/v1/auth/logout").status_code == 403` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:40 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:46 — `assert c.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:47 — `assert c.get("/api/v1/auth/me").status_code == 401` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:57 — `assert row.token_hash != cookie` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:58 — `assert len(row.token_hash) == 64` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:60 — `assert c.get("/api/v1/auth/me").status_code == 401` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:66 — `assert c.get("/api/v1/auth/me").status_code == 401` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:72 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:78 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:95 — `assert "Secure" in response.headers["set-cookie"]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:100 — `assert c.get("/api/v1/auth/me").status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:103 — `assert row.created_at == created` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:104 — `assert now() - row.last_seen < timedelta(seconds=10)` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_auth.py:117 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T6

Gate: 11 testes passaram; provisionamento e redefinição com revogação.
- **Requirement**: FAM-01; AUTH-01.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_cli.py:17 — `assert s.get(User, user).email == email` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cli.py:18 — `assert s.get(Membership, (family, user)) is not None` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cli.py:20 — `with pytest.raises(ValueError, match="cadastrado"):` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cli.py:24 — `assert passwords.verify(s.get(User, user).password_hash, "another-password") is True` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cli.py:25 — `assert all(` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cli.py:31 — `assert second_family == family` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cli.py:32 — `assert second_user != user` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T7

Gate: 16 testes passaram; fechamento e ano/meses curtos; Alembic check limpo.
- **Requirement**: CARD-01 AC01–03; BUY-01 AC01–03.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/unit/test_cycles.py:14 — `assert cycle["month"] == month` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_cycles.py:15 — `assert cycle["needs_review"] == review` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_cycles.py:16 — `assert cycle["due_date"] == date(month.year, month.month, 5)` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_cycles.py:21 — `assert cycle["closing_date"] == date(2027, 2, 28)` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_cycles.py:22 — `assert cycle["due_date"] == date(2027, 3, 5)` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_cycles.py:23 — `assert add_months(date(2026, 12, 1), 1) == date(2027, 1, 1)` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_cycles.py:24 — `assert month_start(date(2026, 10, 15)) == date(2026, 10, 1)` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_cycles.py:29 — `assert cycle["closing_date"] == date(2026, 9, 5)` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_cycles.py:30 — `assert cycle["due_date"] == date(2026, 10, 5)` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.
