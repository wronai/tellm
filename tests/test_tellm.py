import asyncio
import base64
import json
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


def test_view_html_renders_dynamic_json_structure():
    from tellm import Task, TaskType, ViewData

    task = Task(
        TaskType.NOW,
        "summarize",
        {"topic": "test"},
        view={
            "title": "Panel",
            "blocks": [
                {"type": "heading", "text": "Podsumowanie", "level": 2},
                {"type": "metric", "label": "Score", "value": 7},
                {"type": "list", "items": ["a", "<script>x</script>"]},
                {
                    "type": "table",
                    "columns": ["name", "value"],
                    "rows": [{"name": "x", "value": "<b>safe</b>"}],
                },
            ],
        },
    )
    view = ViewData(
        transcription="render",
        task=task,
        result={"ok": True},
        render_data=task.view,
    )

    html = view.to_html()

    assert "dynamic-view" in html
    assert "Panel" in html
    assert "Podsumowanie" in html
    assert "Score" in html
    assert "&lt;script&gt;x&lt;/script&gt;" in html
    assert "&lt;b&gt;safe&lt;/b&gt;" in html


def test_execute_task_supports_sync_functions(tmp_path):
    from tellm import Task, TaskType, create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    bot.register_function("echo", lambda params: {"echo": params["text"]})

    result = asyncio.run(bot.execute_task(Task(TaskType.NOW, "echo", {"text": "ok"})))

    assert result == {"echo": "ok"}


def test_registry_executes_typed_local_resource(tmp_path):
    from tellm import create_bot
    from tellm.registry import RegistryValidationError

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    result = asyncio.run(bot.execute_resource("tellm://function/system/echo", {"text": "ok"}))

    assert result["ok"] is True
    assert result["uri"] == "tellm://function/system/echo"
    assert result["data"] == {"input": {"text": "ok"}}
    assert "message" in result

    with pytest.raises(RegistryValidationError):
        asyncio.run(bot.execute_resource("tellm://service/domain/check", {}))


def test_registry_manifest_uses_tellm_standards(tmp_path):
    from tellm import create_bot
    from tellm.registry import (
        JSON_SCHEMA_DRAFT_2020_12,
        TRM_VERSION,
        TSR_VERSION,
        RegistryValidationError,
        service_result,
        service_result_schema,
        validate_schema,
        validate_tellm_uri,
    )

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    manifest = bot.registry.manifest()
    weather = bot.registry.get("tellm://service/weather/current").to_dict()
    envelope = service_result(
        ok=True,
        uri="tellm://service/test/example",
        result_type="test.result",
        data={"source": "unit_test", "fetched_at": "2026-06-14T00:00:00Z"},
        title="OK",
        summary="done",
    )

    validate_tellm_uri("tellm://service/weather/current", "service")
    with pytest.raises(RegistryValidationError):
        validate_tellm_uri("http://localhost:8008/weather", "service")

    assert manifest["manifest_version"] == TRM_VERSION
    assert manifest["schema_version"] == "2020-12"
    assert manifest["schemas"]["service_result"]["$schema"] == JSON_SCHEMA_DRAFT_2020_12
    assert any(
        resource["uri"] == "tellm://schema/tellm/resource-manifest"
        for resource in manifest["resources"]
    )
    assert weather["manifest_version"] == TRM_VERSION
    assert weather["schema_version"] == "2020-12"
    assert weather["input_schema"]["$schema"] == JSON_SCHEMA_DRAFT_2020_12
    assert "location" in weather["input_schema"]["properties"]
    assert weather["permissions"]["network"] is True
    assert weather["data_policy"]["requires_real_world_data"] is True
    assert weather["render"]["default_view"] == "tellm://view/weather/current"

    assert envelope["envelope_version"] == TSR_VERSION
    assert envelope["warnings"] == []
    assert envelope["meta"]["source"] == "unit_test"
    assert envelope["render"]["renderer"] == "auto"
    validate_schema(service_result_schema(), envelope)

    error_envelope = service_result(
        ok=False,
        uri="tellm://service/weather/current",
        result_type="weather.current.result",
        data=None,
        title="Błąd",
        summary="Brak danych",
        errors=["Function cannot access network or files"],
    )
    assert error_envelope["errors"] == [
        {
            "code": "NETWORK_ACCESS_NOT_ALLOWED",
            "source": "tellm://service/weather/current",
            "detail": "Function cannot access network or files",
            "recoverable": True,
        }
    ]
    validate_schema(service_result_schema(), error_envelope)


