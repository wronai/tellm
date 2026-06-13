import asyncio
import sqlite3


def test_import():
    import tellm

    assert tellm.__version__ == "4.0.0"


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
