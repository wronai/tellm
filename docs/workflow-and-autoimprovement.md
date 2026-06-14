# Workflow and autoimprovement

The workflow is designed to make LLM output auditable. The LLM is not the final
source of truth for execution; it routes and validates, while local services
execute through registry contracts.

## Query lifecycle

```text
query usera
-> LLM answer as task JSON
-> registry service or Python process execution
-> service result JSON
-> renderer HTML
-> function and renderer logs
-> LLM validates result and render
-> LLM returns OK or repaired data
-> workflow saves view and execution history
```

While a query is active, the browser UI blocks sending another query. The user
can interrupt the active work with `cancel`.

## Logs

The server emits structured logs through WebSocket:

- `query` - accepted user query;
- `llm_answer` - routing and task JSON;
- `registry` or `functions` - local execution;
- `service_result` - business result of a registry service;
- `renderer` - HTML render status;
- `llm_validation` - validation and repair loop;
- `local_validation` - schema-valid trusted registry result confirmed without
  an LLM call;
- `workflow` - final workflow status.

The browser shows these logs and can include prior client logs when sending the
next query.

## Statuses

Workflow status and service status are intentionally separate.

| Layer | Example | Meaning |
| --- | --- | --- |
| Workflow | `completed` | Technical pipeline completed. |
| Workflow | `completed_with_service_error` | Pipeline completed, but the service result has `ok=false`. |
| Service result | `ok` | Domain task succeeded. |
| Service result | `failed` | Domain task failed with a structured error. |

This avoids misleading labels such as `functions / ok` when the actual service
returned `ok=false`.

## Repair loop

Renderer validation sends the task, result, render data, HTML and logs back to
the LLM. The LLM can respond with:

- `OK` when the rendered result is valid;
- repaired data/view when schema or render diagnostics show a problem.

The workflow repeats until the result is valid or the configured limit is
reached.

Trusted registry services may skip the LLM repair loop when the result is
schema-valid, the renderer succeeded and data-source diagnostics are clean. This
applies both to successful results and structured service errors such as
`LOCATION_TOO_BROAD`.

## Autoimprovement findings

`tellm://service/system/autoimprove` audits registry schemas and execution
history. It detects recurring patterns such as:

- missing schema metadata;
- renderer failures;
- repair loops;
- simulated data used for real-world queries;
- missing real data providers;
- ad-hoc functions generated for known domains;
- provider location resolution failures.

Example finding:

```json
{
  "severity": "warning",
  "type": "provider_location_resolution_failed",
  "uri": "tellm://service/weather/current",
  "recommendation": "Dodać normalizację country do ISO-3166 alpha-2, fallback geocoding bez kraju oraz cache znanych lokalizacji."
}
```

Run it through Python:

```python
import asyncio
from tellm import create_bot

bot = create_bot(db_path="tellm.db")
result = asyncio.run(
    bot.execute_resource(
        "tellm://service/system/autoimprove",
        {"dry_run": True, "allow_auto_apply": False},
    )
)
print(result["data"]["summary"])
```