def test_registry_masks_env_and_exposes_discovery(tmp_path, monkeypatch):
    from tellm import create_bot

    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-value")
    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    env_value = bot.registry.read("tellm://env/OPENROUTER_API_KEY")
    entries = bot.registry.discover_for_llm()

    assert env_value == {"exists": True, "masked": True}
    assert any(entry["uri"] == "tellm://service/domain/check" for entry in entries)
    assert "secret-value" not in json.dumps(entries)


def test_weather_service_fetches_open_meteo_data(tmp_path, monkeypatch):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    def fake_http_json(url, timeout=8):
        if "geocoding-api.open-meteo.com" in url:
            return {
                "results": [
                    {
                        "name": "Wejherowo",
                        "country_code": "PL",
                        "latitude": 54.6057,
                        "longitude": 18.2356,
                    }
                ]
            }
        if "api.open-meteo.com" in url:
            return {
                "current": {
                    "time": "2026-06-14T12:00",
                    "temperature_2m": 15.0,
                    "relative_humidity_2m": 80,
                    "apparent_temperature": 14.2,
                    "weather_code": 61,
                    "wind_speed_10m": 12.5,
                    "wind_direction_10m": 240,
                }
            }
        raise AssertionError(url)

    monkeypatch.setattr(bot, "_http_json", fake_http_json)

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/weather/current",
            {"city": "Wejherowo", "country": "PL"},
        )
    )

    assert result["ok"] is True
    assert result["type"] == "weather.current.result"
    assert result["uri"] == "tellm://service/weather/current"
    assert result["data"]["city"] == "Wejherowo"
    assert result["data"]["temperature_c"] == 15.0
    assert result["data"]["source"] == "open_meteo"
    assert "deszcz" in result["data"]["description"]


def test_weather_service_returns_standard_error_when_network_denied(tmp_path, monkeypatch):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    def fake_http_json(url, timeout=8):
        raise PermissionError("Network access is required but not allowed.")

    monkeypatch.setattr(bot, "_http_json", fake_http_json)

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/weather/current",
            {"city": "Wejherowo", "country": "PL"},
        )
    )

    assert result["ok"] is False
    assert result["uri"] == "tellm://service/weather/current"
    assert result["type"] == "weather.current.result"
    assert result["data"] is None
    assert result["input"] == {"location": "Wejherowo", "country": "PL"}
    assert result["errors"][0]["code"] == "NETWORK_ACCESS_NOT_ALLOWED"
    assert result["errors"][0]["source"] == "tellm://service/weather/current"
    assert result["errors"][0]["recoverable"] is True


def test_autoimprove_service_returns_and_saves_schema_valid_report(tmp_path):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/system/autoimprove",
            {"mode": "manual", "dry_run": True, "allow_auto_apply": False},
        )
    )
    latest = bot.get_latest_autoimprovement_report()

    assert result["type"] == "system.autoimprovement.report"
    assert result["data"]["dry_run"] is True
    assert result["data"]["allow_auto_apply"] is False
    assert isinstance(result["data"]["findings"], list)
    assert isinstance(result["data"]["suggested_actions"], list)
    assert isinstance(result["data"]["patches"], list)
    assert result["data"]["tests"]["pytest"] == "not_run"
    assert latest["data"]["report_id"] == result["data"]["report_id"]
    assert bot.registry.read("tellm://data/system/autoimprovement-report/latest")["type"] == "system.autoimprovement.report"


def test_autoimprove_finds_missing_schema(tmp_path):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    bot.register_function("unsafe_echo", lambda params: {"echo": params})

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/system/autoimprove",
            {"mode": "manual", "dry_run": True},
        )
    )

    finding_types = {item["type"] for item in result["data"]["findings"]}
    assert "missing_output_schema" in finding_types
    assert any(
        patch["status"] == "pending_review" and patch["risk"] == "low"
        for patch in result["data"]["patches"]
    )


def test_autoimprove_finds_repeated_service_failures(tmp_path):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    for index in range(3):
        bot.record_execution(
            uri="tellm://service/domain/check",
            kind="registry_execute",
            ok=False,
            status="error",
            error="NETWORK_UNAVAILABLE %d" % index,
        )

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/system/autoimprove",
            {"repeated_failure_threshold": 3, "dry_run": True},
        )
    )

    findings = result["data"]["findings"]
    assert any(item["type"] == "repeated_service_failure" for item in findings)
    assert result["data"]["summary"]["failed_services"] >= 3


