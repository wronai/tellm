# Architecture

tellm is a local assistant runtime with speech input, LLM routing, local
service execution, JSON rendering, SQLite persistence and workflow validation.

## Components

| Component | File | Responsibility |
| --- | --- | --- |
| Bot core | `tellm/bot.py` | STT, TTS, LLM routing, task execution, registry services, HTML view generation and SQLite persistence. |
| Web server | `tellm/server.py` | Browser UI, HTTP resource endpoints, WebSocket chat, logs, renderer validation and workflow history. |
| Registry | `tellm/registry/core.py` | Canonical URI resources, aliases, schemas, permissions, service result envelopes and validation helpers. |
| Autoimprovement | `tellm/improvement/runner.py` | Audits registry schemas, execution history, renderer logs and recurring failure patterns. |
| CLI | `tellm/main.py` | `tellm-bot` entry point. |

## Query flow

```text
user query
-> LLM router
-> Task JSON
-> registry URI or Python process
-> service result JSON
-> dynamic HTML renderer
-> renderer/function logs
-> LLM validation
-> optional repair loop
-> SQLite history and saved view
```

The preferred path is registry execution through a stable URI such as
`tellm://service/weather/current`. Ad-hoc Python process generation remains
available for generic tasks, but domain services should be represented as
registry resources with schemas and permissions.

## Status model

tellm separates technical workflow completion from user-visible business
success.

```json
{
  "execution_status": "completed",
  "service_result_status": "failed",
  "workflow_status": "completed_with_service_error"
}
```

This means a workflow can finish correctly while the service result is still a
domain failure, for example `LOCATION_NOT_FOUND` or
`NETWORK_ACCESS_NOT_ALLOWED`. Schema-valid failures from trusted registry
services can be confirmed locally without an additional LLM validation call.

## Persistence

SQLite stores:

- executed tasks and results;
- rendered HTML views;
- execution history and workflow logs;
- autoimprovement reports.

The database path is configured with `--db` or `create_bot(db_path=...)`.

## Weather service example

`tellm://service/weather/current` uses Open-Meteo as a real provider. It
normalizes country names to ISO-3166 alpha-2 codes, for example `POLAND` to
`PL`, then geocodes with fallback attempts:

```text
name=Wejherowo&countryCode=PL
name=Wejherowo
```

Failures use structured errors with codes and diagnostics, so autoimprovement
can identify provider integration problems instead of treating them as generic
LLM failures.

Country-level locations such as `Polska` are rejected before provider lookup
with `LOCATION_TOO_BROAD`. The service asks for a city or coordinates instead
of returning weather for an arbitrary country centroid.

## Price service example

`tellm://service/price/search` handles questions such as `jaka jest cena cukru
na allegro.pl`. The deterministic router extracts the product and source site,
then the service fetches a supported public search page and parses visible PLN
prices from HTML.

If the source is unsupported, blocked, dynamic-only or contains no visible
price, the service returns a structured error such as `PRICE_SOURCE_UNSUPPORTED`
or `PRICE_NOT_FOUND`. It must not fall back to `domain.check` or generated
Python code for price questions.
