# SEC Monitor MVP

A minimal, quiet SEC monitoring pipeline that defaults to silence and only escalates high-signal events.

## Scope

- Primary sources: Form 4 and Form 8-K.
- For foreign issuers like BABA, report CLI can include Form 6-K (`--forms 4,8-K,6-K`).
- Goal: reduce noise and surface rare, interrupt-worthy events.

## Pipeline

```text
[SEC API] -> [Fetcher] -> [Rule Filter] -> [Agent Judge] -> [Notifier]
```

## Quick start (mock)

```bash
python run_mvp.py --ticker BABA
```

## Real SEC data + report

```bash
python generate_report.py --ticker BABA --days 30 --forms 4,8-K,6-K --out reports/baba_report.md
```

Notes:
- SEC requests should include a valid User-Agent. Set `SEC_USER_AGENT` (app name + email).
- `RealSecFetcher` now supports fallback CIK mapping for BABA if ticker lookup endpoint is unavailable.
- Current real-data MVP keeps Form 4 transaction fields as unknown until XML transaction parsing is added.

## Output policy

- `high` => immediate push (`interrupt`)
- `medium` => daily summary (`digest`)
- `low` => drop silently (`silent`)

## Next integration points

- Parse Form 4 XML to extract amount, insider role, and 10b5-1 flag.
- Parse 8-K / 6-K filing body to infer event subtype and framework mapping.
- Replace heuristic judge with Claude API using the same strict JSON schema.
- Wire route outputs to Feishu webhook.