def test_autoimprove_finds_direct_llm_answer_violation(tmp_path):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    bot.record_execution(
        uri="domain.check",
        kind="workflow",
        ok=True,
        status="completed",
        result={"answer": "Nie mogę sprawdzić domeny"},
        metadata={
            "query": "sprawdź czy example.pl jest wolna",
            "llm_direct_answer_violation": True,
        },
    )

    result = asyncio.run(
        bot.execute_resource("tellm://service/system/autoimprove", {"dry_run": True})
    )

    assert any(
        item["type"] == "llm_direct_answer_violation"
        for item in result["data"]["findings"]
    )
    assert result["data"]["summary"]["direct_answer_violations"] == 1


def test_autoimprove_finds_simulated_data_for_real_world_query(tmp_path):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    bot.record_execution(
        uri="get_weather_wejherowo",
        kind="workflow",
        ok=True,
        status="completed_with_warnings",
        result={
            "status": "completed",
            "processes": [
                {
                    "name": "get_weather_wejherowo",
                    "ok": True,
                    "result": {"city": "Wejherowo", "source": "local_simulation"},
                }
            ],
        },
        metadata={
            "query": "Jaka jest pogoda w Wejherowie",
            "data_quality_findings": [
                {
                    "type": "simulated_data_used_for_real_world_query",
                    "source": "local_simulation",
                    "problem": "source=local_simulation",
                    "recommendation": "Use weather.current.",
                }
            ],
        },
    )

    result = asyncio.run(
        bot.execute_resource("tellm://service/system/autoimprove", {"dry_run": True})
    )

    assert any(
        item["type"] == "simulated_data_used_for_real_world_query"
        for item in result["data"]["findings"]
    )
    assert result["data"]["summary"]["simulated_data_warnings"] >= 1


def test_autoimprove_finds_missing_weather_provider_and_ad_hoc_function(tmp_path):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    bot.record_execution(
        uri="weather_wejherowo",
        kind="workflow",
        ok=True,
        status="completed_with_service_error",
        result={
            "ok": False,
            "uri": "tellm://service/weather/current",
            "type": "weather.current.result",
            "data": None,
            "message": {
                "title": "Nie udało się pobrać pogody",
                "summary": "Brak sieci",
            },
            "errors": [
                {
                    "code": "NETWORK_ACCESS_NOT_ALLOWED",
                    "source": "tellm://service/weather/current",
                    "detail": "Network access is required but not allowed.",
                    "recoverable": True,
                }
            ],
        },
        metadata={
            "query": "Jaka jest pogoda w Wejherowie",
            "execution_status": "completed",
            "service_result_status": "failed",
        },
    )

    result = asyncio.run(
        bot.execute_resource("tellm://service/system/autoimprove", {"dry_run": True})
    )
    finding_types = {item["type"] for item in result["data"]["findings"]}

    assert "missing_real_data_provider" in finding_types
    assert "ad_hoc_function_generated" in finding_types
    assert result["data"]["summary"]["missing_real_data_provider"] == 1
    assert result["data"]["summary"]["ad_hoc_function_generated"] == 1


def test_autoimprovement_report_renders_as_html(tmp_path):
    from tellm import Task, TaskType, create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    result = asyncio.run(
        bot.execute_resource("tellm://service/system/autoimprove", {"dry_run": True})
    )
    view = bot.generate_view(
        "autoimprove",
        Task(TaskType.NOW, "tellm://service/system/autoimprove", {}),
        result,
    )
    html = view.to_html()

    assert "Autoimprovement report" in html
    assert "Pending patches" in html
    assert "not_run" in html


def test_analyze_query_reads_llm_json_view_and_processes(tmp_path, monkeypatch):
    from tellm import TaskType, create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    def fake_completion(messages):
        class Message:
            content = json.dumps(
                {
                    "type": "now",
                    "function_name": "run",
                    "parameters": {"x": 2},
                    "view": {
                        "title": "Dynamic",
                        "blocks": [{"type": "text", "text": "OK"}],
                    },
                    "processes": [
                        {
                            "name": "calc",
                            "language": "python",
                            "entrypoint": "run",
                            "code": "def run(params):\n    return {'x': params['x']}",
                        }
                    ],
                }
            )

        class Choice:
            message = Message()

        class Response:
            choices = [Choice()]

        assert "view" in messages[0]["content"]
        assert "processes" in messages[0]["content"]
        assert "tellm://service/domain/check" in messages[0]["content"]
        assert "tellm://service/weather/current" in messages[0]["content"]
        return Response()

    monkeypatch.setattr(bot, "_completion", fake_completion)

    task = asyncio.run(bot.analyze_query("policz"))

    assert task.type == TaskType.NOW
    assert task.function_name == "run"
    assert task.parameters == {"x": 2}
    assert task.view["title"] == "Dynamic"
    assert task.processes[0]["name"] == "calc"


