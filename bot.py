"""tellm v4"""
import inspect
import html as html_lib
import json
import os
import sqlite3
import tempfile
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum

from .config import Config, load_config

class TaskType(Enum):
    NOW = "now"
    CRON = "cron"
    EVENT_TRIGGER = "event_trigger"

@dataclass
class Task:
    type: TaskType
    function_name: str
    parameters: Dict[str, Any]
    code: str = ""
    schedule: str = ""

@dataclass
class ViewData:
    transcription: str
    task: Task
    result: Any
    generated_code: str = ""
    performance_score: float = 0.0
    view_elements: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {"transcription": self.transcription, "task": {"type": self.task.type.value, "function": self.task.function_name, "parameters": self.task.parameters}, "result": self.result, "generated_code": self.generated_code, "performance_score": self.performance_score, "view_elements": self.view_elements}

    @staticmethod
    def _safe_json(value: Any) -> str:
        return html_lib.escape(json.dumps(value, ensure_ascii=False, default=str))

    def to_html(self) -> str:
        transcription = html_lib.escape(self.transcription)
        function_name = html_lib.escape(self.task.function_name)
        generated_code = html_lib.escape(self.generated_code)

        html = "<html><body>"
        html += "<h1>tellm View</h1>"
        html += "<p><strong>Transkrypcja:</strong> " + transcription + "</p>"
        html += "<p><strong>Zadanie:</strong> " + self.task.type.value + " / " + function_name + "</p>"
        html += "<p><strong>Parametry:</strong> " + self._safe_json(self.task.parameters) + "</p>"
        html += "<p><strong>Wynik:</strong> " + self._safe_json(self.result) + "</p>"
        if self.generated_code:
            html += "<p><strong>Kod:</strong> <pre>" + generated_code + "</pre></p>"
        html += "<p><strong>Score:</strong> " + str(self.performance_score) + "</p>"
        for elem in self.view_elements:
            if elem.get("type") == "answer":
                html += "<p><strong>Odpowiedz:</strong> " + html_lib.escape(str(elem.get("text", ""))) + "</p>"
        html += "</body></html>"
        return html

class TellmBot:
    def __init__(self, config: Optional[Config] = None, db_path: str = "tellm.db"):
        self.config = config or load_config()
        self.db_path = db_path
        self.functions_db: Dict[str, Callable] = {}
        self.evolution_history: Dict[str, List[Dict]] = {}
        self.current_version: Dict[str, int] = {}
        self.performance_scores: Dict[str, float] = {}
        self.stt_model = None
        self.tts = None
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, transcription TEXT, type TEXT, function_name TEXT, parameters TEXT, code TEXT, result TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS evolution (id INTEGER PRIMARY KEY, function_name TEXT, version INTEGER, code TEXT, score REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS views (id INTEGER PRIMARY KEY, transcription TEXT, task_data TEXT, result_data TEXT, html TEXT)")
        conn.commit()
        conn.close()

    def save_task(self, task: Task, result: Any, transcription: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO tasks (transcription, type, function_name, parameters, code, result) VALUES (?, ?, ?, ?, ?, ?)", (transcription, task.type.value, task.function_name, json.dumps(task.parameters), task.code, json.dumps(result)))
        conn.commit()
        conn.close()

    def save_evolution(self, function_name: str, step: Dict):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO evolution (function_name, version, code, score) VALUES (?, ?, ?, ?)", (function_name, step["version"], step["code"], step["score"]))
        conn.commit()
        conn.close()

    def save_view(self, view: ViewData) -> str:
        html = view.to_html()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO views (transcription, task_data, result_data, html) VALUES (?, ?, ?, ?)", (view.transcription, json.dumps(view.to_dict()["task"]), json.dumps(view.result), html))
        conn.commit()
        conn.close()
        return html

    def get_tasks(self, limit: int = 10) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, transcription, type, function_name, parameters, result FROM tasks ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "transcription": r[1], "type": r[2], "function": r[3], "parameters": json.loads(r[4]), "result": json.loads(r[5])} for r in rows]

    def register_function(self, name: str, func: Callable):
        self.functions_db[name] = func
        self.current_version[name] = 0
        self.evolution_history[name] = []
        self.performance_scores[name] = 0.0

    def _completion(self, messages: List[Dict[str, str]]):
        from litellm import completion

        return completion(
            model=self.config.llm_model,
            messages=messages,
            api_key=self.config.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def _get_stt_model(self):
        if self.stt_model is None:
            from faster_whisper import WhisperModel

            self.stt_model = WhisperModel("base", device="cpu", compute_type="int8")
        return self.stt_model

    def _get_tts(self):
        if self.tts is None:
            import pyttsx3

            self.tts = pyttsx3.init()
            self.tts.setProperty("rate", 150)
        return self.tts

    async def analyze_query(self, query: str) -> Task:
        prompt = "Analizuj: " + query + ". JSON: type,function_name,parameters,code,schedule"
        response = self._completion([{"role": "user", "content": prompt}])
        result = json.loads(response.choices[0].message.content)
        return Task(TaskType(result["type"]), result["function_name"], result["parameters"], result.get("code",""), result.get("schedule",""))

    async def evolve_function(self, task: Task) -> Dict:
        func_name = task.function_name
        version = self.current_version[func_name]
        prev_code = self.evolution_history[func_name][-1]["code"] if version > 0 else ""
        prompt = "Generuj funkcji: " + func_name + ". Zadanie: " + str(task.parameters) + ". Kod:"
        response = self._completion([{"role": "user", "content": prompt}])
        new_code = response.choices[0].message.content
        score = self.performance_scores[func_name] + 0.1
        step = {"version": version + 1, "previous_code": prev_code, "code": new_code, "improvement": "LLM", "score": score}
        self.evolution_history[func_name].append(step)
        self.current_version[func_name] += 1
        self.performance_scores[func_name] = score
        self.save_evolution(func_name, step)
        if new_code:
            try:
                exec(new_code, globals())
            except Exception as e:
                print("Blad:", e)
        return step

    async def execute_task(self, task: Task) -> Any:
        if task.type == TaskType.NOW:
            if task.function_name in self.functions_db:
                result = self.functions_db[task.function_name](task.parameters)
                if inspect.isawaitable(result):
                    return await result
                return result
            return await self.evolve_function(task)
        elif task.type == TaskType.CRON: return {"status": "cron_set", "schedule": task.schedule}
        elif task.type == TaskType.EVENT_TRIGGER: return {"status": "event_set", "function": task.function_name}

    def transcribe(self, audio_data: bytes) -> str:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            segments, _ = self._get_stt_model().transcribe(temp_path, language="pl")
            return " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as e:
            print("STT blad:", e)
            return ""
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def speak(self, text: str):
        tts = self._get_tts()
        tts.say(text)
        tts.runAndWait()

    def generate_view(self, transcription: str, task: Task, result: Any) -> ViewData:
        view_elements = [{"type": "transcription", "text": transcription}, {"type": "task", "data": {"type": task.type.value, "function": task.function_name, "parameters": task.parameters}}, {"type": "result", "data": result}, {"type": "code", "code": task.code}]
        score = self.performance_scores.get(task.function_name, 0.0)
        view = ViewData(transcription=transcription, task=task, result=result, generated_code=task.code, performance_score=score, view_elements=view_elements)
        html = self.save_view(view)
        view.view_elements.append({"type": "html", "html": html})
        return view
