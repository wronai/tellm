"""tellm v4 server"""
import asyncio
import json
from http import HTTPStatus

import websockets
from websockets.datastructures import Headers
from websockets.http11 import Response

from .bot import TellmBot
from .config import load_config
from litellm import completion

class TellmServer:
    def __init__(self, host: str = "localhost", port: int = 8000, db_path: str = "tellm.db"):
        self.host = host
        self.port = port
        self.bot = TellmBot(db_path=db_path)

    def register_function(self, name: str, func):
        self.bot.register_function(name, func)

    def process_request(self, connection, request):
        upgrade = request.headers.get("Upgrade", "").lower()
        if upgrade == "websocket":
            return None

        if request.path == "/healthz":
            body = b"ok\n"
            content_type = "text/plain; charset=utf-8"
        else:
            host = request.headers.get("Host", f"{self.host}:{self.port}")
            body = (
                "<!doctype html><html><body>"
                "<h1>tellm v4</h1>"
                "<p>WebSocket endpoint: <code>ws://"
                + host
                + "</code></p>"
                "</body></html>"
            ).encode("utf-8")
            content_type = "text/html; charset=utf-8"

        headers = Headers()
        headers["Content-Type"] = content_type
        headers["Content-Length"] = str(len(body))
        return Response(HTTPStatus.OK, "OK", headers, body)

    async def handle(self, websocket, path=None):
        async for message in websocket:
            try:
                data = json.loads(message)
                audio = data.get("audio")
                if not audio: continue
                transcription = self.bot.transcribe(audio)
                if not transcription: continue
                print("STT:", transcription)
                await websocket.send(json.dumps({"type": "view", "data": {"transcription": transcription, "status": "analyzing"}}))
                task = await self.bot.analyze_query(transcription)
                result = await self.bot.execute_task(task)
                view = self.bot.generate_view(transcription, task, result)
                config = load_config()
                resp = completion(model=config.llm_model, messages=[{"role": "user", "content": "Odpowiedz: " + transcription + ". Wynik: " + str(result)}], api_key=config.openrouter_api_key, base_url="https://openrouter.ai/api/v1")
                answer = resp.choices[0].message.content
                view.view_elements.append({"type": "answer", "text": answer})
                html = view.to_html()
                await websocket.send(json.dumps({"type": "view", "data": view.to_dict(), "html": html}))
                self.bot.speak(answer)
            except Exception as e:
                print("Bqd:", e)
                await websocket.send(json.dumps({"type": "error", "message": str(e)}))

    async def serve_forever(self):
        print("tellm v4 na " + self.host + ":" + str(self.port))
        async with websockets.serve(
            self.handle,
            self.host,
            self.port,
            process_request=self.process_request,
        ):
            await asyncio.Future()

    def run(self):
        try:
            asyncio.run(self.serve_forever())
        except KeyboardInterrupt:
            print("\ntellm stopped")