def test_analyze_query_routes_weather_to_registry_service(tmp_path, monkeypatch):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    def fake_completion(messages):
        class Message:
            content = json.dumps(
                {
                    "type": "now",
                    "function_name": "weather_wejherowo",
                    "parameters": {},
                    "processes": [
                        {
                            "name": "weather_wejherowo",
                            "language": "python",
                            "entrypoint": "run",
                            "code": "def run(params):\n    return {'source': 'local_simulation'}",
                        }
                    ],
                    "code": "def weather_wejherowo(params):\n    return {}",
                }
            )

        class Choice:
            message = Message()

        class Response:
            choices = [Choice()]

        return Response()

    monkeypatch.setattr(bot, "_completion", fake_completion)

    task = asyncio.run(bot.analyze_query("Jaka jest pogoda w Wejherowie?"))

    assert task.function_name == "tellm://service/weather/current"
    assert task.parameters == {"location": "Wejherowo", "country": "PL"}
    assert task.processes == []
    assert task.code == ""


def test_execute_task_runs_python_process(tmp_path):
    from tellm import Task, TaskType, create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    task = Task(
        TaskType.NOW,
        "run",
        {"x": 2, "y": 3},
        processes=[
            {
                "name": "sum_values",
                "language": "python",
                "entrypoint": "run",
                "code": "def run(params):\n    return {'sum': params['x'] + params['y']}",
            }
        ],
    )

    result = asyncio.run(bot.execute_task(task))

    assert result == {
        "status": "completed",
        "processes": [
            {"name": "sum_values", "ok": True, "result": {"sum": 5}},
        ],
    }


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
            response = await reader.read(20000)
            writer.close()
            await writer.wait_closed()
            return response

    response = asyncio.run(request_plain_http())

    assert response.startswith(b"HTTP/1.1 200 OK")
    assert b"tellm v4" in response
    assert b"WebSocket endpoint" in response
    assert b"<textarea" in response
    assert b"SpeechRecognition" in response
    assert b'data-theme="light"' in response
    assert b'name="theme" value="warm"' in response
    assert b'name="theme" value="light"' in response
    assert b'name="theme" value="dark"' in response
    assert b'localStorage.setItem("tellm-theme"' in response
    assert b'id="copyQuery"' in response
    assert b'id="copyResult"' in response
    assert b'id="workflowLog"' in response
    assert b'id="cancel"' in response
    assert b"URLSearchParams" in response
    assert b"view_id" in response
    assert b"restoreUrlState" in response
    assert b"Logi workflow" in response
    assert b"setBusy" in response


def test_server_docs_describe_text_and_speech_api(tmp_path):
    from tellm.server import TellmServer

    async def request_docs():
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
                b"GET /docs HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"Connection: keep-alive\r\n"
                b"\r\n"
            )
            await writer.drain()
            response = await reader.read(50000)
            writer.close()
            await writer.wait_closed()
            return response

    response = asyncio.run(request_docs())

    assert response.startswith(b"HTTP/1.1 200 OK")
    assert b"tellm v4 API docs" in response
    assert b'"type": "text"' in response
    assert b"navigator.mediaDevices.getUserMedia" in response
    assert b"MediaRecorder" in response
    assert b"audio/webm" in response
    assert b"Kontrakt LLM JSON" in response
    assert b'"view": {' in response
    assert b'"processes": [' in response
    assert b'"type": "metric"' in response
    assert b"Udost" in response
    assert b"?q=tekst" in response
    assert b"view_id" in response
    assert b"/views/12" in response
    assert b"Workflow z walidacj" in response
    assert b'"type": "log"' in response
    assert b'"type": "cancel"' in response
    assert b"LLM validation" in response
    assert b"Tellm Resource Registry" in response
    assert b"/registry" in response
    assert b"/registry-ui" in response
    assert b"/autoimprovement" in response
    assert b"/resource?uri=tellm://..." in response
    assert b'"type": "execute"' in response
    assert b"POST /execute" in response
    assert b"tellm://service/system/autoimprove" in response
    assert b"dry_run" in response
    assert b"tellm://service/weather/current" in response
    assert b"data_source" in response
    assert b"/manifest" in response
    assert b"/openapi.json" in response
    assert b"/asyncapi.json" in response
    assert b"/execute" in response
    assert b"/query" in response
    assert b"/autoimprovement/run" in response
    assert b"Tellm Resource Manifest 1.0" in response
    assert b"Tellm Service Result 1.0" in response


