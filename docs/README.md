# tellm documentation

This directory is the project documentation entry point. Runtime API docs are
also available from a running server at `http://localhost:8008/docs`.

## Guides

- [Getting started](getting-started.md) - installation, configuration, CLI,
  browser UI and Python usage.
- [Architecture](architecture.md) - main modules, data flow, persistence and
  status model.
- [API and protocols](api.md) - HTTP endpoints, WebSocket messages, speech
  transport and generated OpenAPI/AsyncAPI documents.
- [Registry and URI resources](registry-and-uri.md) - canonical URI contracts,
  aliases, dereferencing and service-result envelopes.
- [Workflow and autoimprovement](workflow-and-autoimprovement.md) - query
  lifecycle, renderer validation, logs, repair loops and audit findings.
- [Testing](testing.md) - pytest, live provider checks, generated audio
  fixtures and protocol smoke tests.

## Runtime entry points

Start the server:

```bash
tellm-bot --host localhost --port 8008
```

Then open:

- `http://localhost:8008/` - browser chat UI with text input, dictation and
  theme switcher.
- `http://localhost:8008/docs` - interactive API reference.
- `http://localhost:8008/openapi.json` - HTTP contract.
- `http://localhost:8008/asyncapi.json` - WebSocket contract.
- `ws://localhost:8008` - WebSocket transport.

