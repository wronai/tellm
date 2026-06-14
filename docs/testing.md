# Testing

## Unit tests

Run:

```bash
python -m pytest -q
```

The suite covers imports, SQLite persistence, task execution, HTML escaping,
registry services, workflow status separation, weather provider behavior,
autoimprovement findings and server protocol helpers.

## Live weather smoke test

This checks the real Open-Meteo provider and country normalization:

```bash
python - <<'PY'
import asyncio
from tellm import create_bot

bot = create_bot(db_path="/tmp/tellm-weather-smoke.db")
result = asyncio.run(
    bot.execute_resource(
        "tellm://service/weather/current",
        {"location": "Wejherowo", "country": "POLAND"},
    )
)
print(result["ok"])
print(result.get("data", {}).get("city"))
print(result.get("data", {}).get("country"))
print(result.get("errors"))
PY
```

Expected result:

```text
True
Wejherowo
PL
[]
```

## Generated audio fixtures

Generate local audio files for text/audio protocol tests:

```bash
python scripts/generate_test_audio.py
```

The script writes files under `output/test-audio/` and a manifest at
`output/test-audio/manifest.json`. It requires `espeak-ng` and `ffmpeg`.

Generated formats:

- `wav`
- `webm`
- `ogg`
- `mp3`
- `m4a`

## Protocol smoke tests

Start the server:

```bash
tellm-bot --host localhost --port 8008
```

Run text/audio/HTTP checks:

```bash
python scripts/protocol_smoke.py --base-url http://localhost:8008
```

The script checks:

- `GET /`
- `GET /docs`
- `GET /healthz`
- WebSocket text transport
- WebSocket audio transport
- generated WebRTC browser smoke page

Use real STT instead of transport-only audio mode:

```bash
python scripts/protocol_smoke.py \
  --base-url http://localhost:8008 \
  --real-stt
```

## Browser WebRTC smoke page

`scripts/protocol_smoke.py` writes a browser recorder to:

```text
output/protocol-tests/webrtc-recorder-smoke.html
```

Open it in a browser, grant microphone permission and send a short recording to
the WebSocket server.

## HTTPS/WSS

The built-in server is HTTP/WS. For HTTPS and WSS, put it behind a TLS reverse
proxy and pass those URLs to the smoke script:

```bash
python scripts/protocol_smoke.py \
  --base-url http://localhost:8008 \
  --https-url https://tellm.example.test \
  --wss-url wss://tellm.example.test \
  --insecure
```

