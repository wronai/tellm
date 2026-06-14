#!/usr/bin/env python3
"""Smoke-test tellm HTTP/HTTPS and WebSocket text/audio protocols."""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import mimetypes
import ssl
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

import websockets


DEFAULT_TEXT = "Jaka jest pogoda w Warszawie?"


def ws_url_from_http(base_url: str) -> str:
    parsed = urlparse(base_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return f"{scheme}://{parsed.netloc}"


def get_url(url: str, insecure: bool = False) -> bytes:
    context = ssl._create_unverified_context() if insecure and url.startswith("https") else None
    with urlopen(url, timeout=10, context=context) as response:
        return response.read()


def check_http(base_url: str, insecure: bool = False) -> None:
    checks = {
        "/": b"tellm v4",
        "/docs": b"tellm v4 API docs",
        "/healthz": b"ok",
    }
    for path, needle in checks.items():
        url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        body = get_url(url, insecure=insecure)
        if needle not in body:
            raise SystemExit(f"HTTP check failed for {url}: missing {needle!r}")
        print(f"ok HTTP {url}")


def mime_for_audio(path: Path) -> str:
    if path.suffix == ".m4a":
        return "audio/mp4"
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def audio_data_url(path: Path) -> str:
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_for_audio(path)};base64,{payload}"


def ws_ssl_context(ws_url: str, insecure: bool) -> ssl.SSLContext | None:
    if ws_url.startswith("wss://") and insecure:
        return ssl._create_unverified_context()
    return None


async def send_ws_payload(
    ws_url: str, payload: dict, timeout: float, insecure: bool = False
) -> list[dict]:
    events: list[dict] = []
    ssl_context = ws_ssl_context(ws_url, insecure)
    async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
        await websocket.send(json.dumps(payload, ensure_ascii=False))
        while True:
            raw = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            event = json.loads(raw)
            events.append(event)
            if event.get("type") == "error" or event.get("html"):
                return events


async def check_ws_text(ws_url: str, text: str, timeout: float, insecure: bool) -> None:
    events = await send_ws_payload(
        ws_url,
        {"type": "text", "text": text, "test": True, "speak": False},
        timeout,
        insecure,
    )
    final = events[-1]
    if final.get("type") != "view" or "Protocol test OK" not in final.get("html", ""):
        raise SystemExit(f"WS text check failed: {final}")
    transcription = final.get("data", {}).get("transcription", "")
    print(f"ok WS text {ws_url} transcription={transcription!r}")


async def check_ws_audio(
    ws_url: str,
    audio_path: Path,
    transcription: str,
    real_stt: bool,
    timeout: float,
    insecure: bool,
) -> None:
    payload = {
        "type": "audio",
        "audio": audio_data_url(audio_path),
        "test": True,
        "speak": False,
    }
    if not real_stt:
        payload["transcription"] = transcription

    events = await send_ws_payload(ws_url, payload, timeout, insecure)
    final = events[-1]
    if final.get("type") != "view" or "Protocol test OK" not in final.get("html", ""):
        raise SystemExit(f"WS audio check failed: {final}")
    transcription = final.get("data", {}).get("transcription", "")
    print(f"ok WS audio {ws_url} {audio_path} transcription={transcription!r}")


def write_webrtc_html(path: Path, ws_url: str, transcription: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    html = f"""<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>tellm WebRTC smoke</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 24px; max-width: 760px; }}
    input, button {{ min-height: 36px; font: inherit; }}
    input {{ width: min(100%, 520px); padding: 6px 8px; }}
    pre {{ background: #111827; color: #e5e7eb; padding: 12px; overflow: auto; }}
  </style>
</head>
<body>
  <h1>tellm WebRTC / MediaRecorder smoke</h1>
  <p>Testuje mikrofon w przeglądarce i wysyła <code>audio/webm</code> jako data URL przez WebSocket.</p>
  <label>WebSocket URL<br><input id="ws" value="{ws_url}"></label>
  <p><label><input id="realStt" type="checkbox"> real STT zamiast transport-only test</label></p>
  <button id="record">Nagraj 3.5 s i wyślij</button>
  <pre id="log">Gotowe.</pre>
  <script>
    const log = (value) => {{
      document.getElementById("log").textContent += "\\n" + value;
    }};
    document.getElementById("record").onclick = async () => {{
      const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
      const recorder = new MediaRecorder(stream, {{ mimeType: "audio/webm" }});
      const chunks = [];
      recorder.ondataavailable = (event) => chunks.push(event.data);
      recorder.onstop = () => {{
        const blob = new Blob(chunks, {{ type: recorder.mimeType || "audio/webm" }});
        const reader = new FileReader();
        reader.onloadend = () => {{
          const socket = new WebSocket(document.getElementById("ws").value);
          socket.onopen = () => {{
            const realStt = document.getElementById("realStt").checked;
            const payload = {{
              type: "audio",
              audio: reader.result,
              test: true,
              speak: false
            }};
            if (!realStt) payload.transcription = "{transcription}";
            socket.send(JSON.stringify(payload));
          }};
          socket.onmessage = (event) => log(event.data);
          socket.onerror = () => log("WebSocket error");
        }};
        reader.readAsDataURL(blob);
        stream.getTracks().forEach((track) => track.stop());
      }};
      log("Recording...");
      recorder.start();
      setTimeout(() => recorder.stop(), 3500);
    }};
  </script>
</body>
</html>
"""
    path.write_text(html)


async def async_main(args: argparse.Namespace) -> None:
    ws_targets = []
    for url in (args.ws_url, args.wss_url):
        if url and url not in ws_targets:
            ws_targets.append(url)

    for ws_url in ws_targets:
        if not args.skip_text:
            await check_ws_text(ws_url, args.text, args.timeout, args.insecure)
        if not args.skip_audio:
            await check_ws_audio(
                ws_url,
                args.audio,
                args.transcription,
                args.real_stt,
                args.timeout,
                args.insecure,
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8008")
    parser.add_argument("--https-url", default="")
    parser.add_argument("--ws-url", default="")
    parser.add_argument("--wss-url", default="")
    parser.add_argument("--audio", type=Path, default=Path("output/test-audio/tellm-pl-pogoda.webm"))
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--transcription", default=DEFAULT_TEXT)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--real-stt", action="store_true")
    parser.add_argument("--skip-text", action="store_true")
    parser.add_argument("--skip-audio", action="store_true")
    parser.add_argument("--insecure", action="store_true")
    parser.add_argument("--write-webrtc-html", type=Path, default=Path("output/protocol-tests/webrtc-recorder-smoke.html"))
    args = parser.parse_args()

    args.ws_url = args.ws_url or ws_url_from_http(args.base_url)
    check_http(args.base_url, insecure=args.insecure)
    if args.https_url:
        check_http(args.https_url, insecure=args.insecure)

    if args.write_webrtc_html:
        write_webrtc_html(args.write_webrtc_html, args.wss_url or args.ws_url, args.transcription)
        print(f"ok WebRTC HTML {args.write_webrtc_html}")

    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
