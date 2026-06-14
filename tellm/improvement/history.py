import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class ExecutionHistoryStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_history (
                id INTEGER PRIMARY KEY,
                created_at TEXT,
                uri TEXT,
                kind TEXT,
                ok INTEGER,
                status TEXT,
                error TEXT,
                result_json TEXT,
                logs_json TEXT,
                metadata_json TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def record(
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
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO execution_history
                (created_at, uri, kind, ok, status, error, result_json, logs_json, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.now(),
                uri,
                kind,
                1 if ok else 0,
                status,
                error,
                json.dumps(result, ensure_ascii=False, default=str),
                json.dumps(logs or [], ensure_ascii=False, default=str),
                json.dumps(metadata or {}, ensure_ascii=False, default=str),
            ),
        )
        row_id = c.lastrowid
        conn.commit()
        conn.close()
        return int(row_id)

    @staticmethod
    def _decode_row(row) -> Dict[str, Any]:
        return {
            "id": row[0],
            "created_at": row[1],
            "uri": row[2],
            "kind": row[3],
            "ok": bool(row[4]),
            "status": row[5],
            "error": row[6],
            "result": json.loads(row[7] or "null"),
            "logs": json.loads(row[8] or "[]"),
            "metadata": json.loads(row[9] or "{}"),
        }

    def recent(self, limit: int = 100, uri: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if uri:
            c.execute(
                """
                SELECT id, created_at, uri, kind, ok, status, error, result_json, logs_json, metadata_json
                FROM execution_history
                WHERE uri = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (uri, limit),
            )
        else:
            c.execute(
                """
                SELECT id, created_at, uri, kind, ok, status, error, result_json, logs_json, metadata_json
                FROM execution_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
        rows = c.fetchall()
        conn.close()
        return [self._decode_row(row) for row in rows]

    def count_since_id(self, since_id: int) -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM execution_history WHERE id > ?", (since_id,))
        count = int(c.fetchone()[0])
        conn.close()
        return count

    def latest_id(self) -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COALESCE(MAX(id), 0) FROM execution_history")
        latest = int(c.fetchone()[0])
        conn.close()
        return latest
