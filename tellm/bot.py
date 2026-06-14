"""tellm v4"""
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version as package_version
import inspect
import html as html_lib
import json
import os
import re
import socket
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from urllib import error as url_error
from urllib import parse as url_parse
from urllib import request as url_request

from .config import Config, load_config
from .improvement import AutoimprovementRunner, ExecutionHistoryStore
from .registry import (
    RegistryPermissionError,
    ResourceRegistry,
    registry_manifest_schema,
    service_result,
    service_result_schema,
)

class TaskType(Enum):
    NOW = "now"
    CRON = "cron"
    EVENT_TRIGGER = "event_trigger"


class WeatherLocationResolutionError(ValueError):
    def __init__(self, city: str, country: str, normalized_country: str, attempts: List[Dict[str, Any]]):
        super().__init__("Location not found: " + city)
        self.city = city
        self.country = country
        self.normalized_country = normalized_country
        self.attempts = attempts


class WeatherLocationTooBroadError(ValueError):
    def __init__(self, location: str, country: str, normalized_country: str):
        super().__init__("Location is too broad for current weather: " + location)
        self.location = location
        self.country = country
        self.normalized_country = normalized_country


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

    def get_view_record(self, view_id: int) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT id, transcription, task_data, result_data, html FROM views WHERE id = ?",
            (view_id,),
        )
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0],
            "transcription": row[1],
            "task": json.loads(row[2] or "{}"),
            "result": json.loads(row[3] or "null"),
            "html": row[4],
        }

    @staticmethod
    def _is_text_content_type(content_type: str) -> bool:
        base = (content_type or "").split(";", 1)[0].lower()
        return base.startswith("text/") or base in {
            "application/json",
            "application/javascript",
            "application/xml",
            "application/yaml",
            "application/x-yaml",
        }

    def _storage_base_path(self, base: str) -> Path:
        project_root = Path(__file__).resolve().parent.parent
        home = Path.home()
        bases = {
            "project": project_root,
            "workspace": Path.cwd(),
            "user_data": home / ".local" / "share" / "tellm",
            "cache": home / ".cache" / "tellm",
            "temp": Path(tempfile.gettempdir()) / "tellm",
            "config": home / ".config" / "tellm",
        }
        return bases.get(base or "project", project_root)

    @staticmethod
    def _value_preview(value: Any) -> Dict[str, Any]:
        if isinstance(value, str):
            return {"type": "string", "length": len(value)}
        if isinstance(value, list):
            return {"type": "array", "length": len(value)}
        if isinstance(value, dict):
            return {"type": "object", "keys": sorted(str(key) for key in value.keys())}
        return {"type": type(value).__name__}

    def resolve_resource_document(
        self,
        resource: Dict[str, Any],
        include_value: bool = False,
        max_bytes: int = 65536,
        route_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        permissions = resource.get("permissions") or {}
        if not bool(permissions.get("llm_read", True)):
            raise RegistryPermissionError("Permission denied for read on %s" % resource.get("uri", ""))

        storage = resource.get("storage") or {}
        storage_type = str(storage.get("type", ""))
        content_type = str(resource.get("content_type") or "")
        resolved: Dict[str, Any] = {
            "requested_uri": (route_info or {}).get("requested_uri", resource.get("uri", "")),
            "canonical_uri": (route_info or {}).get("canonical_uri", resource.get("canonical_uri") or resource.get("uri", "")),
            "uri": resource.get("uri", ""),
            "kind": resource.get("kind", ""),
            "name": resource.get("name", ""),
            "domain": resource.get("domain", ""),
            "storage_type": storage_type,
            "storage": storage,
            "content_type": content_type,
            "media_type": resource.get("media_type", ""),
            "relations": resource.get("relations") or {},
            "dependencies": resource.get("dependencies") or [],
            "capabilities": resource.get("capabilities") or [],
            "llm_read": bool(permissions.get("llm_read")),
            "llm_execute": bool(permissions.get("llm_execute")),
            "requires_confirmation": bool(permissions.get("requires_confirmation")),
            "danger_level": permissions.get("danger_level", "read_only"),
            "route": (route_info or {}).get("route", []),
            "warnings": (route_info or {}).get("warnings", []),
            "input": (route_info or {}).get("input", {}),
            "value_included": False,
        }
        result: Dict[str, Any] = {"resource": resource, "resolved": resolved}
        value: Any = None

        if resource.get("kind") == "command":
            resolved["command"] = {
                "template": resource.get("command_template", ""),
                "schema_based_input": bool(resource.get("input_schema")),
                "raw_shell_from_llm_allowed": False,
                "execution_allowed": bool(permissions.get("llm_execute")),
            }
        if resource.get("kind") == "package":
            resolved["package"] = {
                "ecosystem": resource.get("ecosystem", ""),
                "import_name": resource.get("import_name", ""),
                "installed_version": (resource.get("metadata") or {}).get("installed_version", ""),
                "network": bool(permissions.get("network")),
            }

        if storage_type == "local_file":
            path = str(storage.get("path", ""))
            base = str(storage.get("base") or "project")
            absolute_path = Path(path) if os.path.isabs(path) else self._storage_base_path(base) / path
            exists = absolute_path.exists()
            file_info: Dict[str, Any] = {
                "path": path,
                "base": base,
                "absolute_path": str(absolute_path),
                "exists": exists,
            }
            if exists:
                file_info["size_bytes"] = absolute_path.stat().st_size
            resolved["local_file"] = file_info
            if include_value and exists:
                if not self._is_text_content_type(content_type):
                    resolved["value_omitted_reason"] = "binary_or_non_text_content"
                elif file_info.get("size_bytes", 0) > max_bytes:
                    resolved["value_omitted_reason"] = "file_exceeds_max_bytes"
                    resolved["max_bytes"] = max_bytes
                else:
                    with absolute_path.open("r", encoding="utf-8", errors="replace") as handle:
                        value = handle.read(max_bytes)
        elif storage_type == "inline":
            if include_value:
                value = storage.get("content")
            else:
                resolved["inline"] = self._value_preview(storage.get("content"))
        elif storage_type == "sqlite":
            table = str(storage.get("table", ""))
            column = str(storage.get("column", ""))
            selector = storage.get("selector")
            resolved["sqlite"] = {
                "table": table,
                "column": column,
                "selector": selector,
                "supported": table in {"views", "autoimprovement_reports"},
            }
            if table == "views":
                view_id = storage.get("id") or (resource.get("metadata") or {}).get("view_id")
                record = self.get_view_record(int(view_id)) if view_id is not None else None
                resolved["sqlite"]["id"] = view_id
                resolved["sqlite"]["found"] = record is not None
                if include_value and record is not None:
                    if column == "html":
                        value = record.get("html")
                    elif column == "result_data":
                        value = record.get("result")
                    elif column == "task_data":
                        value = record.get("task")
                    else:
                        value = record
            elif table == "autoimprovement_reports" and selector == "latest":
                if include_value:
                    if column == "html":
                        value = self.get_latest_autoimprovement_html()
                    else:
                        value = self.get_latest_autoimprovement_report()
        elif include_value:
            entry = self.registry.get(str(resource.get("uri", "")))
            if entry is not None and entry.value_ref is not None and entry.callable_ref is None:
                value = self.registry.read(entry.uri)

        if include_value:
            result["value"] = value
            resolved["value_included"] = value is not None
            if value is not None:
                resolved["value_preview"] = self._value_preview(value)
        return result

    def resolve_resource(
        self,
        uri: str,
        input_data: Optional[Dict[str, Any]] = None,
        include_value: bool = False,
        max_bytes: int = 65536,
    ) -> Dict[str, Any]:
        route_info = self.registry.resolve_uri(uri, input_data or {})
        resource = route_info["resource"]
        return self.resolve_resource_document(
            resource,
            include_value=include_value,
            max_bytes=max_bytes,
            route_info=route_info,
        )

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

    @staticmethod
    def _package_version(package_name: str) -> str:
        try:
            return package_version(package_name)
        except PackageNotFoundError:
            return ""

    def _register_file_resource(
        self,
        uri: str,
        name: str,
        path: str,
        content_type: str,
        description: str,
        tags: List[str],
    ) -> None:
        self.registry.register_value(
            uri=uri,
            kind="file",
            name=name,
            value={"path": path, "content_type": content_type},
            description=description,
            value_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content_type": {"type": "string"},
                },
                "required": ["path"],
            },
            permissions={
                "llm_read": True,
                "filesystem_read": True,
                "danger_level": "read_only",
            },
            tags=tags,
            storage={"type": "local_file", "base": "project", "path": path},
            content_type=content_type,
        )

    def _register_package_resource(
        self,
        package_name: str,
        import_name: str,
        capabilities: List[str],
        network: bool = False,
    ) -> None:
        installed_version = self._package_version(package_name)
        self.registry.register_value(
            uri="tellm://package/python/" + package_name,
            kind="package",
            name=package_name,
            value={
                "ecosystem": "python",
                "name": package_name,
                "import_name": import_name,
                "version": installed_version,
                "capabilities": capabilities,
            },
            description="Python package dependency: " + package_name,
            value_schema={"type": "object"},
            permissions={
                "llm_read": True,
                "llm_execute": False,
                "network": network,
                "danger_level": "read_only",
            },
            tags=["package", "python"] + capabilities,
            ecosystem="python",
            import_name=import_name,
            capabilities=capabilities,
            metadata={"installed_version": installed_version},
        )

    def _register_artifact_resources(self) -> None:
        self._register_file_resource(
            "tellm://file/project/tellm/server.py",
            "project.tellm.server.py",
            "tellm/server.py",
            "text/x-python",
            "Project source file for the tellm WebSocket and HTTP registry server.",
            ["file", "project", "python", "server"],
        )
        self._register_file_resource(
            "tellm://file/project/tellm/bot.py",
            "project.tellm.bot.py",
            "tellm/bot.py",
            "text/x-python",
            "Project source file for the tellm bot, services, STT/TTS and registry initialization.",
            ["file", "project", "python", "bot"],
        )
        self._register_file_resource(
            "tellm://file/project/tellm/registry/aliases.yaml",
            "project.tellm.registry.aliases_yaml",
            "tellm/registry/aliases.yaml",
            "application/x-yaml",
            "Declarative URI alias migration map for the tellm registry.",
            ["file", "project", "registry", "alias", "yaml"],
        )
        self._register_file_resource(
            "tellm://file/output/test-audio/tellm-pl-pogoda.webm",
            "output.test_audio.tellm_pl_pogoda_webm",
            "output/test-audio/tellm-pl-pogoda.webm",
            "audio/webm",
            "Physical local file for the Polish weather query audio sample.",
            ["file", "audio", "test", "weather"],
        )
        self.registry.register_value(
            uri="tellm://artifact/audio/weather-query-sample",
            kind="artifact",
            name="weather_query_sample",
            value={
                "path": "output/test-audio/tellm-pl-pogoda.webm",
                "media_type": "audio/webm",
                "description": "Przykładowe nagranie zapytania pogodowego.",
            },
            description="Logical audio artifact for testing the weather query workflow.",
            value_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "media_type": {"type": "string"},
                    "duration_sec": {"type": "number"},
                },
                "required": ["path", "media_type"],
            },
            permissions={
                "llm_read": True,
                "filesystem_read": True,
                "filesystem_write": False,
                "danger_level": "read_only",
            },
            tags=["artifact", "audio", "test", "weather"],
            storage={"type": "local_file", "base": "project", "path": "output/test-audio/tellm-pl-pogoda.webm"},
            relations={
                "physical_file": ["tellm://file/output/test-audio/tellm-pl-pogoda.webm"],
                "used_by": ["tellm://service/audio/transcribe"],
            },
            media_type="audio/webm",
            content_type="audio/webm",
        )
        self.registry.register_value(
            uri="tellm://media/audio/weather-query-sample",
            kind="media",
            name="weather_query_sample_audio",
            value={
                "path": "output/test-audio/tellm-pl-pogoda.webm",
                "media_type": "audio/webm",
            },
            description="Media resource view of the weather query audio sample.",
            value_schema={"type": "object"},
            permissions={
                "llm_read": True,
                "filesystem_read": True,
                "danger_level": "read_only",
            },
            tags=["media", "audio", "test", "weather"],
            storage={"type": "local_file", "base": "project", "path": "output/test-audio/tellm-pl-pogoda.webm"},
            relations={"same_as": ["tellm://artifact/audio/weather-query-sample"]},
            media_type="audio/webm",
            content_type="audio/webm",
        )
        self.registry.register_value(
            uri="tellm://artifact/html/latest-autoimprovement-report",
            kind="artifact",
            name="latest_autoimprovement_report_html",
            value=lambda: self.get_latest_autoimprovement_html() or "",
            description="Logical HTML artifact for the latest autoimprovement report.",
            value_schema={"type": "string"},
            permissions={"llm_read": True, "danger_level": "read_only"},
            tags=["artifact", "html", "autoimprovement", "report"],
            storage={
                "type": "sqlite",
                "table": "autoimprovement_reports",
                "column": "html",
                "selector": "latest",
            },
            relations={
                "same_as": ["tellm://view/system/autoimprovement-report/latest"],
                "derived_from": ["tellm://data/system/autoimprovement-report/latest"],
            },
            content_type="text/html",
        )
        self.registry.register_value(
            uri="tellm://command/shell/pytest",
            kind="command",
            name="shell.pytest",
            value={"command_template": "python -m pytest -q {path}"},
            description="Declared shell command for running pytest. It is discoverable but not directly executable by the current registry dispatcher.",
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string", "default": "tests"}},
                "additionalProperties": False,
            },
            value_schema={"type": "object"},
            permissions={
                "llm_read": True,
                "llm_execute": False,
                "shell": True,
                "filesystem_read": True,
                "filesystem_write": False,
                "network": False,
                "requires_confirmation": True,
                "danger_level": "medium",
            },
            tags=["command", "shell", "pytest", "test"],
            command_template="python -m pytest -q {path}",
            capabilities=["run_tests"],
            metadata={"execution_mode": "declared_only"},
        )
        self.registry.register_value(
            uri="tellm://command/python/compile-project",
            kind="command",
            name="python.compile_project",
            value={"command_template": "python -m py_compile {paths}"},
            description="Declared Python compile command for selected project files.",
            input_schema={
                "type": "object",
                "properties": {"paths": {"type": "string"}},
                "required": ["paths"],
                "additionalProperties": False,
            },
            value_schema={"type": "object"},
            permissions={
                "llm_read": True,
                "llm_execute": False,
                "shell": True,
                "filesystem_read": True,
                "filesystem_write": False,
                "network": False,
                "requires_confirmation": True,
                "danger_level": "medium",
            },
            tags=["command", "python", "compile"],
            command_template="python -m py_compile {paths}",
            capabilities=["compile_python"],
            metadata={"execution_mode": "declared_only"},
        )
        for package_name, import_name, capabilities, network in [
            ("litellm", "litellm", ["llm_client"], True),
            ("websockets", "websockets", ["websocket_server"], False),
            ("faster-whisper", "faster_whisper", ["speech_to_text"], False),
            ("pyttsx3", "pyttsx3", ["text_to_speech"], False),
            ("python-dotenv", "dotenv", ["env_config"], False),
            ("jsonschema", "jsonschema", ["validate_json_schema"], False),
        ]:
            self._register_package_resource(package_name, import_name, capabilities, network)
        self.registry.register_value(
            uri="tellm://prompt/validator/workflow-result",
            kind="prompt",
            name="validator.workflow_result",
            value={
                "content": "Sprawdź, czy wynik JSON jest zgodny z renderem HTML i logami workflow. Zwróć JSON status=ok|repair.",
            },
            description="Prompt resource used to validate workflow result JSON, renderer HTML and logs.",
            input_schema={
                "type": "object",
                "properties": {
                    "result_json": {"type": "object"},
                    "html": {"type": "string"},
                    "logs": {"type": "array"},
                },
                "required": ["result_json", "html"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "answer": {"type": "string"},
                    "reason": {"type": "string"},
                    "view": {},
                    "result": {},
                },
            },
            value_schema={"type": "object"},
            permissions={"llm_read": True, "danger_level": "read_only"},
            tags=["prompt", "validator", "workflow"],
            storage={
                "type": "inline",
                "content": "Sprawdź, czy wynik JSON jest zgodny z renderem HTML i logami workflow. Zwróć JSON status=ok|repair.",
            },
            relations={"used_by": ["tellm://service/render/html"]},
        )
        self.registry.register_value(
            uri="tellm://prompt/repair/render-data",
            kind="prompt",
            name="repair.render_data",
            value={"content": "Napraw wyłącznie strukturę view/result zgodnie z lokalnymi danymi usługi."},
            description="Prompt resource for renderer data repair cycles.",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            value_schema={"type": "object"},
            permissions={"llm_read": True, "danger_level": "read_only"},
            tags=["prompt", "repair", "renderer"],
            storage={
                "type": "inline",
                "content": "Napraw wyłącznie strukturę view/result zgodnie z lokalnymi danymi usługi.",
            },
            relations={"used_by": ["tellm://prompt/validator/workflow-result"]},
        )
        self.registry.register_value(
            uri="tellm://python/module/tellm.bot",
            kind="python",
            name="module.tellm.bot",
            value={"module": "tellm.bot"},
            description="Python module containing TellmBot and workflow service implementations.",
            value_schema={"type": "object"},
            permissions={"llm_read": True, "filesystem_read": True, "danger_level": "read_only"},
            tags=["python", "module", "bot"],
            relations={"source_file": ["tellm://file/project/tellm/bot.py"]},
        )
        self.registry.register_value(
            uri="tellm://python/class/tellm.registry.core.ResourceRegistry",
            kind="python",
            name="class.tellm.registry.core.ResourceRegistry",
            value={
                "module": "tellm.registry.core",
                "qualname": "ResourceRegistry",
            },
            description="Python class implementing the tellm local resource registry.",
            value_schema={"type": "object"},
            permissions={"llm_read": True, "filesystem_read": True, "danger_level": "read_only"},
            tags=["python", "class", "registry"],
        )

    def _register_uri_aliases(self) -> None:
        self.registry.register_alias(
            uri="tellm://function/weather_wejherowo",
            target="tellm://service/weather/current",
            status="deprecated",
            default_input={"location": "Wejherowo", "country": "PL"},
            description="Deprecated city-specific weather function alias.",
            deprecation={
                "since": "2026-06-14",
                "remove_after": "2026-09-01",
                "message": "Use tellm://service/weather/current with input.location instead.",
            },
            message="Stara funkcja weather_wejherowo została zastąpiona przez generyczną usługę weather.current.",
        )
        self.registry.register_alias(
            uri="tellm://function/get_weather_wejherowo",
            target="tellm://service/weather/current",
            status="deprecated",
            default_input={"location": "Wejherowo", "country": "PL"},
            description="Deprecated generated weather function alias.",
            deprecation={
                "since": "2026-06-14",
                "remove_after": "2026-09-01",
                "message": "Use tellm://service/weather/current with input.location instead.",
            },
            message="Generated per-city weather functions are redirected to the canonical weather.current service.",
        )
        self.registry.register_alias(
            uri="tellm://service/pogoda/current",
            target="tellm://service/weather/current",
            status="alias",
            description="Polish service alias for current weather.",
            message="Use canonical URI tellm://service/weather/current.",
        )
        self.registry.register_alias(
            uri="tellm://service/weather/get",
            target="tellm://service/weather/current",
            status="deprecated",
            input_map={"city": "location", "country_code": "country"},
            description="Deprecated weather.get shape with legacy input names.",
            deprecation={
                "since": "2026-06-14",
                "remove_after": "2026-09-01",
                "message": "Use tellm://service/weather/current and input.location/input.country.",
            },
            message="Legacy weather.get input is mapped to weather.current.",
        )
        self.registry.register_value(
            uri="tellm://service/old/weather",
            kind="tombstone",
            name="old.weather",
            value={
                "replacement": "tellm://service/weather/current",
                "message": "This service was removed. Use replacement URI.",
            },
            description="Removed weather service tombstone.",
            canonical_uri="tellm://service/weather/current",
            replacement="tellm://service/weather/current",
            permissions={"llm_read": True, "danger_level": "read_only"},
            tags=["tombstone", "removed", "weather"],
            status="removed",
            metadata={"message": "This service was removed. Use tellm://service/weather/current."},
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
            capabilities=["domain.check", "real_world_data.domain", "network.rdap"],
        )
        self.registry.register_callable(
            uri="tellm://service/price/search",
            kind="service",
            name="price.search",
            func=self._registry_price_search,
            description=(
                "Search a supported public commerce source for visible product prices. "
                "Use this for current price questions instead of domain.check or generated code."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "product": {"type": "string"},
                    "site": {"type": "string"},
                    "url": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
                "additionalProperties": True,
            },
            output_schema={"type": "object", "required": ["ok", "type", "data", "message", "errors"]},
            permissions={
                "llm_read": True,
                "llm_execute": True,
                "requires_confirmation": False,
                "network": True,
                "danger_level": "network",
            },
            tags=["service", "price", "commerce", "network", "real_world_data"],
            capabilities=[
                "price.search",
                "commerce.price",
                "real_world_data.price",
                "network.http",
            ],
            metadata={
                "result_type": "price.search.result",
                "requires_real_world_data": True,
                "allowed_sources": ["allegro.pl", "skapiec.pl"],
                "disallowed_sources": ["local_simulation", "mock", "test", "llm_generated", "generated"],
            },
            data_policy={
                "requires_real_world_data": True,
                "allowed_sources": ["allegro.pl", "skapiec.pl"],
                "disallowed_sources": ["local_simulation", "mock", "test", "llm_generated", "generated"],
            },
            render={
                "default_view": "tellm://view/price/search",
                "renderer": "auto",
                "template": "price_search",
            },
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
                    "location": {"type": "string"},
                    "country": {"type": "string"},
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                },
                "required": ["location"],
                "additionalProperties": True,
            },
            output_schema={"type": "object", "required": ["ok", "type", "data", "message", "errors"]},
            permissions={
                "llm_read": True,
                "llm_execute": True,
                "requires_confirmation": False,
                "network": True,
                "danger_level": "network",
            },
            tags=["service", "weather", "network", "real_world_data"],
            capabilities=[
                "weather.current",
                "real_world_data.weather",
                "location.current_conditions",
            ],
            metadata={
                "result_type": "weather.current.result",
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
            capabilities=["system.autoimprove", "registry.audit", "autoimprovement.audit"],
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
        self._register_uri_aliases()
        self._register_artifact_resources()

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

    @staticmethod
    def _http_text(url: str, timeout: int = 8) -> str:
        req = url_request.Request(
            url,
            headers={
                "User-Agent": "tellm/4 (+https://github.com/wronai/tellm)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pl,en;q=0.8",
            },
        )
        with url_request.urlopen(req, timeout=timeout) as response:
            payload = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
        return payload.decode(charset, "replace")

    @staticmethod
    def _normalize_country_code(country: str) -> str:
        value = str(country or "").strip()
        if not value:
            return ""
        upper = value.upper().replace(".", "")
        aliases = {
            "POLAND": "PL",
            "POLSKA": "PL",
            "RZECZPOSPOLITA POLSKA": "PL",
            "PL": "PL",
            "GERMANY": "DE",
            "NIEMCY": "DE",
            "DEUTSCHLAND": "DE",
            "DE": "DE",
            "UNITED STATES": "US",
            "USA": "US",
            "US": "US",
            "UNITED KINGDOM": "GB",
            "UK": "GB",
            "GB": "GB",
        }
        return aliases.get(upper, upper if len(upper) == 2 else "")

    @classmethod
    def _is_country_level_weather_location(cls, location: str) -> bool:
        value = str(location or "").strip()
        if not value:
            return False
        normalized = re.sub(r"\s+", " ", value.casefold().replace(".", " ")).strip()
        countries = {
            "polska",
            "poland",
            "rzeczpospolita polska",
            "niemcy",
            "germany",
            "deutschland",
            "united states",
            "usa",
            "stany zjednoczone",
            "united kingdom",
            "uk",
            "wielka brytania",
            "great britain",
            "france",
            "francja",
            "spain",
            "hiszpania",
            "italy",
            "wlochy",
            "włochy",
            "czechy",
            "czech republic",
            "slovakia",
            "slowacja",
            "słowacja",
            "ukraine",
            "ukraina",
            "europe",
            "europa",
            "world",
            "swiat",
            "świat",
        }
        if normalized in countries:
            return True
        compact = normalized.replace(" ", "").upper()
        return len(compact) == 2 and cls._normalize_country_code(compact) == compact

    @staticmethod
    def _score_geocode_result(result: Dict[str, Any], city: str, country_code: str) -> float:
        score = 0.0
        if country_code and str(result.get("country_code", "")).upper() == country_code:
            score += 1000.0
        if str(result.get("name", "")).casefold() == city.casefold():
            score += 100.0
        try:
            score += min(float(result.get("population") or 0), 1000000.0) / 1000000.0
        except Exception:
            pass
        return score

    def _geocode_city(self, city: str, country: str = "") -> Dict[str, Any]:
        raw_country = str(country or "").strip()
        normalized_country = self._normalize_country_code(raw_country)
        attempts: List[Dict[str, Any]] = []

        def fetch(country_code: str) -> List[Dict[str, Any]]:
            query = {
                "name": city,
                "count": 10,
                "language": "pl",
                "format": "json",
            }
            if country_code:
                query["countryCode"] = country_code
            url = "https://geocoding-api.open-meteo.com/v1/search?" + url_parse.urlencode(query)
            started = time.perf_counter()
            data = self._http_json(url)
            duration_ms = int(round((time.perf_counter() - started) * 1000))
            results = data.get("results") or []
            attempts.append(
                {
                    "provider": "open_meteo_geocoding",
                    "query": {
                        "name": city,
                        "country": raw_country,
                        "normalized_country": country_code,
                    },
                    "result_count": len(results),
                    "duration_ms": duration_ms,
                }
            )
            return [item for item in results if isinstance(item, dict)]

        candidates: List[Dict[str, Any]] = []
        if normalized_country:
            candidates.extend(fetch(normalized_country))
        if not candidates:
            candidates.extend(fetch(""))
        if not candidates:
            raise WeatherLocationResolutionError(city, raw_country, normalized_country, attempts)

        selected = max(
            candidates,
            key=lambda item: self._score_geocode_result(item, city, normalized_country),
        )
        selected = dict(selected)
        selected["_diagnostics"] = {
            "provider": "open_meteo_geocoding",
            "query": {
                "name": city,
                "country": raw_country,
                "normalized_country": normalized_country,
            },
            "attempts": attempts,
        }
        return selected

    def _registry_weather_current(self, params: Dict[str, Any]) -> Dict[str, Any]:
        uri = "tellm://service/weather/current"
        city = str(params.get("city") or params.get("location") or "").strip()
        requested_country = str(params.get("country") or "PL").strip()
        country = self._normalize_country_code(requested_country) or requested_country.upper()
        geocoding_diagnostics: Dict[str, Any] = {
            "provider": "open_meteo_geocoding",
            "query": {
                "name": city,
                "country": requested_country,
                "normalized_country": country,
            },
            "attempts": [],
        }
        provider_started = time.perf_counter()
        forecast_duration_ms = None
        try:
            latitude = params.get("latitude")
            longitude = params.get("longitude")
            location = {}
            if latitude is None or longitude is None:
                if not city:
                    raise ValueError("city or latitude/longitude is required")
                if self._is_country_level_weather_location(city):
                    raise WeatherLocationTooBroadError(city, requested_country, country)
                location = self._geocode_city(city, requested_country)
                geocoding_diagnostics = location.get("_diagnostics") or geocoding_diagnostics
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
            forecast_started = time.perf_counter()
            weather = self._http_json(forecast_url)
            forecast_duration_ms = int(round((time.perf_counter() - forecast_started) * 1000))
            current = weather.get("current") or {}
            code = current.get("weather_code")
            description = self._weather_code_description(code)
            temperature = current.get("temperature_2m")
            fetched_at = datetime.now(timezone.utc).isoformat()
            summary = "Aktualnie %s°C, %s." % (temperature, description)
            geocoding_duration_ms = sum(
                int(item.get("duration_ms") or 0)
                for item in geocoding_diagnostics.get("attempts", [])
                if isinstance(item, dict)
            )
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
                    "provider": "open_meteo",
                    "geocoding": geocoding_diagnostics,
                    "timings": {
                        "geocoding_ms": geocoding_duration_ms,
                        "forecast_ms": forecast_duration_ms,
                        "provider_total_ms": int(round((time.perf_counter() - provider_started) * 1000)),
                    },
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
            detail = str(exc)
            lowered = detail.lower()
            code = "WEATHER_PROVIDER_UNAVAILABLE"
            if isinstance(exc, PermissionError) or (
                "network" in lowered
                and (
                    "not allowed" in lowered
                    or "denied" in lowered
                    or "cannot access" in lowered
                    or "requires network" in lowered
                )
            ):
                code = "NETWORK_ACCESS_NOT_ALLOWED"
            elif isinstance(exc, WeatherLocationResolutionError):
                code = "LOCATION_NOT_FOUND"
                geocoding_diagnostics = {
                    "provider": "open_meteo_geocoding",
                    "query": {
                        "name": exc.city,
                        "country": exc.country,
                        "normalized_country": exc.normalized_country,
                    },
                    "attempts": exc.attempts,
                }
            elif isinstance(exc, WeatherLocationTooBroadError):
                code = "LOCATION_TOO_BROAD"
                geocoding_diagnostics = {
                    "provider": "tellm_location_normalizer",
                    "query": {
                        "name": exc.location,
                        "country": exc.country,
                        "normalized_country": exc.normalized_country,
                    },
                    "attempts": [],
                }
            error_payload: Dict[str, Any] = {
                "code": code,
                "source": uri,
                "detail": detail,
                "provider": "open_meteo_geocoding"
                if code == "LOCATION_NOT_FOUND"
                else "tellm_location_normalizer"
                if code == "LOCATION_TOO_BROAD"
                else "open_meteo",
                "recoverable": True,
            }
            if code in {"LOCATION_NOT_FOUND", "LOCATION_TOO_BROAD"}:
                error_payload["query"] = geocoding_diagnostics["query"]
                error_payload["attempts"] = geocoding_diagnostics["attempts"]
            if code == "LOCATION_TOO_BROAD":
                title = "Podaj konkretną lokalizację"
                summary = "Zapytanie wskazuje zbyt szeroki obszar. Do aktualnej pogody podaj miasto albo współrzędne."
                details = "weather.current nie wybiera arbitralnego punktu dla kraju, żeby nie pokazywać mylącej pogody."
            else:
                title = "Nie udało się pobrać pogody"
                summary = "Usługa pogodowa wymaga dostępu do sieci lub providera, ale nie udało się pobrać realnych danych."
                details = "Skonfiguruj provider pogody albo zezwól tej usłudze na kontrolowany dostęp HTTP."
            result = service_result(
                ok=False,
                result_type="weather.current.result",
                uri=uri,
                data=None,
                title=title,
                summary=summary,
                details=details,
                errors=[error_payload],
                view={"renderer": "auto", "template": "status_card", "severity": "error"},
                meta={"source": None, "fetched_at": None},
            )
            result["input"] = {
                "location": city,
                "country": country,
                "requested_country": requested_country,
                "geocoding": geocoding_diagnostics,
            }
            return result

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

    @staticmethod
    def _normalize_price_site(site: str) -> str:
        domain = TellmBot._normalize_domain(str(site or ""))
        if domain.startswith("www."):
            domain = domain[4:]
        return domain

    @staticmethod
    def _commerce_search_url(site: str, query: str) -> str:
        encoded_plus = url_parse.quote_plus(query)
        if site == "allegro.pl":
            return "https://allegro.pl/listing?string=" + encoded_plus
        if site == "skapiec.pl":
            return "https://www.skapiec.pl/szukaj/w_calym_serwisie/" + url_parse.quote(query)
        return ""

    @classmethod
    def _skapiec_category_url_from_document(cls, document: str, query: str) -> Optional[Dict[str, str]]:
        query_tokens = set(cls._price_relevance_tokens(query))
        if not query_tokens:
            return None
        candidates: List[Dict[str, Any]] = []
        anchor_pattern = re.compile(
            r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
            flags=re.IGNORECASE | re.DOTALL,
        )
        for match in anchor_pattern.finditer(document):
            href = html_lib.unescape(match.group(1))
            if "/cat/" not in href:
                continue
            label = cls._text_from_html(match.group(2))
            label_tokens = set(cls._price_relevance_tokens(label))
            matched = sorted(query_tokens & label_tokens)
            if not matched:
                continue
            score = len(matched) * 100 - len(label_tokens)
            if label.lower() == str(query or "").strip().lower():
                score += 50
            candidates.append(
                {
                    "score": score,
                    "label": label,
                    "url": url_parse.urljoin("https://www.skapiec.pl/", href),
                    "matched_terms": matched,
                }
            )
        if not candidates:
            return None
        best = sorted(candidates, key=lambda item: item["score"], reverse=True)[0]
        return {
            "label": str(best["label"]),
            "url": str(best["url"]),
            "matched_terms": list(best["matched_terms"]),
        }

    @staticmethod
    def _text_from_html(document: str) -> str:
        text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", document)
        text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
        text = re.sub(r"(?is)<(nav|header|footer|aside)[^>]*>.*?</\1>", " ", text)
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = html_lib.unescape(text)
        text = text.replace("\xa0", " ")
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _parse_price_amount(raw: str) -> Optional[float]:
        number = re.sub(r"[^0-9,.]", "", raw)
        if not number:
            return None
        if "," in number and "." in number:
            if number.rfind(",") > number.rfind("."):
                number = number.replace(".", "").replace(",", ".")
            else:
                number = number.replace(",", "")
        else:
            number = number.replace(",", ".")
        try:
            return float(number)
        except ValueError:
            return None

    @staticmethod
    def _price_relevance_tokens(query: str) -> List[str]:
        normalized = str(query or "").lower()
        normalized = re.sub(r"[^\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+", " ", normalized, flags=re.UNICODE)
        stopwords = {
            "cena",
            "ceny",
            "cene",
            "cenę",
            "koszt",
            "kosztuje",
            "aktualna",
            "aktualne",
            "aktualny",
            "dzisiaj",
            "dziś",
            "teraz",
            "na",
            "w",
            "we",
            "z",
            "ze",
        }
        tokens = []
        for token in normalized.split():
            if token in stopwords:
                continue
            if len(token) < 3 and not token.isdigit():
                continue
            tokens.append(token)
        return list(dict.fromkeys(tokens))

    @staticmethod
    def _price_relevance(snippet: str, tokens: List[str]) -> Dict[str, Any]:
        if not tokens:
            return {"ok": True, "matched_terms": []}
        lowered = snippet.lower()
        matched = [token for token in tokens if token in lowered]
        required = 1 if len(tokens) <= 2 else max(2, (len(tokens) + 1) // 2)
        return {"ok": len(matched) >= required, "matched_terms": matched}

    @classmethod
    def _extract_price_candidates(
        cls,
        document: str,
        limit: int = 10,
        query: str = "",
        diagnostics: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        text = cls._text_from_html(document)
        matches: List[Dict[str, Any]] = []
        seen = set()
        tokens = cls._price_relevance_tokens(query)
        raw_candidate_count = 0
        irrelevant_candidate_count = 0
        price_pattern = re.compile(
            r"(?<!\d)(\d{1,5}(?:[ .]\d{3})*(?:\s*[,.]\s*\d{2})?)\s*(zł|zl|PLN)\b",
            flags=re.IGNORECASE,
        )
        for match in price_pattern.finditer(text):
            amount = cls._parse_price_amount(match.group(1))
            if amount is None:
                continue
            raw_candidate_count += 1
            start = max(match.start() - 90, 0)
            end = min(match.end() + 90, len(text))
            snippet = text[start:end].strip()
            relevance = cls._price_relevance(snippet, tokens)
            if not relevance["ok"]:
                irrelevant_candidate_count += 1
                continue
            raw = match.group(0).strip()
            key = (round(amount, 2), snippet[:140])
            if key in seen:
                continue
            seen.add(key)
            matches.append(
                {
                    "amount": round(amount, 2),
                    "currency": "PLN",
                    "raw": raw,
                    "snippet": snippet,
                    "matched_terms": relevance["matched_terms"],
                }
            )
            if len(matches) >= limit:
                break
        if diagnostics is not None:
            diagnostics.update(
                {
                    "relevance_tokens": tokens,
                    "raw_candidate_count": raw_candidate_count,
                    "irrelevant_candidate_count": irrelevant_candidate_count,
                    "matched_candidate_count": len(matches),
                }
            )
        return matches

    @staticmethod
    def _price_error_result(
        uri: str,
        code: str,
        title: str,
        summary: str,
        details: str,
        detail: str,
        query: str,
        site: str,
        source_url: str,
        provider: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        error_payload: Dict[str, Any] = {
            "code": code,
            "source": uri,
            "detail": detail,
            "recoverable": True,
            "query": {"query": query, "site": site, "url": source_url},
        }
        if provider:
            error_payload["provider"] = provider
        if extra:
            error_payload.update(extra)
        result = service_result(
            ok=False,
            result_type="price.search.result",
            uri=uri,
            data=None,
            title=title,
            summary=summary,
            details=details,
            errors=[error_payload],
            view={"renderer": "auto", "template": "status_card", "severity": "error"},
            meta={"source": None, "fetched_at": None},
        )
        result["input"] = {"query": query, "site": site, "url": source_url}
        return result

    def _registry_price_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        uri = "tellm://service/price/search"
        query = str(params.get("query") or params.get("product") or "").strip()
        site = self._normalize_price_site(str(params.get("site") or ""))
        limit = int(params.get("limit") or 10)
        supported_sites = {"allegro.pl", "skapiec.pl"}
        source_url = str(params.get("url") or "").strip()
        if source_url and not site:
            site = self._normalize_price_site(source_url)
        if not source_url and site in supported_sites and query:
            source_url = self._commerce_search_url(site, query)

        started = time.perf_counter()
        try:
            if not query:
                return self._price_error_result(
                    uri,
                    "PRICE_QUERY_REQUIRED",
                    "Podaj produkt",
                    "Do sprawdzenia ceny potrzebna jest nazwa produktu.",
                    "price.search nie zgaduje produktu z pustego wejścia.",
                    "price search query is required",
                    query,
                    site,
                    source_url,
                )
            if not site:
                return self._price_error_result(
                    uri,
                    "PRICE_SITE_REQUIRED",
                    "Podaj źródło ceny",
                    "Do sprawdzenia ceny potrzebna jest konkretna obsługiwana strona, np. allegro.pl albo skapiec.pl.",
                    "price.search nie zgaduje źródła danych cenowych.",
                    "price query requires a supported commerce site",
                    query,
                    site,
                    source_url,
                )
            if site not in supported_sites or not source_url:
                return self._price_error_result(
                    uri,
                    "PRICE_SOURCE_UNSUPPORTED",
                    "Nieobsługiwane źródło ceny",
                    "Obsługiwane źródła cen to: " + ", ".join(sorted(supported_sites)) + ".",
                    "Dodaj provider dla tego sklepu albo użyj obsługiwanego źródła.",
                    "unsupported price source: " + site,
                    query,
                    site,
                    source_url,
                    extra={"supported_sites": sorted(supported_sites)},
                )

            fetch_started = time.perf_counter()
            document = self._http_text(source_url, timeout=8)
            fetch_ms = int(round((time.perf_counter() - fetch_started) * 1000))
            parse_started = time.perf_counter()
            candidate_diagnostics: Dict[str, Any] = {}
            prices = self._extract_price_candidates(
                document,
                limit=max(1, min(limit, 20)),
                query=query,
                diagnostics=candidate_diagnostics,
            )
            parse_ms = int(round((time.perf_counter() - parse_started) * 1000))
            timings = {
                "fetch_ms": fetch_ms,
                "parse_ms": parse_ms,
                "provider_total_ms": int(round((time.perf_counter() - started) * 1000)),
            }
            requested_url = source_url
            fallback_info: Optional[Dict[str, str]] = None
            if not prices and site == "skapiec.pl":
                fallback_info = self._skapiec_category_url_from_document(document, query)
                if fallback_info:
                    try:
                        fallback_fetch_started = time.perf_counter()
                        fallback_document = self._http_text(fallback_info["url"], timeout=8)
                        fallback_fetch_ms = int(round((time.perf_counter() - fallback_fetch_started) * 1000))
                        fallback_parse_started = time.perf_counter()
                        fallback_diagnostics: Dict[str, Any] = {}
                        fallback_prices = self._extract_price_candidates(
                            fallback_document,
                            limit=max(1, min(limit, 20)),
                            query=query,
                            diagnostics=fallback_diagnostics,
                        )
                        fallback_parse_ms = int(round((time.perf_counter() - fallback_parse_started) * 1000))
                        timings.update(
                            {
                                "fallback_fetch_ms": fallback_fetch_ms,
                                "fallback_parse_ms": fallback_parse_ms,
                            }
                        )
                        candidate_diagnostics = {
                            "primary": candidate_diagnostics,
                            "fallback": {
                                "provider": "skapiec_category",
                                "label": fallback_info["label"],
                                "url": fallback_info["url"],
                                "matched_terms": fallback_info["matched_terms"],
                                **fallback_diagnostics,
                            },
                        }
                        if fallback_prices:
                            source_url = fallback_info["url"]
                            prices = fallback_prices
                    except Exception as fallback_exc:
                        candidate_diagnostics["fallback_error"] = {
                            "provider": "skapiec_category",
                            "url": fallback_info["url"],
                            "detail": str(fallback_exc),
                        }
                else:
                    candidate_diagnostics["fallback"] = {
                        "provider": "skapiec_category",
                        "status": "not_found",
                    }
                timings["provider_total_ms"] = int(round((time.perf_counter() - started) * 1000))
            if not prices:
                failure_diagnostics = candidate_diagnostics.get("fallback")
                if not isinstance(failure_diagnostics, dict) or "raw_candidate_count" not in failure_diagnostics:
                    failure_diagnostics = candidate_diagnostics.get("primary", candidate_diagnostics)
                irrelevant_count = int(failure_diagnostics.get("irrelevant_candidate_count") or 0)
                raw_count = int(failure_diagnostics.get("raw_candidate_count") or 0)
                has_irrelevant_prices = raw_count > 0 and irrelevant_count >= raw_count
                code = "PRICE_RESULT_NOT_RELEVANT" if has_irrelevant_prices else "PRICE_NOT_FOUND"
                summary = (
                    "Znaleziono ceny w pobranym HTML, ale ich kontekst nie pasuje do produktu: "
                    + query
                    + "."
                    if has_irrelevant_prices
                    else "Nie znaleziono widocznej ceny PLN dla zapytania w pobranej stronie."
                )
                detail = (
                    "visible PLN prices were found, but none matched the requested product context"
                    if has_irrelevant_prices
                    else "no visible PLN prices were found in fetched HTML"
                )
                result = self._price_error_result(
                    uri,
                    code,
                    "Nie znaleziono ceny",
                    summary,
                    "Strona może renderować ceny dynamicznie, blokować pobranie albo wymagać dedykowanego providera/API.",
                    detail,
                    query,
                    site,
                    source_url,
                    provider=site,
                    extra={"candidate_diagnostics": candidate_diagnostics},
                )
                result["input"]["timings"] = timings
                result["input"]["candidate_diagnostics"] = candidate_diagnostics
                if requested_url != source_url:
                    result["input"]["requested_url"] = requested_url
                return result

            amounts = [item["amount"] for item in prices]
            fetched_at = datetime.now(timezone.utc).isoformat()
            data = {
                "query": query,
                "site": site,
                "source": site,
                "url": source_url,
                "prices": prices,
                "price_count": len(prices),
                "min_price": min(amounts),
                "max_price": max(amounts),
                "currency": "PLN",
                "fetched_at": fetched_at,
                "timings": timings,
            }
            if requested_url != source_url:
                data["requested_url"] = requested_url
                data["source_discovery"] = {
                    "provider": "skapiec_category",
                    "label": (fallback_info or {}).get("label", ""),
                    "matched_terms": (fallback_info or {}).get("matched_terms", []),
                }
            summary = "Znaleziono %d widocznych cen PLN. Zakres: %.2f-%.2f PLN." % (
                len(prices),
                data["min_price"],
                data["max_price"],
            )
            return service_result(
                ok=True,
                result_type="price.search.result",
                uri=uri,
                data=data,
                title="Ceny: " + query,
                summary=summary,
                details="To są ceny wyciągnięte z publicznie pobranego HTML źródła " + site + ".",
                errors=[],
                view={"renderer": "auto", "template": "price_search", "severity": "info"},
            )
        except Exception as exc:
            detail = str(exc)
            lowered = detail.lower()
            code = "PRICE_SOURCE_UNAVAILABLE"
            if isinstance(exc, PermissionError) or (
                "network" in lowered
                and ("not allowed" in lowered or "denied" in lowered or "cannot access" in lowered)
            ):
                code = "NETWORK_ACCESS_NOT_ALLOWED"
            result = self._price_error_result(
                uri,
                code,
                "Nie udało się pobrać ceny",
                "Nie udało się pobrać realnych danych cenowych z wybranego źródła.",
                "Źródło może blokować pobranie albo wymagać dedykowanego providera/API.",
                detail,
                query,
                site,
                source_url,
                provider=site or None,
            )
            result["input"]["duration_ms"] = int(round((time.perf_counter() - started) * 1000))
            return result

    async def execute_resource(self, uri: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        route_info: Dict[str, Any] = {}
        try:
            route_info = self.registry.resolve_uri(uri, payload or {})
            result = self.registry.execute(uri, payload or {})
            if inspect.isawaitable(result):
                result = await result
            self.record_execution(
                uri=route_info.get("canonical_uri", uri),
                kind="registry_execute",
                ok=bool(result.get("ok", True)) if isinstance(result, dict) else True,
                status=str(result.get("type", "completed")) if isinstance(result, dict) else "completed",
                result=result,
                metadata={
                    "requested_uri": uri,
                    "canonical_uri": route_info.get("canonical_uri", uri),
                    "input": route_info.get("input", payload or {}),
                    "route": route_info.get("route", []),
                    "warnings": route_info.get("warnings", []),
                },
            )
            return result
        except Exception as exc:
            self.record_execution(
                uri=route_info.get("canonical_uri", uri),
                kind="registry_execute",
                ok=False,
                status="error",
                error=str(exc),
                result={"error": str(exc)},
                metadata={
                    "requested_uri": uri,
                    "canonical_uri": route_info.get("canonical_uri", uri),
                    "input": route_info.get("input", payload or {}),
                    "route": route_info.get("route", []),
                    "warnings": route_info.get("warnings", []),
                },
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
    def _message_text(message: Any) -> str:
        for key in ["content", "reasoning_content"]:
            value = getattr(message, key, None)
            if isinstance(value, str) and value.strip():
                return value
        data: Dict[str, Any] = {}
        if hasattr(message, "model_dump"):
            try:
                data = message.model_dump()
            except Exception:
                data = {}
        elif isinstance(message, dict):
            data = message
        for key in ["content", "reasoning_content", "reasoning"]:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value
        provider_fields = data.get("provider_specific_fields")
        if isinstance(provider_fields, dict):
            for key in ["content", "reasoning_content", "reasoning"]:
                value = provider_fields.get(key)
                if isinstance(value, str) and value.strip():
                    return value
        return ""

    @staticmethod
    def _parse_json_response(content: Any) -> Dict[str, Any]:
        text = str(content or "").strip()
        if not text:
            raise ValueError("LLM response did not contain JSON content")
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        decoder = json.JSONDecoder()
        try:
            value = decoder.decode(text)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass

        candidates = []
        for match in re.finditer(r"\{", text):
            try:
                value, _ = decoder.raw_decode(text[match.start() :])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                candidates.append(value)
        if candidates:
            structured = [
                item
                for item in candidates
                if any(key in item for key in ["type", "function_name", "function", "parameters"])
            ]
            if structured:
                return structured[-1]
            return max(candidates, key=lambda item: len(json.dumps(item, ensure_ascii=False)))
        raise ValueError("LLM response did not contain a valid JSON object")

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

    @staticmethod
    def _looks_like_weather_query(query: str) -> bool:
        lowered = query.lower()
        return any(
            keyword in lowered
            for keyword in [
                "pogoda",
                "pogodę",
                "pogode",
                "temperatura",
                "temperaturę",
                "temperature",
                "weather",
                "forecast",
            ]
        )

    @staticmethod
    def _normalize_weather_location(value: Any) -> str:
        location = str(value or "").strip()
        location = re.sub(r"^[\"'`]+|[\"'`.,?!:;]+$", "", location).strip()
        if not location:
            return ""
        normalized = {
            "wejherowie": "Wejherowo",
            "warszawie": "Warszawa",
            "gdansku": "Gdańsk",
            "gdańsku": "Gdańsk",
            "krakowie": "Kraków",
            "poznaniu": "Poznań",
            "wroclawiu": "Wrocław",
            "wrocławiu": "Wrocław",
        }.get(location.lower())
        if normalized:
            return normalized
        if location.lower().endswith("owie") and len(location) > 5:
            return location[:-4] + "owo"
        return location[:1].upper() + location[1:]

    def _weather_location_from_query(
        self,
        query: str,
        parameters: Dict[str, Any],
    ) -> str:
        for key in ["city", "location", "place", "miejscowosc", "miasto"]:
            if parameters.get(key):
                return self._normalize_weather_location(parameters[key])
        patterns = [
            r"\b(?:pogoda|pogodę|pogode|temperatura|weather|forecast)\b[^?.!,\n]{0,80}\b(?:w|we|dla)\s+([^?.!,\n]+)",
            r"\b(?:w|we|dla)\s+([A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż -]{1,60})",
        ]
        for pattern in patterns:
            match = re.search(pattern, query, flags=re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                candidate = re.split(r"\s+(?:teraz|dzisiaj|dziś|jutro|aktualnie)\b", candidate, maxsplit=1, flags=re.IGNORECASE)[0]
                return self._normalize_weather_location(candidate)
        return ""

    def _route_weather_task(self, query: str, task: Task) -> Task:
        if not self._looks_like_weather_query(query):
            return task
        parameters = dict(task.parameters or {})
        city = self._weather_location_from_query(query, parameters)
        routed_parameters = {
            "location": city,
            "country": str(parameters.get("country") or "PL").strip().upper(),
        }
        for key in ["latitude", "longitude"]:
            if key in parameters:
                routed_parameters[key] = parameters[key]
        task.type = TaskType.NOW
        task.function_name = "tellm://service/weather/current"
        task.parameters = routed_parameters
        task.processes = []
        task.code = ""
        if not isinstance(task.view, dict):
            task.view = {}
        task.view.setdefault("title", "Pogoda")
        task.view.setdefault(
            "blocks",
            [{"type": "text", "text": "Pobieram realny wynik z weather.current."}],
        )
        return task

    def _local_weather_task_from_query(self, query: str) -> Optional[Task]:
        if not self._looks_like_weather_query(query):
            return None
        city = self._weather_location_from_query(query, {})
        if not city:
            return None
        return Task(
            TaskType.NOW,
            "tellm://service/weather/current",
            {"location": city, "country": "PL"},
            view={
                "title": "Pogoda w " + city,
                "blocks": [
                    {
                        "type": "text",
                        "text": "Pobieram realny wynik z weather.current.",
                    }
                ],
                "_router": "local_weather",
            },
        )

    @staticmethod
    def _looks_like_price_query(query: str) -> bool:
        lowered = query.lower()
        return any(
            keyword in lowered
            for keyword in [
                "cena",
                "cenę",
                "cene",
                "kosztuje",
                "price",
                "prices",
            ]
        )

    def _price_site_from_query(self, query: str, parameters: Dict[str, Any]) -> str:
        for key in ["site", "source", "domain"]:
            if parameters.get(key):
                return self._normalize_price_site(str(parameters[key]))
        match = re.search(
            r"(?:https?://)?(?:www\.)?([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)",
            query,
            flags=re.IGNORECASE,
        )
        return self._normalize_price_site(match.group(1)) if match else ""

    @staticmethod
    def _normalize_price_product(value: Any) -> str:
        product = str(value or "").strip()
        product = re.sub(r"^[\"'`]+|[\"'`.,?!:;]+$", "", product).strip()
        product = re.sub(r"\b(?:aktualna|aktualną|aktualne|dzisiaj|dziś|teraz)\b", "", product, flags=re.IGNORECASE)
        product = re.sub(r"\s+", " ", product).strip()
        inflections = {
            "cukru": "cukier",
            "mleka": "mleko",
            "chleba": "chleb",
            "masła": "masło",
            "masla": "masło",
            "jajek": "jajka",
        }
        return inflections.get(product.lower(), product)

    def _price_query_from_query(self, query: str, parameters: Dict[str, Any]) -> str:
        for key in ["query", "product", "item", "name"]:
            if parameters.get(key):
                return self._normalize_price_product(parameters[key])
        site_pattern = r"(?:https?://)?(?:www\.)?[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
        patterns = [
            r"\b(?:jaka\s+jest\s+)?(?:cena|cenę|cene|price)\s+(.+?)\s+(?:na|w|we|z|ze)\s+" + site_pattern,
            r"\b(?:ile\s+kosztuje|kosztuje)\s+(.+?)\s+(?:na|w|we|z|ze)\s+" + site_pattern,
        ]
        for pattern in patterns:
            match = re.search(pattern, query, flags=re.IGNORECASE)
            if match:
                return self._normalize_price_product(match.group(1))
        return ""

    def _route_price_task(self, query: str, task: Task) -> Task:
        if not self._looks_like_price_query(query):
            return task
        parameters = dict(task.parameters or {})
        product = self._price_query_from_query(query, parameters)
        site = self._price_site_from_query(query, parameters)
        routed_parameters = {
            "query": product,
            "site": site,
            "original_query": query,
        }
        if parameters.get("url"):
            routed_parameters["url"] = parameters["url"]
        task.type = TaskType.NOW
        task.function_name = "tellm://service/price/search"
        task.parameters = routed_parameters
        task.processes = []
        task.code = ""
        if not isinstance(task.view, dict):
            task.view = {}
        task.view.setdefault("title", "Cena: " + (product or "produkt"))
        task.view.setdefault(
            "blocks",
            [{"type": "text", "text": "Pobieram realny wynik z price.search."}],
        )
        return task

    def _local_price_task_from_query(self, query: str) -> Optional[Task]:
        if not self._looks_like_price_query(query):
            return None
        product = self._price_query_from_query(query, {})
        site = self._price_site_from_query(query, {})
        if not product or not site:
            return None
        return Task(
            TaskType.NOW,
            "tellm://service/price/search",
            {"query": product, "site": site, "original_query": query},
            view={
                "title": "Cena: " + product,
                "blocks": [
                    {
                        "type": "text",
                        "text": "Pobieram realny wynik z price.search.",
                    }
                ],
                "_router": "local_price",
            },
        )

    def _local_task_from_query(self, query: str) -> Optional[Task]:
        for resolver in [self._local_weather_task_from_query, self._local_price_task_from_query]:
            task = resolver(query)
            if task is not None:
                return task
        return None

    async def analyze_query(self, query: str) -> Task:
        local_task = self._local_task_from_query(query)
        if local_task is not None:
            return local_task

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
Jeżeli pytanie dotyczy aktualnej ceny produktu, użyj tellm://service/price/search z parametrami query/site. Nie używaj domain.check do pytań o ceny.
Nie generuj ad hoc funkcji pogodowych typu get_weather_* i nie używaj local_simulation/mock dla aktualnych danych.
LLM nie jest źródłem prawdy dla zadań wykonawczych: wybiera usługę albo generuje bezpieczny proces,
a końcowy wynik musi pochodzić z lokalnej funkcji/procesu jako JSON.
Registry dostępne dla LLM:
""" + registry_json + """
Zapytanie: """ + query
        response = self._completion([{"role": "user", "content": prompt}])
        result = self._parse_json_response(self._message_text(response.choices[0].message))
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
        task = Task(
            task_type,
            function_name,
            parameters,
            code,
            str(result.get("schedule", "") or ""),
            view,
            processes,
        )
        return self._route_price_task(query, self._route_weather_task(query, task))

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
        if not isinstance(message, dict):
            return {}
        if result.get("type") == "system.autoimprovement.report" and isinstance(data, dict):
            return TellmBot._render_autoimprovement_data(data, message)
        blocks = []
        summary = message.get("summary")
        details = message.get("details")
        if summary:
            blocks.append({"type": "text", "text": summary})
        if isinstance(data, dict):
            blocks.append({"type": "key_value", "items": data})
        if result.get("uri"):
            blocks.append({"type": "text", "text": "Usługa: " + str(result["uri"])})
        if details:
            blocks.append({"type": "text", "text": details})
        if result.get("errors"):
            blocks.append({"type": "json", "data": {"errors": result["errors"]}})
        if result.get("warnings"):
            blocks.append({"type": "json", "data": {"warnings": result["warnings"]}})
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
