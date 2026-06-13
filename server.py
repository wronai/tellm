"""tellm v4 server"""
import json
import asyncio
import websockets
from .bot import TellmBot, Task, ViewData
from .config import load_config
from litellm import completion

class TellmServer:
    def __init__(self, host: str = "localhost", port: int = 8000, db_path: str = "tellm.db"):
        self.host = host
        self.port = port
        self.bot = TellmBot(db_path=db_path)

    def register_function(self, name: str, func):
        self.bot.register_function(name, func)

    async def handle(self, websocket, path):
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

    def run(self):
        print("tellm v4 na " + self.host + ":" + str(self.port))
        start = websockets.serve(self.handle, self.host, self.port)
        asyncio.get_event_loop().run_until_complete(start)
        asyncio.get_event_loop().run_forever()
