# tellm v4 - STT+TTS+LLM+SQLite+HTML


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-4.0.6-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.64-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-3.6h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.6429 (5 commits)
- 👤 **Human dev:** ~$363 (3.6h @ $100/h, 30min dedup)

Generated on 2026-06-14 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

## Dokumentacja

Pełna dokumentacja projektu jest w [docs/](docs/README.md):

- [Getting started](docs/getting-started.md) - instalacja, konfiguracja, CLI, UI i użycie z Pythona.
- [Architecture](docs/architecture.md) - moduły, przepływ danych, statusy workflow i persistence.
- [API and protocols](docs/api.md) - HTTP, WebSocket, speech/WebRTC, OpenAPI i AsyncAPI.
- [Registry and URI resources](docs/registry-and-uri.md) - kontrakty `tellm://...`, aliasy, dereferencja i service result envelope.
- [Workflow and autoimprovement](docs/workflow-and-autoimprovement.md) - logi, walidacja renderu, repair loop i findingi.
- [Testing](docs/testing.md) - pytest, audio fixtures, smoke testy protokołów i live provider checks.

Po uruchomieniu serwera dokumentacja runtime jest dostępna pod `http://localhost:8008/docs`.

## Instalacja
```bash
tar -xzf tellm-4.0.5.tar.gz
cd tellm-4.0.5
pip install -e .
```

## Uruchomienie
```bash
cp .env.example .env
# ustaw OPENROUTER_API_KEY w .env
tellm-bot --host localhost --port 8008
```

## Endpointy

- Browser UI: `http://localhost:8008/`
- API docs: `http://localhost:8008/docs`
- OpenAPI: `http://localhost:8008/openapi.json`
- AsyncAPI: `http://localhost:8008/asyncapi.json`
- WebSocket: `ws://localhost:8008`

## Użycie
```python
import asyncio
from tellm import create_bot

bot = create_bot(db_path="tellm.db")

result = asyncio.run(
    bot.execute_resource(
        "tellm://service/weather/current",
        {"location": "Wejherowo", "country": "POLAND"},
    )
)
print(result["ok"], result.get("data", {}).get("source"))
```


## License

Licensed under Apache-2.0.