def test_server_registry_http_endpoints(tmp_path):
    from tellm.server import TellmServer

    async def request(path):
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
                (
                    "GET "
                    + path
                    + " HTTP/1.1\r\n"
                    + "Host: localhost\r\n"
                    + "Connection: keep-alive\r\n"
                    + "\r\n"
                ).encode("ascii")
            )
            await writer.drain()
            response = await reader.read(50000)
            writer.close()
            await writer.wait_closed()
            return response

    registry_response = asyncio.run(request("/registry"))
    manifest_response = asyncio.run(request("/manifest"))
    openapi_response = asyncio.run(request("/openapi.json"))
    asyncapi_response = asyncio.run(request("/asyncapi.json"))
    execute_response = asyncio.run(request("/execute"))
    resource_response = asyncio.run(
        request("/resource?uri=tellm://function/system/now")
    )
    resolve_response = asyncio.run(
        request("/resolve?uri=tellm://service/domain/check")
    )

    assert registry_response.startswith(b"HTTP/1.1 200 OK")
    assert b"application/json" in registry_response
    assert b"tellm://service/domain/check" in registry_response
    assert b"OPENROUTER_API_KEY" in registry_response
    assert b"secret-value" not in registry_response

    assert manifest_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"manifest_version": "1.0.0"' in manifest_response
    assert b'"$schema": "https://json-schema.org/draft/2020-12/schema"' in manifest_response
    assert b"tellm://schema/tellm/service-result" in manifest_response

    assert openapi_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"openapi": "3.1.0"' in openapi_response
    assert b'TellmServiceResult' in openapi_response
    assert b'"/execute"' in openapi_response
    assert b'"post"' in openapi_response
    assert b"ExecuteRequest" in openapi_response

    assert asyncapi_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"asyncapi": "3.1.0"' in asyncapi_response
    assert b"ClientExecute" in asyncapi_response

    assert execute_response.startswith(b"HTTP/1.1 501 Not Implemented")
    assert b"HTTP_BODY_TRANSPORT_NOT_ENABLED" in execute_response

    assert resource_response.startswith(b"HTTP/1.1 200 OK")
    assert b"tellm://function/system/now" in resource_response

    assert resolve_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"has_callable": true' in resolve_response


def test_server_registry_ui_and_autoimprovement_pages(tmp_path):
    from tellm.server import TellmServer

    async def request(path):
        server = TellmServer(
            host="127.0.0.1",
            port=0,
            db_path=str(tmp_path / "tellm.db"),
        )
        server.bot.save_autoimprovement_report(
            {
                "ok": True,
                "type": "system.autoimprovement.report",
                "data": {"summary": {}, "findings": [], "patches": [], "tests": {}},
                "message": {"title": "Autoimprovement report", "summary": "ok", "details": ""},
                "view": {"renderer": "auto"},
                "errors": [],
            },
            html="<html><body>report</body></html>",
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
                (
                    "GET "
                    + path
                    + " HTTP/1.1\r\n"
                    + "Host: localhost\r\n"
                    + "Connection: keep-alive\r\n"
                    + "\r\n"
                ).encode("ascii")
            )
            await writer.drain()
            response = await reader.read(50000)
            writer.close()
            await writer.wait_closed()
            return response

    registry_ui = asyncio.run(request("/registry-ui"))
    autoimprovement = asyncio.run(request("/autoimprovement"))
    latest = asyncio.run(request("/autoimprovement/latest"))

    assert registry_ui.startswith(b"HTTP/1.1 200 OK")
    assert b"Registry UI" in registry_ui
    assert b"tellm://service/system/autoimprove" in registry_ui

    assert autoimprovement.startswith(b"HTTP/1.1 200 OK")
    assert b"Run dry-run audit" in autoimprovement
    assert b"tellm://service/system/autoimprove" in autoimprovement

    assert latest.startswith(b"HTTP/1.1 200 OK")
    assert b"system.autoimprovement.report" in latest
    assert b"<html><body>report</body></html>" in latest


