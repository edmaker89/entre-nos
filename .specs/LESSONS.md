# LESSONS — auto-maintained by scripts/lessons.py

> Machine-owned. Do NOT hand-edit. Changes are overwritten on the next `lessons.py` write.
> Canonical state lives in `.specs/lessons.json`. Edit lessons only via the script.
> promote_threshold=2 distinct features · window_days=45 · quarantine_threshold=2

## Confirmed (load these at Specify/Design)

Corroborated across multiple features. Safe to apply as guidance.

_none_

## Candidates (under observation — do NOT load as guidance yet)

Seen once or not yet corroborated. Tracked, not trusted.

### L-001 — Teste rejeição de antecipação de parcela paga pela rota financeira e confirme ausência de mudança persistida.
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `backend/advances` · harmful: 0
- features: controle-familiar
- evidence: M4 (backend/advances)
- last seen: 2026-09-10T21:53:29Z

### L-002 — Teste os limites inferior e superior dos valores de antecipação e confirme os valores persistidos.
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `backend/advances` · harmful: 0
- features: controle-familiar
- evidence: M5 (backend/advances)
- last seen: 2026-09-10T21:53:29Z

### L-003 — Conserve a chave da operação na interface até confirmar a resposta ou mudar o conteúdo.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `frontend` · harmful: 0
- features: controle-familiar
- evidence: DATA-01 AC04 (frontend)
- last seen: 2026-09-10T21:53:29Z

### L-004 — Injete falhas SQL no caminho HTTP real e verifique rollback e logs sanitizados correlacionados à resposta.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `backend/api` · harmful: 0
- features: controle-familiar
- evidence: DATA-01 AC05 (backend/api)
- last seen: 2026-09-10T21:53:29Z

### L-005 — Ao editar períodos antigos recalcule estimativas a partir do último valor confirmado anterior a cada período.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `backend/recurrences` · harmful: 0
- features: controle-familiar
- evidence: BILL-01 AC02 (backend/recurrences)
- last seen: 2026-09-10T21:53:29Z

### L-006 — Mantenha a competência escolhida acima de componentes desmontados pela navegação.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `frontend` · harmful: 0
- features: controle-familiar
- evidence: MONTH-01 AC01 (frontend)
- last seen: 2026-09-10T21:53:29Z

### L-007 — Verifique textos de competência e avisos de pendências com datas controladas.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `frontend` · harmful: 0
- features: controle-familiar
- evidence: MONTH-01 AC07 (frontend)
- last seen: 2026-09-10T21:53:29Z

### L-008 — Verifique a identificação de parcelas finais na projeção renderizada.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `frontend` · harmful: 0
- features: controle-familiar
- evidence: MONTH-01 AC06 (frontend)
- last seen: 2026-09-10T21:53:29Z

### L-009 — Verifique os detalhes históricos de antecipação após salvar e recarregar a página.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `frontend` · harmful: 0
- features: controle-familiar
- evidence: ADV-01 AC01 (frontend)
- last seen: 2026-09-10T21:53:29Z

### L-010 — Exponha diferenças de rateio no erro de validação do formulário sem registrar dados financeiros no log.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `backend/api` · harmful: 0
- features: controle-familiar
- evidence: SPLIT-01 AC04 (backend/api)
- last seen: 2026-09-10T21:53:29Z

### L-011 — Teste cada resultado composto do critério na camada que o usuário realmente executa, incluindo persistência e falhas.
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `acceptance-tests` · harmful: 0
- features: controle-familiar
- evidence: FAM-01 AC01 (acceptance-tests) (+29 more)
- last seen: 2026-09-10T21:53:30Z

## Quarantined (failed when applied — ignore)

A confirmed lesson that recurred alongside failure. Kept for the maintainer to review.

_none_
