# API and protocols

The in-process server is WebSocket-first for query execution and HTTP-first for
documentation, schema discovery, resource metadata and saved views.

Start it with:

```bash
tellm-bot --host localhost --port 8008
```

## HTTP endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Browser chat UI. |
| `GET /docs` | Human-readable API docs served by tellm. |
| `GET /openapi.json` | OpenAPI contract for HTTP/resource endpoints. |
| `GET /asyncapi.json` | AsyncAPI contract for WebSocket messages. |
| `GET /healthz` | Plain health check returning `ok`. |
| `GET /manifest` | Registry manifest. |
| `GET /registry` | Discover registry resources. Supports filters such as `kind`, `tag`, `domain`, `status` and `capability`. |
| `GET /resource?uri=...` | Resource metadata. |
| `GET /resolve?uri=...&include_value=true` | Dereference a URI and optionally include readable value. |
| `GET /schema?uri=...` | Input and output schemas for a resource. |
| `GET /schema/input?uri=...` | Input schema only. |
| `GET /schema/output?uri=...` | Output schema only. |
| `GET /describe?uri=...` | Human-readable resource description. |
| `GET /permissions?uri=...` | Resource permissions. |
| `GET /history?uri=...` | Recent execution history for a resource. |
| `GET /health?uri=...` | Resource health from recent history. |
| `GET /validate-input?uri=...&input={...}` | Validate query-encoded input JSON. |
| `GET /validate-output?uri=...&output={...}` | Validate query-encoded output JSON. |
| `GET /view/{id}` | Saved HTML view. |

`POST /query`, `POST /execute` and `POST /autoimprovement/run` are documented
as target HTTP adapter contracts, but the built-in server cannot read HTTP
request bodies. Use WebSocket messages for execution or add an HTTP adapter.

## WebSocket endpoint

Connect to:

```text
ws://localhost:8008
```

Text query:

```json
{
  "type": "text",
  "text": "Jaka jest pogoda w Wejherowie?",
  "speak": false,
  "logs": []
}
```

Registry execution:

```json
{
  "type": "execute",
  "uri": "tellm://service/weather/current",
  "input": {
    "location": "Wejherowo",
    "country": "POLAND"
  },
  "speak": false
}
```

Audio query:

```json
{
  "type": "audio",
  "audio": "data:audio/webm;base64,...",
  "speak": false
}
```

Transport-only audio test:

```json
{
  "type": "audio",
  "audio": "data:audio/webm;base64,...",
  "test": true,
  "transcription": "Jaka jest pogoda w Warszawie?"
}
```

Cancel active query:

```json
{
  "type": "cancel"
}
```

## WebSocket events

The server emits events such as:

- `state` - busy/idle status;
- `log` - workflow, service, renderer and validation logs;
- `view` - intermediate state or final view with rendered HTML;
- `error` - protocol or execution error.

A final `view` event contains `html`. Intermediate `view` events can contain
only `transcription` and `status`.

## HTTPS and WSS

The built-in server listens as plain HTTP/WS. For HTTPS/WSS, run it behind a
reverse proxy that terminates TLS and forwards WebSocket upgrades to the local
server. The smoke-test script accepts both HTTP and HTTPS targets:

```bash
python scripts/protocol_smoke.py \
  --base-url http://localhost:8008 \
  --https-url https://example.test \
  --wss-url wss://example.test
```

