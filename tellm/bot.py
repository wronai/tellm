"""tellm v4"""
from datetime import datetime, timezone
import inspect
import html as html_lib
import json
import os
import socket
import sqlite3
import tempfile
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from urllib import error as url_error
from urllib import parse as url_parse
from urllib import request as url_request

from .config import Config, load_config
from .improvement import AutoimprovementRunner, ExecutionHistoryStore
from .registry import (
    ResourceRegistry,
    registry_manifest_schema,
    service_result,
    service_result_schema,
)

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
    view: Dict[str, Any] = field(default_factory=dict)
    processes: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ViewData:
    transcription: str
    task: Task
    result: Any
    generated_code: str = ""
    performance_score: float = 0.0
    view_elements: List[Dict] = field(default_factory=list)
    render_data: Dict[str, Any] = field(default_factory=dict)
    view_id: Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "transcription": self.transcription,
            "task": {
                "type": self.task.type.value,
                "function": self.task.function_name,
                "parameters": self.task.parameters,
                "schedule": self.task.schedule,
                "view": self.task.view,
                "processes": self.task.processes,
            },
            "result": self.result,
            "generated_code": self.generated_code,
            "performance_score": self.performance_score,
            "view_elements": self.view_elements,
            "render_data": self.render_data,
            "view_id": self.view_id,
        }

    @staticmethod
    def _safe_json(value: Any) -> str:
        return html_lib.escape(json.dumps(value, ensure_ascii=False, default=str))

    @staticmethod
    def _safe_text(value: Any) -> str:
        return html_lib.escape("" if value is None else str(value))

    def _render_items(self, items: Any) -> str:
        if isinstance(items, dict):
            rows = "".join(
                "<tr><th>"
                + self._safe_text(key)
                + "</th><td>"
                + self._safe_text(value)
                + "</td></tr>"
                for key, value in items.items()
            )
            return '<table class="kv"><tbody>' + rows + "</tbody></table>"
        if isinstance(items, list):
            rendered = "".join("<li>" + self._safe_text(item) + "</li>" for item in items)
            return "<ul>" + rendered + "</ul>"
        return "<p>" + self._safe_text(items) + "</p>"

    def _render_table(self, block: Dict[str, Any]) -> str:
        columns = block.get("columns") or []
        rows = block.get("rows") or []
        if not isinstance(columns, list) or not isinstance(rows, list):
            return "<pre>" + self._safe_json(block) + "</pre>"

        head = "".join("<th>" + self._safe_text(column) + "</th>" for column in columns)
        body = ""
        for row in rows:
            if isinstance(row, dict):
                cells = [row.get(column, "") for column in columns]
            elif isinstance(row, list):
                cells = row
            else:
                cells = [row]
            body += "<tr>" + "".join("<td>" + self._safe_text(cell) + "</td>" for cell in cells) + "</tr>"
        return "<table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>"

    def _render_block(self, block: Any) -> str:
        if not isinstance(block, dict):
            return "<pre>" + self._safe_json(block) + "</pre>"

        block_type = str(block.get("type", "json")).lower()
        if block_type in {"heading", "title"}:
            level = int(block.get("level", 2) or 2)
            level = min(max(level, 2), 4)
            return f"<h{level}>" + self._safe_text(block.get("text")) + f"</h{level}>"
        if block_type in {"text", "paragraph", "answer"}:
            return "<p>" + self._safe_text(block.get("text")) + "</p>"
        if block_type == "metric":
            return (
                '<div class="metric"><span>'
                + self._safe_text(block.get("label"))
                + "</span><strong>"
                + self._safe_text(block.get("value"))
                + "</strong></div>"
            )
        if block_type in {"list", "items"}:
            return self._render_items(block.get("items", []))
        if block_type in {"key_value", "details"}:
            return self._render_items(block.get("items", block.get("data", {})))
        if block_type == "table":
            return self._render_table(block)
        if block_type == "code":
            return "<pre><code>" + self._safe_text(block.get("code", "")) + "</code></pre>"
        if block_type == "json":
            return "<pre><code>" + self._safe_json(block.get("data", block)) + "</code></pre>"
        return "<pre><code>" + self._safe_json(block) + "</code></pre>"

    def _render_dynamic(self) -> str:
        if not self.render_data:
            return ""
        title = self.render_data.get("title") or "Dynamiczny widok"
        blocks = self.render_data.get("blocks") or []
        if not isinstance(blocks, list):
            blocks = [{"type": "json", "data": blocks}]
        html = '<section class="dynamic-view">'
        html += "<h2>" + self._safe_text(title) + "</h2>"
        html += "".join(self._render_block(block) for block in blocks)
        html += "</section>"
        return html

    def to_html(self) -> str:
        transcription = html_lib.escape(self.transcription)
        function_name = html_lib.escape(self.task.function_name)
        generated_code = html_lib.escape(self.generated_code)

        html = """<html><head><style>
body { font-family: system-ui, sans-serif; line-height: 1.5; color: #20242a; }
table { width: 100%; border-collapse: collapse; margin: 10px 0; }
th, td { border-bottom: 1px solid #d9dee7; padding: 6px 8px; text-align: left; vertical-align: top; }
pre { overflow: auto; padding: 10px; background: #f2f4f7; border-radius: 6px; }
.dynamic-view { margin: 12px 0; padding: 12px; border: 1px solid #d9dee7; border-radius: 8px; }
.metric { display: inline-grid; gap: 2px; min-width: 130px; margin: 6px 8px 6px 0; padding: 10px; border: 1px solid #d9dee7; border-radius: 6px; }
.metric span { color: #5d6673; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.metric strong { font-size: 20px; }
</style></head><body>"""
        html += "<h1>tellm View</h1>"
        html += "<p><strong>Transkrypcja:</strong> " + transcription + "</p>"
        html += "<p><strong>Zadanie:</strong> " + self.task.type.value + " / " + function_name + "</p>"
        html += "<p><strong>Parametry:</strong> " + self._safe_json(self.task.parameters) + "</p>"
        html += self._render_dynamic()
        html += "<p><strong>Wynik:</strong> " + self._safe_json(self.result) + "</p>"
        if self.generated_code:
            html += "<p><strong>Kod:</strong> <pre>" + generated_code + "</pre></p>"
        if self.task.processes:
            html += "<p><strong>Procesy:</strong> " + self._safe_json(self.task.processes) + "</p>"
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
        self.history = ExecutionHistoryStore(self.db_path)
        self.registry = ResourceRegistry()
        self._init_registry()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, transcription TEXT, type TEXT, function_name TEXT, parameters TEXT, code TEXT, result TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS evolution (id INTEGER PRIMARY KEY, function_name TEXT, version INTEGER, code TEXT, score REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS views (id INTEGER PRIMARY KEY, transcription TEXT, task_data TEXT, result_data TEXT, html TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS autoimprovement_reports (id INTEGER PRIMARY KEY, created_at TEXT, report_json TEXT, html TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS pending_patches (id INTEGER PRIMARY KEY, created_at TEXT, patch_key TEXT, status TEXT, risk TEXT, uri TEXT, description TEXT, patch_json TEXT)")
        conn.commit()
        conn.close()

    def record_execution(
        self,
        uri: str,
        kind: str,
        ok: bool,
        status: str = "",
        error: str = "",
        result: Any = None,
        logs: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        return self.history.record(
            uri=uri,
            kind=kind,
            ok=ok,
            status=status,
            error=error,
            result=result,
            logs=logs or [],
            metadata=metadata or {},
        )

    def save_autoimprovement_report(self, report: Dict[str, Any], html: str = "") -> int:
        data = report.setdefault("data", {})
        created_at = str(data.get("generated_at") or datetime.now(timezone.utc).isoformat())
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO autoimprovement_reports (created_at, report_json, html) VALUES (?, ?, ?)",
            (created_at, json.dumps(report, ensure_ascii=False, default=str), html),
        )
        report_id = int(c.lastrowid)
        data["report_id"] = report_id
        c.execute(
            "UPDATE autoimprovement_reports SET report_json = ?, html = ? WHERE id = ?",
            (json.dumps(report, ensure_ascii=False, default=str), html, report_id),
        )
        for patch in data.get("patches", []) or []:
            if not isinstance(patch, dict):
                continue
            c.execute(
                """
                INSERT INTO pending_patches
                    (created_at, patch_key, status, risk, uri, description, patch_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    str(patch.get("id", "")),
                    str(patch.get("status", "pending_review")),
                    str(patch.get("risk", "")),
                    str(patch.get("uri", "")),
                    str(patch.get("description", "")),
                    json.dumps(patch, ensure_ascii=False, default=str),
                ),
            )
        conn.commit()
        conn.close()
        return report_id

    def update_autoimprovement_report_html(self, report_id: int, report: Dict[str, Any], html: str) -> None:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "UPDATE autoimprovement_reports SET report_json = ?, html = ? WHERE id = ?",
            (json.dumps(report, ensure_ascii=False, default=str), html, report_id),
        )
        conn.commit()
        conn.close()

    def get_latest_autoimprovement_report(self) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT report_json FROM autoimprovement_reports ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        return json.loads(row[0]) if row else None

    def get_latest_autoimprovement_html(self) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT html FROM autoimprovement_reports ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        return row[0] if row and row[0] else None

    def save_task(self, task: Task, result: Any, transcription: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO tasks (transcription, type, function_name, parameters, code, result) VALUES (?, ?, ?, ?, ?, ?)", (transcription, task.type.value, task.function_name, json.dumps(task.parameters, ensure_ascii=False, default=str), task.code, json.dumps(result, ensure_ascii=False, default=str)))
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
        c.execute("INSERT INTO views (transcription, task_data, result_data, html) VALUES (?, ?, ?, ?)", (view.transcription, json.dumps(view.to_dict()["task"], ensure_ascii=False, default=str), json.dumps(view.result, ensure_ascii=False, default=str), html))
        view.view_id = c.lastrowid
        conn.commit()
        conn.close()
        return html

    def get_view_html(self, view_id: int) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT html FROM views WHERE id = ?", (view_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

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
        self.registry.register_callable(
            uri="tellm://function/local/" + name,
            kind="function",
            name=name,
            func=func,
            description="User-registered local Python function.",
            input_schema={"type": "object"},
            permissions={
                "llm_read": True,
                "llm_execute": True,
                "danger_level": "execute_local",
            },
            tags=["local", "function"],
            aliases=["tellm://function/" + name],
            metadata={"call_style": "params"},
        )

    def _init_registry(self) -> None:
        self.registry.register_value(
            uri="tellm://schema/tellm/resource-manifest",
            kind="schema",
            name="tellm.resource_manifest",
            value=registry_manifest_schema(),
            description="Tellm Resource Manifest 1.0 schema based on JSON Schema Draft 2020-12.",
            value_schema={"type": "object"},
            permissions={"llm_read": True, "danger_level": "safe"},
            tags=["schema", "trm", "json-schema"],
            version="1.0.0",
        )
        self.registry.register_value(
            uri="tellm://schema/tellm/service-result",
            kind="schema",
            name="tellm.service_result",
            value=service_result_schema(),
            description="Tellm Service Result envelope schema based on JSON Schema Draft 2020-12.",
            value_schema={"type": "object"},
            permissions={"llm_read": True, "danger_level": "safe"},
            tags=["schema", "tsr", "json-schema"],
            version="1.0.0",
        )
        self.registry.register_callable(
            uri="tellm://function/system/now",
            kind="function",
            name="now",
            func=self._registry_now,
            description="Return current UTC time as structured JSON.",
            input_schema={"type": "object"},
            output_schema={"type": "object", "required": ["ok", "type", "data", "message", "errors"]},
            permissions={
                "llm_read": True,
                "llm_execute": True,
                "danger_level": "safe",
            },
            tags=["system", "time"],
        )
        self.registry.register_callable(
            uri="tellm://function/system/echo",
            kind="function",
            name="echo",
            func=self._registry_echo,
            description="Echo input payload. Useful for protocol tests.",
            input_schema={"type": "object"},
            output_schema={"type": "object", "required": ["ok", "type", "data", "message", "errors"]},
            permissions={
                "llm_read": True,
                "llm_execute": True,
                "danger_level": "safe",
            },
            tags=["system", "test"],
        )
        self.registry.register_callable(
            uri="tellm://service/domain/check",
            kind="service",
            name="domain.check",
            func=self._registry_domain_check,
            description="Check domain status with local DNS and RDAP probes. The service returns structured JSON and does not let the LLM invent availability.",
            input_schema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "pattern": r"^[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}$",
                    }
                },
                "required": ["domain"],
                "additionalProperties": True,
            },
            output_schema={"type": "object", "required": ["ok", "type", "data", "message", "errors"]},
            permissions={
                "llm_read": True,
                "llm_execute": True,
                "requires_confirmation": False,
                "danger_level": "network",
            },
            tags=["service", "domain", "network"],
        )
        self.registry.register_callable(
            uri="tellm://service/weather/current",
            kind="service",
            name="weather.current",
            func=self._registry_weather_current,
            description="Fetch current real-world weather from Open-Meteo. Use this for current weather questions instead of ad hoc simulated Python functions.",
            input_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "country": {"type": "string"},
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                },
                "additionalProperties": True,
            },
            output_schema={"type": "object", "required": ["ok", "type", "data", "message", "errors"]},
            permissions={
                "llm_read": True,
                "llm_execute": True,
                "requires_confirmation": False,
                "danger_level": "network",
            },
            tags=["service", "weather", "network", "real_world_data"],
            metadata={
                "requires_real_world_data": True,
                "allowed_sources": ["open_meteo"],
                "disallowed_sources": ["local_simulation", "mock", "test", "llm_generated", "generated"],
            },
            data_policy={
                "requires_real_world_data": True,
                "allowed_sources": ["open_meteo"],
                "disallowed_sources": ["local_simulation", "mock", "test", "llm_generated", "generated"],
            },
            render={
                "default_view": "tellm://view/weather/current",
                "renderer": "auto",
                "template": "weather_current",
            },
        )
        self.registry.register_callable(
            uri="tellm://service/system/autoimprove",
            kind="service",
            name="system.autoimprove",
            func=self._registry_autoimprove,
            description="Run controlled autoimprovement audit. Produces report JSON and pending patch proposals; never auto-applies code by default.",
            input_schema={
                "type": "object",
                "properties": {
                    "mode": {"type": "string"},
                    "scope": {"type": "string"},
                    "max_cycles": {"type": "integer"},
                    "time_window": {"type": "string"},
                    "dry_run": {"type": "boolean"},
                    "allow_code_generation": {"type": "boolean"},
                    "allow_auto_apply": {"type": "boolean"},
                    "repeated_failure_threshold": {"type": "integer"},
                },
                "additionalProperties": True,
            },
            output_schema={"type": "object", "required": ["ok", "type", "data", "message", "errors"]},
            permissions={
                "llm_read": True,
                "llm_execute": True,
                "requires_confirmation": False,
                "danger_level": "read_only",
            },
            tags=["service", "system", "autoimprovement", "audit"],
        )
        self.registry.register_value(
            uri="tellm://env/OPENROUTER_API_KEY",
            kind="env",
            name="OPENROUTER_API_KEY",
            value=lambda: os.getenv("OPENROUTER_API_KEY"),
            description="OpenRouter API key presence. Value is masked for LLM.",
            value_schema={"type": ["string", "null"]},
            permissions={
                "llm_discover": True,
                "llm_read": True,
                "llm_execute": False,
                "danger_level": "secret",
            },
            tags=["env", "secret"],
            masked=True,
        )
        self.registry.register_value(
            uri="tellm://setting/app/theme",
            kind="setting",
            name="theme",
            value="light",
            description="Default browser UI theme.",
            value_schema={"type": "string", "enum": ["warm", "light", "dark"]},
            permissions={
                "llm_read": True,
                "llm_write": True,
                "requires_confirmation": True,
                "danger_level": "write_local",
            },
            tags=["setting", "ui"],
        )
        self.registry.register_value(
            uri="tellm://data/task/recent",
            kind="data",
            name="recent_tasks",
            value=lambda: self.get_tasks(limit=10),
            description="Recent tasks saved in SQLite.",
            value_schema={"type": "array"},
            permissions={
                "llm_read": True,
                "danger_level": "read_only",
            },
            tags=["data", "tasks", "sqlite"],
        )
        self.registry.register_value(
            uri="tellm://data/system/execution-history",
            kind="data",
            name="execution_history",
            value=lambda: self.history.recent(limit=100),
            description="Recent local service and workflow executions.",
            value_schema={"type": "array"},
            permissions={"llm_read": True, "danger_level": "read_only"},
            tags=["data", "history", "autoimprovement"],
        )
        self.registry.register_value(
            uri="tellm://data/system/registry-health",
            kind="data",
            name="registry_health",
            value=lambda: AutoimprovementRunner(self.registry, self.history).registry_health(),
            description="Current registry validation health snapshot.",
            value_schema={"type": "object"},
            permissions={"llm_read": True, "danger_level": "read_only"},
            tags=["data", "registry", "health"],
        )
        self.registry.register_value(
            uri="tellm://data/system/autoimprovement-report/latest",
            kind="data",
            name="latest_autoimprovement_report",
            value=lambda: self.get_latest_autoimprovement_report() or {},
            description="Latest saved autoimprovement report JSON.",
            value_schema={"type": "object"},
            permissions={"llm_read": True, "danger_level": "read_only"},
            tags=["data", "autoimprovement", "report"],
        )
        self.registry.register_value(
            uri="tellm://view/system/autoimprovement-report/latest",
            kind="view",
            name="latest_autoimprovement_report_html",
            value=lambda: self.get_latest_autoimprovement_html() or "",
            description="Latest saved autoimprovement report HTML.",
            value_schema={"type": "string"},
            permissions={"llm_read": True, "danger_level": "read_only"},
            tags=["view", "autoimprovement", "report"],
        )
        self.registry.register_value(
            uri="tellm://event/cron/hourly",
            kind="event",
            name="cron.hourly",
            value={
                "schedule": "0 * * * *",
                "target": "tellm://service/system/autoimprove",
                "input": {
                    "mode": "scheduled",
                    "scope": "registry",
                    "time_window": "1h",
                    "max_cycles": 10,
                    "dry_run": True,
                    "allow_auto_apply": False,
                },
            },
            description="Hourly maintenance trigger for registry autoimprovement.",
            value_schema={"type": "object"},
            permissions={"llm_read": True, "danger_level": "read_only"},
            tags=["event", "cron", "autoimprovement"],
        )
        self.registry.register_value(
            uri="tellm://event/workflow/every-10-cycles",
            kind="event",
            name="workflow.every_10_cycles",
            value={
                "condition": {
                    "metric": "workflow.completed_since_last_autoimprove",
                    "operator": ">=",
                    "value": 10,
                },
                "target": "tellm://service/system/autoimprove",
                "input": {
                    "mode": "event",
                    "scope": "registry",
                    "max_cycles": 10,
                    "dry_run": True,
                    "allow_auto_apply": False,
                },
            },
            description="Autoimprovement trigger after every 10 completed workflow executions.",
            value_schema={"type": "object"},
            permissions={"llm_read": True, "danger_level": "read_only"},
            tags=["event", "workflow", "autoimprovement"],
        )

    def _registry_now(self, params: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return service_result(
            ok=True,
            result_type="system.now.result",
            uri="tellm://function/system/now",
            data={"iso": now, "timezone": "UTC"},
            title="Aktualny czas",
            summary=now,
            details="Wynik lokalnej funkcji system.now.",
            view={"renderer": "auto", "template": "status_card", "severity": "info"},
        )

    def _registry_echo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return service_result(
            ok=True,
            result_type="system.echo.result",
            uri="tellm://function/system/echo",
            data={"input": params},
            title="Echo",
            summary="Payload zostal zwrocony przez lokalna funkcje.",
            details="Wynik lokalnej funkcji system.echo.",
        )

    def _registry_autoimprove(self, params: Dict[str, Any]) -> Dict[str, Any]:
        options = dict(params or {})
        options.setdefault("dry_run", True)
        options.setdefault("allow_auto_apply", False)
        report = AutoimprovementRunner(self.registry, self.history).run(options)
        self.save_autoimprovement_report(report)
        return report

    @staticmethod
    def _weather_code_description(code: Any) -> str:
        descriptions = {
            0: "bezchmurnie",
            1: "głównie bezchmurnie",
            2: "częściowe zachmurzenie",
            3: "zachmurzenie całkowite",
            45: "mgła",
            48: "mgła osadzająca szadź",
            51: "lekka mżawka",
            53: "umiarkowana mżawka",
            55: "gęsta mżawka",
            56: "lekka marznąca mżawka",
            57: "gęsta marznąca mżawka",
            61: "lekki deszcz",
            63: "umiarkowany deszcz",
            65: "silny deszcz",
            66: "lekki marznący deszcz",
            67: "silny marznący deszcz",
            71: "lekkie opady śniegu",
            73: "umiarkowane opady śniegu",
            75: "silne opady śniegu",
            77: "ziarna śnieżne",
            80: "lekkie przelotne opady deszczu",
            81: "umiarkowane przelotne opady deszczu",
            82: "gwałtowne przelotne opady deszczu",
            85: "lekkie przelotne opady śniegu",
            86: "silne przelotne opady śniegu",
            95: "burza",
            96: "burza z lekkim gradem",
            99: "burza z silnym gradem",
        }
        try:
            return descriptions.get(int(code), "nieznane warunki")
        except Exception:
            return "nieznane warunki"

    @staticmethod
    def _http_json(url: str, timeout: int = 8) -> Dict[str, Any]:
        req = url_request.Request(url, headers={"User-Agent": "tellm/4"})
        with url_request.urlopen(req, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)

    def _geocode_city(self, city: str, country: str = "") -> Dict[str, Any]:
        query = {
            "name": city,
            "count": 1,
            "language": "pl",
            "format": "json",
        }
        if country:
            query["countryCode"] = country.upper()
        url = "https://geocoding-api.open-meteo.com/v1/search?" + url_parse.urlencode(query)
        data = self._http_json(url)
        results = data.get("results") or []
        if not results:
            raise ValueError("Location not found: " + city)
        return results[0]

    def _registry_weather_current(self, params: Dict[str, Any]) -> Dict[str, Any]:
        uri = "tellm://service/weather/current"
        city = str(params.get("city") or params.get("location") or "").strip()
        country = str(params.get("country") or "PL").strip().upper()
        errors = []
        try:
            latitude = params.get("latitude")
            longitude = params.get("longitude")
            location = {}
            if latitude is None or longitude is None:
                if not city:
                    raise ValueError("city or latitude/longitude is required")
                location = self._geocode_city(city, country)
                latitude = location.get("latitude")
                longitude = location.get("longitude")
                city = str(location.get("name") or city)
                country = str(location.get("country_code") or country)
            latitude = float(latitude)
            longitude = float(longitude)
            forecast_query = {
                "latitude": latitude,
                "longitude": longitude,
                "current": ",".join(
                    [
                        "temperature_2m",
                        "relative_humidity_2m",
                        "apparent_temperature",
                        "weather_code",
                        "wind_speed_10m",
                        "wind_direction_10m",
                    ]
                ),
                "timezone": "auto",
            }
            forecast_url = "https://api.open-meteo.com/v1/forecast?" + url_parse.urlencode(forecast_query)
            weather = self._http_json(forecast_url)
            current = weather.get("current") or {}
            code = current.get("weather_code")
            description = self._weather_code_description(code)
            temperature = current.get("temperature_2m")
            fetched_at = datetime.now(timezone.utc).isoformat()
            summary = "Aktualnie %s°C, %s." % (temperature, description)
            return service_result(
                ok=True,
                result_type="weather.current.result",
                uri=uri,
                data={
                    "city": city,
                    "country": country,
                    "latitude": latitude,
                    "longitude": longitude,
                    "temperature_c": temperature,
                    "apparent_temperature_c": current.get("apparent_temperature"),
                    "humidity_percent": current.get("relative_humidity_2m"),
                    "wind_speed_kmh": current.get("wind_speed_10m"),
                    "wind_direction_deg": current.get("wind_direction_10m"),
                    "weather_code": code,
                    "description": description,
                    "source": "open_meteo",
                    "fetched_at": fetched_at,
                    "current_time": current.get("time"),
                },
                title="Pogoda w " + city,
                summary=summary,
                details="To jest wynik lokalnej usługi weather.current z providerem Open-Meteo.",
                errors=[],
                view={"renderer": "auto", "template": "weather_current", "severity": "info"},
            )
        except Exception as exc:
            errors.append(
                {
                    "code": "WEATHER_PROVIDER_UNAVAILABLE",
                    "source": "weather.current",
                    "detail": str(exc),
                }
            )
            return service_result(
                ok=False,
                result_type="weather.current.result",
                uri=uri,
                data={
                    "city": city,
                    "country": country,
                    "available": None,
                    "source": "open_meteo",
                    "status": "unknown",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                },
                title="Nie udało się pobrać pogody",
                summary="Lokalna usługa weather.current nie pobrała danych pogodowych.",
                details="To jest błąd lokalnej usługi pogodowej, nie odpowiedź LLM.",
                errors=errors,
                view={"renderer": "auto", "template": "weather_current", "severity": "error"},
            )

    @staticmethod
    def _normalize_domain(domain: str) -> str:
        domain = domain.strip().lower().rstrip(".")
        if "://" in domain:
            domain = domain.split("://", 1)[1]
        domain = domain.split("/", 1)[0].split(":", 1)[0]
        return domain

    def _registry_domain_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        uri = "tellm://service/domain/check"
        domain = self._normalize_domain(str(params.get("domain", "")))
        checked_by = []
        dns_resolves = None
        rdap_status = "not_checked"
        errors = []

        try:
            socket.getaddrinfo(domain, None)
            dns_resolves = True
            checked_by.append("dns")
        except socket.gaierror as exc:
            dns_resolves = False
            checked_by.append("dns")
            errors.append(
                {
                    "code": "DNS_NOT_RESOLVED",
                    "source": "domain.check",
                    "detail": str(exc),
                }
            )
        except Exception as exc:
            errors.append(
                {
                    "code": "DNS_ERROR",
                    "source": "domain.check",
                    "detail": str(exc),
                }
            )

        rdap_url = "https://rdap.org/domain/" + domain
        try:
            req = url_request.Request(rdap_url, headers={"User-Agent": "tellm/4"})
            with url_request.urlopen(req, timeout=4) as response:
                checked_by.append("rdap")
                rdap_status = "registered" if response.status == 200 else "unknown"
        except url_error.HTTPError as exc:
            checked_by.append("rdap")
            rdap_status = "not_found" if exc.code == 404 else "unknown"
            if exc.code != 404:
                errors.append(
                    {
                        "code": "RDAP_HTTP_ERROR",
                        "source": "domain.check",
                        "detail": "HTTP %s" % exc.code,
                    }
                )
        except Exception as exc:
            errors.append(
                {
                    "code": "RDAP_UNAVAILABLE",
                    "source": "domain.check",
                    "detail": str(exc),
                }
            )

        if rdap_status == "registered" or dns_resolves is True:
            available = False
            status = "registered"
            ok = True
            title = "Domena jest zajeta"
            summary = "Domena %s nie wyglada na wolna." % domain
        elif rdap_status == "not_found":
            available = True
            status = "available_candidate"
            ok = True
            title = "Domena moze byc wolna"
            summary = "RDAP zwrocil 404 dla domeny %s." % domain
        else:
            available = None
            status = "unknown"
            ok = False
            title = "Nie sprawdzono domeny"
            summary = "Lokalna usluga nie potwierdzila statusu domeny %s." % domain

        return service_result(
            ok=ok,
            result_type="domain.availability.result",
            uri=uri,
            data={
                "domain": domain,
                "available": available,
                "status": status,
                "dns_resolves": dns_resolves,
                "rdap_status": rdap_status,
                "checked_by": sorted(set(checked_by)),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            },
            title=title,
            summary=summary,
            details="To jest wynik lokalnej uslugi domain.check, nie bezposrednia odpowiedz LLM.",
            errors=[] if ok else errors,
            view={
                "renderer": "auto",
                "template": "domain_result",
                "severity": "success" if available is True else "warning" if available is False else "error",
            },
        )

    async def execute_resource(self, uri: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        try:
            result = self.registry.execute(uri, payload or {})
            if inspect.isawaitable(result):
                result = await result
            self.record_execution(
                uri=uri,
                kind="registry_execute",
                ok=bool(result.get("ok", True)) if isinstance(result, dict) else True,
                status=str(result.get("type", "completed")) if isinstance(result, dict) else "completed",
                result=result,
                metadata={"input": payload or {}},
            )
            return result
        except Exception as exc:
            self.record_execution(
                uri=uri,
                kind="registry_execute",
                ok=False,
                status="error",
                error=str(exc),
                result={"error": str(exc)},
                metadata={"input": payload or {}},
            )
            raise

    def _completion(self, messages: List[Dict[str, str]]):
        from litellm import completion

        return completion(
            model=self.config.llm_model,
            messages=messages,
            api_key=self.config.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    @staticmethod
    def _parse_json_response(content: str) -> Dict[str, Any]:
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        if not text.startswith("{"):
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                text = text[start : end + 1]
        return json.loads(text)

    @staticmethod
    def _normalize_processes(value: Any) -> List[Dict[str, Any]]:
        if isinstance(value, dict):
            return [value]
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        return []

    def _ensure_function_state(self, function_name: str) -> None:
        self.current_version.setdefault(function_name, 0)
        self.evolution_history.setdefault(function_name, [])
        self.performance_scores.setdefault(function_name, 0.0)

    @staticmethod
    def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
        allowed = {"datetime", "json", "math", "re", "statistics", "random"}
        root_name = name.split(".")[0]
        if root_name not in allowed:
            raise ImportError(f"Import '{root_name}' is not allowed in tellm process code")
        return __import__(name, globals, locals, fromlist, level)

    def _process_globals(self) -> Dict[str, Any]:
        safe_builtins = {
            "__import__": self._restricted_import,
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "Exception": Exception,
            "float": float,
            "getattr": getattr,
            "hasattr": hasattr,
            "int": int,
            "isinstance": isinstance,
            "len": len,
            "list": list,
            "max": max,
            "min": min,
            "print": print,
            "range": range,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "TypeError": TypeError,
            "ValueError": ValueError,
            "zip": zip,
        }
        return {
            "__builtins__": safe_builtins,
            "datetime": __import__("datetime"),
            "json": json,
            "math": __import__("math"),
            "re": __import__("re"),
            "statistics": __import__("statistics"),
        }

    async def _execute_registered_function(self, name: str, params: Dict[str, Any]) -> Any:
        result = self.functions_db[name](params)
        if inspect.isawaitable(result):
            return await result
        return result

    async def _execute_python_process(
        self, process: Dict[str, Any], fallback_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        name = str(process.get("name") or process.get("function_name") or "process")
        params = process.get("parameters", fallback_params)
        if not isinstance(params, dict):
            params = {"value": params}

        code = str(process.get("code") or "").strip()
        entrypoint = str(
            process.get("entrypoint")
            or process.get("function_name")
            or process.get("name")
            or ""
        )

        if not code and name in self.functions_db:
            return {
                "name": name,
                "ok": True,
                "result": await self._execute_registered_function(name, params),
            }

        if not code:
            raise ValueError(f"Process '{name}' has no python code or registered function")

        namespace = self._process_globals()
        exec(code, namespace)
        func = namespace.get(entrypoint) if entrypoint else None
        if not callable(func):
            candidates = [
                value
                for key, value in namespace.items()
                if callable(value) and not key.startswith("__")
            ]
            func = candidates[-1] if candidates else None
        if not callable(func):
            raise ValueError(f"Process '{name}' did not define callable entrypoint")

        if process.get("args_style") == "kwargs":
            result = func(**params)
        else:
            try:
                signature = inspect.signature(func)
                result = func() if len(signature.parameters) == 0 else func(params)
            except (TypeError, ValueError):
                result = func(params)
        if inspect.isawaitable(result):
            result = await result
        return {"name": name, "ok": True, "result": result}

    async def execute_processes(self, task: Task) -> Dict[str, Any]:
        outputs = []
        for process in task.processes:
            name = str(process.get("name") or process.get("function_name") or "process")
            try:
                outputs.append(await self._execute_python_process(process, task.parameters))
            except Exception as exc:
                outputs.append({"name": name, "ok": False, "error": str(exc)})
        return {
            "status": "completed" if all(item.get("ok") for item in outputs) else "failed",
            "processes": outputs,
        }

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
        registry_json = json.dumps(
            self.registry.discover_for_llm(),
            ensure_ascii=False,
            default=str,
        )
        prompt = """
Zwróć wyłącznie JSON bez markdown. Użyj schematu:
{
  "type": "now|cron|event_trigger",
  "function_name": "nazwa_funkcji_lub_procesu",
  "parameters": {},
  "schedule": "",
  "view": {
    "title": "tytuł widoku",
    "blocks": [
      {"type": "heading", "text": "...", "level": 2},
      {"type": "text", "text": "..."},
      {"type": "metric", "label": "...", "value": "..."},
      {"type": "list", "items": ["..."]},
      {"type": "table", "columns": ["..."], "rows": [{"...": "..."}]},
      {"type": "json", "data": {}}
    ]
  },
  "processes": [
    {
      "name": "nazwa_procesu",
      "language": "python",
      "entrypoint": "run",
      "parameters": {},
      "code": "def run(params):\\n    return params"
    }
  ],
  "code": ""
}
Pole 'view' to dane do dynamicznego renderowania. Pole 'processes' to funkcje Python do wykonania jako procesy.
Kod Python ma definiować funkcję przyjmującą jeden argument params. Nie używaj plików ani sieci.
Dla zadań wykonawczych najpierw wybierz istniejący zasób z registry i wpisz jego URI w function_name.
Jeżeli pytanie dotyczy aktualnej pogody, użyj tellm://service/weather/current z parametrami city/country.
Nie generuj ad hoc funkcji pogodowych typu get_weather_* i nie używaj local_simulation/mock dla aktualnych danych.
LLM nie jest źródłem prawdy dla zadań wykonawczych: wybiera usługę albo generuje bezpieczny proces,
a końcowy wynik musi pochodzić z lokalnej funkcji/procesu jako JSON.
Registry dostępne dla LLM:
""" + registry_json + """
Zapytanie: """ + query
        response = self._completion([{"role": "user", "content": prompt}])
        result = self._parse_json_response(response.choices[0].message.content)
        try:
            task_type = TaskType(str(result.get("type", "now")).lower())
        except ValueError:
            task_type = TaskType.NOW
        parameters = result.get("parameters", {})
        if not isinstance(parameters, dict):
            parameters = {"value": parameters}
        view = result.get("view") or result.get("render_data") or {}
        if not isinstance(view, dict):
            view = {"title": "Wynik", "blocks": [{"type": "json", "data": view}]}
        processes = self._normalize_processes(result.get("processes", []))
        code = str(result.get("code", "") or "")
        function_name = str(result.get("function_name") or result.get("function") or "run")
        if code and not processes:
            processes = [
                {
                    "name": function_name,
                    "language": "python",
                    "entrypoint": function_name,
                    "parameters": parameters,
                    "code": code,
                }
            ]
        return Task(
            task_type,
            function_name,
            parameters,
            code,
            str(result.get("schedule", "") or ""),
            view,
            processes,
        )

    async def evolve_function(self, task: Task) -> Dict:
        func_name = task.function_name
        self._ensure_function_state(func_name)
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
            if task.function_name.startswith("tellm://"):
                return await self.execute_resource(task.function_name, task.parameters)
            if task.processes:
                return await self.execute_processes(task)
            if task.function_name in self.functions_db:
                return await self._execute_registered_function(
                    task.function_name, task.parameters
                )
            if task.code:
                task.processes = [
                    {
                        "name": task.function_name,
                        "language": "python",
                        "entrypoint": task.function_name,
                        "parameters": task.parameters,
                        "code": task.code,
                    }
                ]
                return await self.execute_processes(task)
            return await self.evolve_function(task)
        elif task.type == TaskType.CRON: return {"status": "cron_set", "schedule": task.schedule}
        elif task.type == TaskType.EVENT_TRIGGER: return {"status": "event_set", "function": task.function_name}

    def transcribe(self, audio_data: bytes, suffix: str = ".wav") -> str:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
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

    @staticmethod
    def _render_autoimprovement_data(data: Dict[str, Any], message: Dict[str, Any]) -> Dict[str, Any]:
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        findings = data.get("findings") if isinstance(data.get("findings"), list) else []
        patches = data.get("patches") if isinstance(data.get("patches"), list) else []
        tests = data.get("tests") if isinstance(data.get("tests"), dict) else {}
        blocks = [
            {"type": "text", "text": message.get("summary", "")},
            {"type": "metric", "label": "Resources", "value": summary.get("checked_resources", 0)},
            {"type": "metric", "label": "Findings", "value": len(findings)},
            {"type": "metric", "label": "Pending patches", "value": len(patches)},
            {"type": "metric", "label": "Auto applied", "value": summary.get("auto_applied", 0)},
        ]
        if findings:
            blocks.append(
                {
                    "type": "table",
                    "columns": ["severity", "type", "uri", "problem", "recommendation"],
                    "rows": [
                        {
                            "severity": item.get("severity", ""),
                            "type": item.get("type", ""),
                            "uri": item.get("uri", ""),
                            "problem": item.get("problem", ""),
                            "recommendation": item.get("recommendation", ""),
                        }
                        for item in findings
                    ],
                }
            )
        else:
            blocks.append({"type": "text", "text": "No findings."})
        if patches:
            blocks.append(
                {
                    "type": "table",
                    "columns": ["id", "status", "risk", "uri", "description"],
                    "rows": [
                        {
                            "id": item.get("id", ""),
                            "status": item.get("status", ""),
                            "risk": item.get("risk", ""),
                            "uri": item.get("uri", ""),
                            "description": item.get("description", ""),
                        }
                        for item in patches
                    ],
                }
            )
        blocks.append({"type": "key_value", "items": tests})
        return {
            "title": str(message.get("title") or "Autoimprovement report"),
            "blocks": blocks,
        }

    @staticmethod
    def _render_data_from_service_result(result: Any) -> Dict[str, Any]:
        if not isinstance(result, dict):
            return {}
        message = result.get("message")
        data = result.get("data")
        if not isinstance(message, dict) or not isinstance(data, dict):
            return {}
        if result.get("type") == "system.autoimprovement.report":
            return TellmBot._render_autoimprovement_data(data, message)
        blocks = []
        summary = message.get("summary")
        details = message.get("details")
        if summary:
            blocks.append({"type": "text", "text": summary})
        blocks.append({"type": "key_value", "items": data})
        if result.get("uri"):
            blocks.append({"type": "text", "text": "Usługa: " + str(result["uri"])})
        if details:
            blocks.append({"type": "text", "text": details})
        if result.get("errors"):
            blocks.append({"type": "json", "data": {"errors": result["errors"]}})
        return {
            "title": str(message.get("title") or result.get("type") or "Wynik usługi"),
            "blocks": blocks,
        }

    def generate_view(self, transcription: str, task: Task, result: Any) -> ViewData:
        render_data = self._render_data_from_service_result(result)
        if not render_data:
            render_data = task.view if isinstance(task.view, dict) else {}
        if not render_data:
            render_data = {
                "title": "Wynik",
                "blocks": [
                    {"type": "text", "text": transcription},
                    {"type": "json", "data": result},
                ],
            }
        view_elements = [{"type": "transcription", "text": transcription}, {"type": "task", "data": {"type": task.type.value, "function": task.function_name, "parameters": task.parameters, "processes": task.processes, "view": render_data}}, {"type": "result", "data": result}, {"type": "code", "code": task.code}, {"type": "render_data", "data": render_data}]
        score = self.performance_scores.get(task.function_name, 0.0)
        view = ViewData(transcription=transcription, task=task, result=result, generated_code=task.code, performance_score=score, view_elements=view_elements, render_data=render_data)
        html = self.save_view(view)
        view.view_elements.append({"type": "html", "html": html})
        return view
