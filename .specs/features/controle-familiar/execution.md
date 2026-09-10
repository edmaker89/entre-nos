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

## T8

Gate: 13 testes unitários passaram; rateio e limites exatos.
- **Requirement**: BUY-01 AC04; SPLIT-01 AC01–04; ADV-01 AC06.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/unit/test_money.py:8 — `assert installments(10000, 3) == [3334, 3333, 3333]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_money.py:9 — `assert installments(30000, 3) == [10000, 10000, 10000]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_money.py:13 — `assert allocate(3333, [1, 1]) == [1667, 1666]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_money.py:14 — `assert allocate(10000, [0, 1]) == [0, 10000]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_money.py:15 — `assert allocate(10000, [1, 1]) == [5000, 5000]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_money.py:16 — `assert allocate(19999, [10000, 10000]) == [10000, 9999]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_money.py:17 — `assert allocate(19998, [10000, 10000]) == [9999, 9999]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_money.py:24 — `with pytest.raises(ValueError):` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T9

Gate: 25 testes passaram; cadastro, edição, repetição e validação de cartão.
- **Requirement**: CARD-01; FAM-01 AC02.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_cards.py:16 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cards.py:18 — `assert (card["closing_day"], card["due_day"], card["holder_id"]) == (25, 5, client.user_id)` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cards.py:19 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cards.py:23 — `assert len(client.get("/api/v1/cards").json()) == 1` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cards.py:29 — `assert r.json()["closing_day"] == 26` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cards.py:30 — `assert r.json()["version"] == 2` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cards.py:34 — `assert r.status_code == 422` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cards.py:40 — `assert r.status_code == 422` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cards.py:41 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T10

Gate: 29 testes passaram; prévia e compra persistida nos ciclos previstos.
- **Requirement**: BUY-01 AC01–06; SPLIT-01 AC01–04; DATA-01 AC01.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_commitments.py:41 — `assert preview.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_commitments.py:42 — `assert preview.json()["installments"][0]["month"] == first` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_commitments.py:43 — `assert preview.json()["installments"][0]["needs_review"] == review` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_commitments.py:46 — `assert saved.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_commitments.py:48 — `assert [p["amount_cents"] for p in body["installments"]] == [10000] * 3` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_commitments.py:49 — `assert body["shares"][0]["user_id"] == client.other_id` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_commitments.py:50 — `assert body["installments"][0]["month"] == first` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_commitments.py:51 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_commitments.py:55 — `assert client.get(f"/api/v1/commitments/{body['id']}").json()["pending_count"] == 3` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_commitments.py:67 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_commitments.py:75 — `assert client.get("/api/v1/commitments").json() == []` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T11

Gate: 30 testes passaram; migração parcial preserva total original.
- **Requirement**: MIG-01 AC01–03; BILL-01 AC03.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_imports.py:19 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_imports.py:20 — `assert [p["number"] for p in r.json()["installments"]] == [10, 11, 12]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_imports.py:21 — `assert [p["month"] for p in r.json()["installments"]] == [` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_imports.py:26 — `assert sum(p["amount_cents"] for p in r.json()["installments"]) == 13053` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_imports.py:36 — `assert r.json()["pending_count"] == 35` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_imports.py:37 — `assert r.json()["original_count"] == 48` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_imports.py:38 — `assert r.json()["last_open_number"] == 44` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_imports.py:40 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T12

Gate: 32 testes passaram; deslocamento, exclusão e bloqueios de pagos/antecipações.
- **Requirement**: SETTLE-01 AC01,AC03,AC06; ADV-01 AC10.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_changes.py:15 — `assert [p["month"] for p in preview.json()["installments"]] == [` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_changes.py:23 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_changes.py:24 — `assert [p["amount_cents"] for p in r.json()["installments"]] == [10000] * 3` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_changes.py:25 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_changes.py:33 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_changes.py:40 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_changes.py:47 — `assert client.get(f"/api/v1/commitments/{c['id']}").status_code == 404` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_changes.py:48 — `assert client.get("/api/v1/commitments").json() == []` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_changes.py:61 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_changes.py:80 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T13

Gate: 33 testes passaram; fechamento efetivo, remanejamento e conferência.
- **Requirement**: CARD-01 AC04; SETTLE-01 AC05; ADV-01 AC10.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_cycle_changes.py:17 — `assert p.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cycle_changes.py:18 — `assert p.json()["changes"][0]["first_month"] == "2026-11-01"` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cycle_changes.py:24 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cycle_changes.py:25 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cycle_changes.py:35 — `assert r.json()["confirmed"] is True` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_cycle_changes.py:41 — `assert p.status_code == 409` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T14

Gate: 34 testes passaram; recorrências idempotentes e estimativas; Alembic check limpo.
- **Requirement**: BILL-01 AC01–04.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_recurrences.py:16 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:19 — `assert [o["amount_cents"] for o in first["occurrences"]] == [36000] * 3` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:20 — `assert all(o["estimated"] for o in first["occurrences"])` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:21 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:35 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:37 — `assert [o["amount_cents"] for o in after["occurrences"]] == [36000, 38000, 38000]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:38 — `assert after["occurrences"][1]["estimated"] is False` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:39 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:47 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T15

