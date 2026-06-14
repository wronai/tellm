# Registry and URI resources

tellm treats stable URIs as the public API between the LLM, local services,
renderers, tests and future adapters.

## URI examples

| URI | Kind | Purpose |
| --- | --- | --- |
| `tellm://service/weather/current` | service | Current weather via Open-Meteo. |
| `tellm://service/price/search` | service | Visible product prices from supported commerce sources. |
| `tellm://service/domain/check` | service | Domain/DNS/RDAP style checks. |
| `tellm://service/system/autoimprove` | service | Autoimprovement audit. |
| `tellm://schema/...` | schema | Input/output schemas. |
| `tellm://view/...` | view | Rendered view resources. |
| `tellm://artifact/...` | artifact | Files and generated artifacts. |

## Why URI routing matters

For domain tasks, the LLM should choose an existing URI instead of generating a
new function per input value.

Good:

```json
{
  "function_name": "tellm://service/weather/current",
  "parameters": {
    "location": "Wejherowo",
    "country": "PL"
  },
  "processes": []
}
```

Bad:

```json
{
  "function_name": "weather_wejherowo",
  "processes": [
    {
      "language": "python",
      "code": "def run(params): ..."
    }
  ]
}
```

Stable URIs give the system one schema, one permission model, one provider
adapter, one renderer contract and one history stream per capability.

Price questions must route to `tellm://service/price/search`, not to
`tellm://service/domain/check`. A domain check can only answer whether a domain
exists; it cannot answer product price questions.

## Dereferencing

Resource metadata:

```bash
curl "http://localhost:8008/resource?uri=tellm://service/weather/current"
```

Resolve a resource:

```bash
curl "http://localhost:8008/resolve?uri=tellm://service/weather/current"
```

Resolve with readable value when allowed:

```bash
curl "http://localhost:8008/resolve?uri=tellm://artifact/audio/weather-query-sample&include_value=true"
```

## Aliases

Aliases live in `tellm/registry/aliases.yaml`. They let older or friendlier
URIs point to canonical resources without breaking shared links. Alias
resolution should preserve diagnostics, including the requested URI, canonical
URI and route warnings.

## Service result envelope

Registry services return a common result shape:

```json
{
  "ok": false,
  "uri": "tellm://service/weather/current",
  "type": "weather.current.result",
  "data": null,
  "message": {
    "title": "Nie udało się pobrać pogody",
    "summary": "Usługa pogodowa nie zwróciła realnych danych.",
    "details": "Skonfiguruj provider albo sprawdź input."
  },
  "errors": [
    {
      "code": "LOCATION_NOT_FOUND",
      "source": "tellm://service/weather/current",
      "detail": "Location not found: Wejherowo",
      "provider": "open_meteo_geocoding",
      "query": {
        "name": "Wejherowo",
        "country": "POLAND",
        "normalized_country": "PL"
      },
      "attempts": [],
      "recoverable": true
    }
  ],
  "warnings": [],
  "render": {
    "renderer": "auto",
    "template": "status_card",
    "severity": "error"
  }
}
```

Errors should use stable object fields, not free-form strings, so
autoimprovement can aggregate failure patterns.