def test_server_returns_saved_view_by_id(tmp_path):
    from tellm import Task, TaskType, ViewData
    from tellm.server import TellmServer

    async def request_saved_view():
        server = TellmServer(
            host="127.0.0.1",
            port=0,
            db_path=str(tmp_path / "tellm.db"),
        )
        view = ViewData(
            transcription="zapytanie",
            task=Task(TaskType.NOW, "echo", {"text": "zapytanie"}),
            result={"ok": True},
        )
        server.bot.save_view(view)

        async with __import__("websockets").serve(
            server.handle,
            server.host,
            server.port,
            process_request=server.process_request,
        ) as ws_server:
            port = ws_server.sockets[0].getsockname()[1]
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(
                f"GET /views/{view.view_id} HTTP/1.1\r\n"
                "Host: localhost\r\n"
                "Connection: keep-alive\r\n"
                "\r\n"
                .encode("ascii")
            )
            await writer.drain()
            response = await reader.read(20000)
            writer.close()
            await writer.wait_closed()
            return response

    response = asyncio.run(request_saved_view())

    assert response.startswith(b"HTTP/1.1 200 OK")
    assert b"tellm View" in response
    assert b"zapytanie" in response


def test_server_audio_payload_reads_data_url_suffix(tmp_path):
    from tellm.server import TellmServer

    server = TellmServer(host="127.0.0.1", port=0, db_path=str(tmp_path / "tellm.db"))
    audio = base64.b64encode(b"fake-webm").decode("ascii")

    payload, suffix = server._audio_payload("data:audio/webm;base64," + audio)

    assert payload == b"fake-webm"
    assert suffix == ".webm"


def test_server_validation_can_repair_render_data(tmp_path, monkeypatch):
    from tellm import Task, TaskType
    from tellm.server import TellmServer

    class DummyWebSocket:
        def __init__(self):
            self.events = []

        async def send(self, raw):
            self.events.append(json.loads(raw))

    def response_with(content):
        class Message:
            pass

        class Choice:
            pass

        class Response:
            pass

        Message.content = content
        Choice.message = Message()
        Response.choices = [Choice()]
        return Response()

    responses = [
        response_with(
            json.dumps(
                {
                    "status": "repair",
                    "reason": "missing final text",
                    "view": {
                        "title": "Poprawione",
                        "blocks": [{"type": "text", "text": "Naprawione"}],
                    },
                    "result": {"ok": True, "fixed": True},
                }
            )
        ),
        response_with(json.dumps({"status": "ok", "answer": "OK po naprawie"})),
    ]

    def fake_completion(*args, **kwargs):
        return responses.pop(0)

    server = TellmServer(
        host="127.0.0.1",
        port=0,
        db_path=str(tmp_path / "tellm.db"),
    )
    monkeypatch.setattr("tellm.server.completion", fake_completion)
    task = Task(
        TaskType.NOW,
        "run",
        {},
        view={"title": "Stare", "blocks": [{"type": "text", "text": "Stare"}]},
    )
    result = {"ok": False}
    view = server.bot.generate_view("query", task, result)
    logs = server._render_logs("query", task, result, view, view.to_html())
    websocket = DummyWebSocket()

    repaired_view, answer, render_logs = asyncio.run(
        server._validate_and_repair(
            websocket,
            "query",
            task,
            result,
            view,
            logs,
            client_logs=[],
        )
    )

    assert answer == "OK po naprawie"
    assert repaired_view.render_data["title"] == "Poprawione"
    assert any(event["status"] == "repair" for event in websocket.events)
    assert render_logs[-1]["stage"] == "renderer"


def test_server_flags_simulated_weather_source(tmp_path):
    from tellm import Task, TaskType
    from tellm.server import TellmServer

    server = TellmServer(
        host="127.0.0.1",
        port=0,
        db_path=str(tmp_path / "tellm.db"),
    )
    task = Task(
        TaskType.NOW,
        "get_weather_wejherowo",
        {"city": "Wejherowo"},
        processes=[
            {
                "name": "get_weather_wejherowo",
                "language": "python",
                "entrypoint": "run",
            }
        ],
    )
    result = {
        "status": "completed",
        "processes": [
            {
                "name": "get_weather_wejherowo",
                "ok": True,
                "result": {
                    "city": "Wejherowo",
                    "temperature_c": 15,
                    "source": "local_simulation",
                },
            }
        ],
    }
    view = server.bot.generate_view("Jaka jest pogoda w Wejherowie", task, result)
    findings = server._data_source_findings(
        "Jaka jest pogoda w Wejherowie",
        task,
        result,
    )
    server._append_data_quality_warnings(view, findings)
    html = view.to_html()
    logs = server._render_logs(
        "Jaka jest pogoda w Wejherowie",
        task,
        result,
        view,
        html,
    )

    assert findings[0]["type"] == "simulated_data_used_for_real_world_query"
    assert any(
        log["stage"] == "data_source" and log["status"] == "warning"
        for log in logs
    )
    assert "Ostrzeżenie" in html
    assert "local_simulation" in html


