import asyncio
import sqlite3
from importlib.metadata import PackageNotFoundError, version

import pytest


def test_import():
    import tellm

    try:
        package_version = version("tellm")
    except PackageNotFoundError:
        package_version = tellm.__version__

    assert tellm.__version__ == package_version


def test_sqlite_save_and_get_tasks(tmp_path):
    from tellm import Task, TaskType, create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    task = Task(TaskType.NOW, "echo", {"text": "czesc"})

    bot.save_task(task, {"ok": True}, "powiedz czesc")

    rows = bot.get_tasks()
    assert rows == [
        {
            "id": 1,
            "transcription": "powiedz czesc",
            "type": "now",
            "function": "echo",
            "parameters": {"text": "czesc"},
            "result": {"ok": True},
        }
    ]

    with sqlite3.connect(tmp_path / "tellm.db") as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"tasks", "evolution", "views"} <= tables


def test_view_html_escapes_user_content():
    from tellm import Task, TaskType, ViewData

    task = Task(
        TaskType.NOW,
        "<script>fn()</script>",
        {"payload": "<img src=x onerror=alert(1)>"},
        code="<script>alert(1)</script>",
    )
    view = ViewData(
        transcription="<b>atak</b>",
        task=task,
        result={"html": "<script>x</script>"},
        generated_code=task.code,
        view_elements=[{"type": "answer", "text": "<script>answer</script>"}],
    )

    html = view.to_html()

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;atak&lt;/b&gt;" in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html


def test_execute_task_supports_sync_functions(tmp_path):
    from tellm import Task, TaskType, create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    bot.register_function("echo", lambda params: {"echo": params["text"]})

    result = asyncio.run(bot.execute_task(Task(TaskType.NOW, "echo", {"text": "ok"})))

    assert result == {"echo": "ok"}


def test_server_starts_inside_running_event_loop(tmp_path):
    from tellm.server import TellmServer

    async def start_and_cancel():
        server = TellmServer(
            host="127.0.0.1",
            port=0,
            db_path=str(tmp_path / "tellm.db"),
        )
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(server.serve_forever(), timeout=0.05)

    asyncio.run(start_and_cancel())


def test_server_handles_plain_http_request(tmp_path):
    from tellm.server import TellmServer

    async def request_plain_http():
        server = TellmServer(
            host="127.0.0.1",
            port=0,
            db_path=str(tmp_path / "tellm.db"),
        )
        async with __import__("websockets").serve(
            server.handle,
            server.host,
            server.port,
            process_request=server.process_request,
        ) as ws_server:
            port = ws_server.sockets[0].getsockname()[1]
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(
                b"GET / HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"Connection: keep-alive\r\n"
                b"\r\n"
            )
            await writer.drain()
            response = await reader.read(4096)
            writer.close()
            await writer.wait_closed()
            return response

    response = asyncio.run(request_plain_http())

    assert response.startswith(b"HTTP/1.1 200 OK")
    assert b"tellm v4" in response
    assert b"WebSocket endpoint" in response