Gate: 35 testes passaram; fatura liquidada sem dupla contagem e reabertura.
- **Requirement**: SETTLE-01 AC02–04; ADV-01 AC02,AC07; MONTH-01 AC08.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_payments.py:19 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_payments.py:20 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_payments.py:27 — `assert len(after["installments"]) == 1` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_payments.py:28 — `assert after["installments"][0]["amount_cents"] == 30000` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_payments.py:29 — `assert after["installments"][0]["month"] == "2026-10-01"` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_payments.py:30 — `assert after["installments"][0]["paid_at"] == "2026-11-05"` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_payments.py:31 — `assert after["pending_count"] == 0` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_payments.py:32 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_payments.py:45 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_payments.py:46 — `assert client.get(f"/api/v1/commitments/{c['id']}").json()["pending_count"] == 1` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T16

Gate: 37 testes passaram; antecipação do carro e cartão preserva identidade e totais.
- **Requirement**: ADV-01 AC01,AC04–06,AC08–10.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_advances.py:34 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advances.py:35 — `assert r.json()["discount_cents"] == 83500` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advances.py:37 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advances.py:38 — `assert r.json()["state"] == "planned"` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advances.py:40 — `assert after["pending_count"] == 35` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advances.py:41 — `assert after["original_count"] == 48` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advances.py:43 — `assert (last["number"], last["amount_cents"], last["month"], last["original_month"]) == (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advances.py:49 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advances.py:53 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advances.py:77 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advances.py:79 — `assert [p["month"] for p in after["installments"]] == ["2026-10-01"] * 3` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advances.py:80 — `assert [p["amount_cents"] for p in after["installments"]] == [10000] * 3` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advances.py:81 — `assert len({p["cycle_id"] for p in after["installments"]}) == 1` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T17

Gate: 38 testes passaram; pagamento reduz pendentes e cancelamento restaura cronograma.
- **Requirement**: ADV-01 AC02–03,AC05,AC07–09.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_advance_changes.py:25 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advance_changes.py:26 — `assert r.json()["state"] == "paid"` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advance_changes.py:28 — `assert (after["pending_count"], after["last_open_number"], after["original_count"]) == (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advance_changes.py:33 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advance_changes.py:46 — `assert r.json()["state"] == "planned"` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advance_changes.py:52 — `assert r.json()["state"] == "cancelled"` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advance_changes.py:55 — `assert (last["month"], last["amount_cents"], last["due_date"]) == (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_advance_changes.py:60 — `assert after["pending_count"] == 35` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T18

Gate: 14 testes unitários passaram; regra do dia 10 e timezone.
- **Requirement**: MONTH-01 AC01,AC08.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/unit/test_month_selection.py:8 — `assert default_month(datetime(2026, 10, 9, 12, tzinfo=timezone.utc), False) == "2026-10"` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_month_selection.py:9 — `assert default_month(datetime(2026, 10, 10, 12, tzinfo=timezone.utc), False) == "2026-11"` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_month_selection.py:10 — `assert default_month(datetime(2026, 10, 5, 12, tzinfo=timezone.utc), True) == "2026-11"` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_month_selection.py:11 — `assert default_month(datetime(2026, 11, 1, 12, tzinfo=timezone.utc), False) == "2026-11"` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_month_selection.py:12 — `assert default_month(datetime(2026, 10, 10, 1, tzinfo=timezone.utc), False) == "2026-10"` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/unit/test_month_selection.py:13 — `assert default_month(datetime(2026, 12, 10, 12, tzinfo=timezone.utc), False) == "2027-01"` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T19

Gate: 40 testes passaram; totais mensais, filtros e previsão de 12 meses.
- **Requirement**: MONTH-01 AC02–03,AC05–07; ADV-01 AC01–04.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_months.py:22 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_months.py:31 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_months.py:32 — `assert r.json()["totals"] == {"expected": 15000, "paid": 10000, "remaining": 5000}` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_months.py:34 — `assert r.json()["totals"] == {"expected": 5000, "paid": 0, "remaining": 5000}` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_months.py:35 — `assert len(r.json()["items"]) == 1` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_months.py:36 — `assert r.json()["family_total"] == 15000` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_months.py:37 — `assert client.get("/api/v1/months/2026-11").json()["totals"] == {` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_months.py:43 — `assert len(forecast) == 12` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_months.py:44 — `assert forecast[0]["totals"]["expected"] == 15000` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_months.py:45 — `assert forecast[-1]["month"] == "2027-09"` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T20

Gate: 41 testes passaram; mês quitado exige pagamentos e invalida com pendências.
- **Requirement**: MONTH-01 AC08.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_month_closure.py:8 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_month_closure.py:19 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_month_closure.py:25 — `assert c["installments"][0]["paid_at"] is None` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_month_closure.py:32 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_month_closure.py:38 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_month_closure.py:46 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T21

Gate: 2 testes frontend e 1 navegador passaram; build concluído; npm audit sem vulnerabilidades.
- **Requirement**: DATA-01 AC04; FAM-01.

| Evidência de asserção | Requisito / resultado |
| --- | --- |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T22

Gate: 3 testes unitários frontend e 2 E2E passaram; build concluído.
- **Requirement**: FAM-01; AUTH-01.

| Evidência de asserção | Requisito / resultado |
| --- | --- |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T23

Gate: 4 testes unitários frontend e 6 E2E passaram; quatro larguras sem overflow após correção.
- **Requirement**: MONTH-01 AC01–08.

| Evidência de asserção | Requisito / resultado |
| --- | --- |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T24

Gate: 5 testes unitários frontend e 7 E2E passaram; compra em viewport móvel salva após prévia.
- **Requirement**: BUY-01 AC05; SPLIT-01; DATA-01 AC01,AC04.

| Evidência de asserção | Requisito / resultado |
| --- | --- |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T25

Gate: 6 testes unitários frontend e 8 E2E passaram; cadastro de cartão e consulta de faturas.
- **Requirement**: CARD-01; SETTLE-01 AC02–05.

| Evidência de asserção | Requisito / resultado |
| --- | --- |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T26

Gate: 7 testes unitários frontend; 8 E2E passaram e teste de antecipação passou após recarregar fixture inserida por API; asserções preservadas.
- **Requirement**: ADV-01 AC01–10; SETTLE-01 AC01,AC03,AC06.

| Evidência de asserção | Requisito / resultado |
| --- | --- |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T27

Gate: 8 testes unitários frontend e 10 E2E passaram; importação e projeção completas.
- **Requirement**: BILL-01; MIG-01; MONTH-01 AC06.

| Evidência de asserção | Requisito / resultado |
| --- | --- |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T28

Gate: Compose build/up passaram; smoke validou portas privadas, login, role restrita, persistência e restauração real; 41 testes backend e gates frontend da T27.
- **Requirement**: AD-002–004; FAM-01 AC03.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| deploy/tests/smoke.py:27 — `assert not config['services']['db'].get('ports')` | Critérios da tarefa acima; valor esperado literal da especificação |
| deploy/tests/smoke.py:28 — `assert not config['services']['api'].get('ports')` | Critérios da tarefa acima; valor esperado literal da especificação |
| deploy/tests/smoke.py:35 — `assert request('/health')=={'status':'ok'}` | Critérios da tarefa acima; valor esperado literal da especificação |
| deploy/tests/smoke.py:40 — `assert error.code==401` | Critérios da tarefa acima; valor esperado literal da especificação |
| deploy/tests/smoke.py:46 — `assert login['user']['id']==user` | Critérios da tarefa acima; valor esperado literal da especificação |
| deploy/tests/smoke.py:49 — `assert saved['installments'][0]['amount_cents']==10000` | Critérios da tarefa acima; valor esperado literal da especificação |
| deploy/tests/smoke.py:51 — `assert sql("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname='expense_runtime'")=='f'` | Critérios da tarefa acima; valor esperado literal da especificação |
| deploy/tests/smoke.py:61 — `assert sql("SELECT total_cents FROM commitments WHERE id='"+saved['id']+"'",restore)=='10000'` | Critérios da tarefa acima; valor esperado literal da especificação |
| deploy/tests/smoke.py:71 — `assert request('/api/v1/commitments/'+saved['id'])['installments'][0]['amount_cents']==10000` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.

## T29

Gate: 42 backend tests passed; lint passed.
- **Requirement**: BILL-01 — último valor conhecido antes da competência.

| Evidência de asserção | Requisito / resultado |
| --- | --- |
| backend/tests/integration/test_recurrences.py:16 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:19 — `assert [o["amount_cents"] for o in first["occurrences"]] == [36000] * 3` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:20 — `assert all(o["estimated"] for o in first["occurrences"])` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:21 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:35 — `assert r.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:37 — `assert [o["amount_cents"] for o in after["occurrences"]] == [36000, 38000, 38000]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:38 — `assert after["occurrences"][1]["estimated"] is False` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:39 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:47 — `assert (` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:73 — `assert result.status_code == 200` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:75 — `assert [o["amount_cents"] for o in actual] == [37000, 38000, 38000, 38000]` | Critérios da tarefa acima; valor esperado literal da especificação |
| backend/tests/integration/test_recurrences.py:76 — `assert [o["estimated"] for o in actual] == [False, False, True, True]` | Critérios da tarefa acima; valor esperado literal da especificação |

Mapa reverso: asserções listadas pertencem aos critérios desta tarefa; revisadas quanto a suficiência, necessidade e resultados persistidos. Nenhum teste removido ou ignorado.