def test_server_logs_execution_and_service_result_separately(tmp_path):
    from tellm import Task, TaskType
    from tellm.server import TellmServer

    server = TellmServer(
        host="127.0.0.1",
        port=0,
        db_path=str(tmp_path / "tellm.db"),
    )
    task = Task(
        TaskType.NOW,
        "tellm://service/weather/current",
        {"city": "Wejherowo", "country": "PL"},
    )
    result = {
        "ok": False,
        "uri": "tellm://service/weather/current",
        "type": "weather.current.result",
        "data": None,
        "message": {
            "title": "Nie udało się pobrać pogody",
            "summary": "Brak sieci",
        },
        "errors": [
            {
                "code": "NETWORK_ACCESS_NOT_ALLOWED",
                "source": "tellm://service/weather/current",
                "detail": "Network access is required but not allowed.",
                "recoverable": True,
            }
        ],
    }
    view = server.bot.generate_view("Jaka jest pogoda w Wejherowie", task, result)
    html = view.to_html()
    logs = server._render_logs(
        "Jaka jest pogoda w Wejherowie",
        task,
        result,
        view,
        html,
    )

    assert any(
        log["stage"] == "functions" and log["status"] == "completed"
        for log in logs
    )
    assert any(
        log["stage"] == "service_result" and log["status"] == "failed"
        for log in logs
    )
    assert server._workflow_history_status(result, []) == "completed_with_service_error"
    assert "NETWORK_ACCESS_NOT_ALLOWED" in html


def test_server_blocks_parallel_query_and_accepts_cancel(tmp_path, monkeypatch):
    import websockets
    from tellm import Task, TaskType
    from tellm.server import TellmServer

    async def run_flow():
        server = TellmServer(
            host="127.0.0.1",
            port=0,
            db_path=str(tmp_path / "tellm.db"),
        )

        async def slow_analyze(query):
            await asyncio.sleep(2)
            return Task(TaskType.NOW, "echo", {"text": query})

        monkeypatch.setattr(server.bot, "analyze_query", slow_analyze)

        async with websockets.serve(
            server.handle,
            server.host,
            server.port,
            process_request=server.process_request,
        ) as ws_server:
            port = ws_server.sockets[0].getsockname()[1]
            async with websockets.connect(f"ws://127.0.0.1:{port}") as websocket:
                await websocket.send(json.dumps({"type": "text", "text": "pierwsze"}))
                first = json.loads(await websocket.recv())
                await websocket.send(json.dumps({"type": "text", "text": "drugie"}))
                blocked = None
                queued = []
                for _ in range(8):
                    event = json.loads(await asyncio.wait_for(websocket.recv(), timeout=2))
                    queued.append(event)
                    if event.get("type") == "error":
                        blocked = event
                        break
                await websocket.send(json.dumps({"type": "cancel"}))
                events = []
                for _ in range(5):
                    event = json.loads(await asyncio.wait_for(websocket.recv(), timeout=2))
                    events.append(event)
                    if event.get("type") == "state" and event.get("state") == "idle":
                        break
                return first, blocked, queued + events

    first, blocked, events = asyncio.run(run_flow())

    assert first["type"] == "state"
    assert first["state"] == "busy"
    assert blocked is not None
    assert blocked["type"] == "error"
    assert "Trwa poprzednie query" in blocked["message"]
    assert any(event.get("state") == "idle" for event in events)


def test_server_test_mode_returns_echo_without_llm(tmp_path):
    import websockets
    from tellm.server import TellmServer

    async def send_test_text():
        server = TellmServer(
            host="127.0.0.1",
            port=0,
            db_path=str(tmp_path / "tellm.db"),
        )
        async with websockets.serve(
            server.handle,
            server.host,
            server.port,
            process_request=server.process_request,
        ) as ws_server:
            port = ws_server.sockets[0].getsockname()[1]
            async with websockets.connect(f"ws://127.0.0.1:{port}") as websocket:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "text",
                            "text": "test protokolu",
                            "test": True,
                            "speak": False,
                        }
                    )
                )
                events = []
                while True:
                    event = json.loads(await websocket.recv())
                    events.append(event)
                    if event.get("html"):
                        break
        analyzing = next(
            event
            for event in events
            if event.get("data", {}).get("status") == "analyzing"
        )
        final = events[-1]
        return analyzing, final, events

    analyzing, final, events = asyncio.run(send_test_text())

    assert analyzing["data"]["status"] == "analyzing"
    assert any(event.get("type") == "state" for event in events)
    assert final["data"]["result"] == {
        "ok": True,
        "source": "text",
        "echo": "test protokolu",
    }
    assert isinstance(final["data"]["view_id"], int)
    assert "Protocol test OK" in final["html"]


