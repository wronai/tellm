# Getting started

## Install

From a source checkout:

```bash
python -m pip install -e .
```

From an extracted release archive:

```bash
tar -xzf tellm-4.0.5.tar.gz
cd tellm-4.0.5
python -m pip install -e .
```

## Configure

Create `.env` in the project directory:

```bash
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=openrouter/qwen/qwen3-coder-next
```

`OPENROUTER_API_KEY` is required for LLM routing and validation. Local registry
services such as `tellm://service/weather/current` can still be executed
directly when they do not need an LLM decision.

## Run the server

```bash
tellm-bot --host localhost --port 8008 --db tellm.db
```

Open:

- `http://localhost:8008/` for the browser UI.
- `http://localhost:8008/docs` for REST and WebSocket documentation.
- `ws://localhost:8008` for WebSocket clients.

The browser UI supports typed queries, browser speech recognition when
available, log visibility, result sharing via URL query parameters and three
themes: `light`, `warm` and `dark`.

## Python usage

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

print(result["ok"])
print(result["data"]["source"])
```

For full natural-language routing:

```python
import asyncio
from tellm import create_bot

bot = create_bot(db_path="tellm.db")

async def main():
    task = await bot.analyze_query("Jaka jest pogoda w Wejherowie?")
    result = await bot.execute_task(task)
    view = bot.generate_view("Jaka jest pogoda w Wejherowie?", task, result)
    print(view.to_html())

asyncio.run(main())
```

## Useful commands

```bash
python -m pytest -q
python scripts/generate_test_audio.py
python scripts/protocol_smoke.py --base-url http://localhost:8008
```