def test_server_executes_registry_uri_over_websocket(tmp_path, monkeypatch):
    import websockets
    from tellm.server import TellmServer

    def fake_completion(*args, **kwargs):
        class Message:
            content = json.dumps({"status": "ok", "answer": "LLM OK"})

        class Choice:
            message = Message()

        class Response:
            choices = [Choice()]

        return Response()

    async def execute_resource():
        server = TellmServer(
            host="127.0.0.1",
            port=0,
            db_path=str(tmp_path / "tellm.db"),
        )
        monkeypatch.setattr("tellm.server.completion", fake_completion)
        async with websockets.serve(
            server.handle,
            server.host,
            server.port,
            process_request=server.process_request,
        ) as ws_server:
            port = ws_server.sockets[0].getsockname()[1]
            async with websockets.connect(f"ws://127.0.0.1:{port}") as websocket:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "execute",
                            "uri": "tellm://function/system/echo",
                            "input": {"text": "registry"},
                            "speak": False,
                        }
                    )
                )
                events = []
                while True:
                    event = json.loads(await websocket.recv())
                    events.append(event)
                    if event.get("html"):
                        break
                return events[-1], events

    final, events = asyncio.run(execute_resource())

    assert any(event.get("stage") == "registry" for event in events)
    assert final["data"]["task"]["function"] == "tellm://function/system/echo"
    assert final["data"]["result"]["uri"] == "tellm://function/system/echo"
    assert "Payload zostal zwrocony" in final["html"]
    assert "LLM OK" not in final["html"]


def test_server_accepts_text_websocket_messages(tmp_path, monkeypatch):
    import websockets
    from tellm import Task, TaskType, ViewData
    from tellm.server import TellmServer

    async def send_text():
        server = TellmServer(
            host="127.0.0.1",
            port=0,
            db_path=str(tmp_path / "tellm.db"),
        )
        speak_calls = []

        async def analyze_query(query):
            return Task(TaskType.NOW, "echo", {"text": query})

        async def execute_task(task):
            return {"echo": task.parameters["text"]}

        def generate_view(transcription, task, result):
            return ViewData(transcription=transcription, task=task, result=result)

        def fake_completion(*args, **kwargs):
            class Message:
                content = "Odpowiedz testowa"

            class Choice:
                message = Message()

            class Response:
                choices = [Choice()]

            return Response()

        monkeypatch.setattr(server.bot, "analyze_query", analyze_query)
        monkeypatch.setattr(server.bot, "execute_task", execute_task)
        monkeypatch.setattr(server.bot, "generate_view", generate_view)
        monkeypatch.setattr(server.bot, "speak", lambda text: speak_calls.append(text))
        monkeypatch.setattr("tellm.server.completion", fake_completion)

        async with websockets.serve(
            server.handle,
            server.host,
            server.port,
            process_request=server.process_request,
        ) as ws_server:
            port = ws_server.sockets[0].getsockname()[1]
            async with websockets.connect(f"ws://127.0.0.1:{port}") as websocket:
                await websocket.send(
                    json.dumps(
                        {
                            "type": "text",
                            "text": "powiedz czesc",
                            "speak": False,
                        }
                    )
                )
                events = []
                while True:
                    event = json.loads(await websocket.recv())
                    events.append(event)
                    if event.get("html"):
                        break

        analyzing = next(
            event
            for event in events
            if event.get("data", {}).get("status") == "analyzing"
        )
        final = events[-1]
        return analyzing, final, speak_calls, events

    analyzing, final, speak_calls, events = asyncio.run(send_text())

    assert analyzing["type"] == "view"
    assert analyzing["data"]["status"] == "analyzing"
    assert any(event.get("type") == "log" for event in events)
    assert final["type"] == "view"
    assert "powiedz czesc" in final["html"]
    assert "Odpowiedz testowa" in final["html"]
    assert speak_calls == []
