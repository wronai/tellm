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
    weather_alias = bot.registry.get("tellm://function/weather_wejherowo").to_dict()
    weather_tombstone = bot.registry.get("tellm://service/old/weather").to_dict()
    audio_artifact = bot.registry.get("tellm://artifact/audio/weather-query-sample").to_dict()
    audio_media = bot.registry.get("tellm://media/audio/weather-query-sample").to_dict()
    project_file = bot.registry.get("tellm://file/project/tellm/server.py").to_dict()
    pytest_command = bot.registry.get("tellm://command/shell/pytest").to_dict()
    litellm_package = bot.registry.get("tellm://package/python/litellm").to_dict()
    jsonschema_package = bot.registry.get("tellm://package/python/jsonschema").to_dict()
    validator_prompt = bot.registry.get("tellm://prompt/validator/workflow-result").to_dict()
    envelope = service_result(
        ok=True,
        uri="tellm://service/test/example",
        result_type="test.result",
        data={"source": "unit_test", "fetched_at": "2026-06-14T00:00:00Z"},
        title="OK",
        summary="done",
    )

    validate_tellm_uri("tellm://service/weather/current", "service")
    validate_tellm_uri("tellm://artifact/audio/weather-query-sample", "artifact")
    validate_tellm_uri("tellm://media/audio/weather-query-sample", "media")
    validate_tellm_uri("tellm://command/shell/pytest", "command")
    validate_tellm_uri("tellm://package/python/litellm", "package")
    validate_tellm_uri("tellm://package/python/jsonschema", "package")
    validate_tellm_uri("tellm://python/module/tellm.bot", "python")
    validate_tellm_uri("tellm://workflow/run/000001", "workflow")
    validate_tellm_uri("tellm://log/workflow/000001", "log")
    validate_tellm_uri("tellm://alias/weather/wejherowo", "alias")
    validate_tellm_uri("tellm://tombstone/weather/old", "tombstone")
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
    assert weather["canonical_uri"] == "tellm://service/weather/current"
    assert weather["domain"] == "weather"
    assert weather["input_schema_uri"] == "tellm://schema/weather/current/input"
    assert "weather.current" in weather["capabilities"]
    assert weather["input_schema"]["$schema"] == JSON_SCHEMA_DRAFT_2020_12
    assert "location" in weather["input_schema"]["properties"]
    assert weather["input_schema"]["required"] == ["location"]
    assert weather["permissions"]["network"] is True
    assert weather["data_policy"]["requires_real_world_data"] is True
    assert weather["render"]["default_view"] == "tellm://view/weather/current"
    assert bot.registry.find_capability("weather.current") == "tellm://service/weather/current"
    assert bot.registry.canonicalize("tellm://function/weather_wejherowo") == "tellm://service/weather/current"
    alias_resolution = bot.registry.resolve_uri("tellm://function/weather_wejherowo", {})
    assert alias_resolution["canonical_uri"] == "tellm://service/weather/current"
    assert alias_resolution["input"] == {"location": "Wejherowo", "country": "PL"}
    assert alias_resolution["warnings"][0]["code"] == "DEPRECATED_URI"
    mapped_resolution = bot.registry.resolve_uri(
        "tellm://service/weather/get",
        {"city": "Gdańsk", "country_code": "PL"},
    )
    assert mapped_resolution["input"] == {"location": "Gdańsk", "country": "PL"}
    assert weather_alias["kind"] == "alias"
    assert weather_alias["canonical_uri"] == "tellm://service/weather/current"
    assert weather_alias["default_input"]["location"] == "Wejherowo"
    assert weather_tombstone["kind"] == "tombstone"
    assert weather_tombstone["status"] == "removed"
    assert weather_tombstone["replacement"] == "tellm://service/weather/current"
    assert audio_artifact["kind"] == "artifact"
    assert audio_artifact["storage"] == {
        "type": "local_file",
        "base": "project",
        "path": "output/test-audio/tellm-pl-pogoda.webm",
    }
    assert audio_artifact["media_type"] == "audio/webm"
    assert "tellm://file/output/test-audio/tellm-pl-pogoda.webm" in audio_artifact["relations"]["physical_file"]
    assert audio_media["kind"] == "media"
    assert audio_media["relations"]["same_as"] == ["tellm://artifact/audio/weather-query-sample"]
    assert project_file["kind"] == "file"
    assert project_file["storage"]["path"] == "tellm/server.py"
    assert pytest_command["kind"] == "command"
    assert pytest_command["command_template"] == "python -m pytest -q {path}"
    assert pytest_command["permissions"]["shell"] is True
    assert pytest_command["permissions"]["llm_execute"] is False
    assert litellm_package["kind"] == "package"
    assert litellm_package["ecosystem"] == "python"
    assert "llm_client" in litellm_package["capabilities"]
    assert jsonschema_package["kind"] == "package"
    assert jsonschema_package["import_name"] == "jsonschema"
    assert "validate_json_schema" in jsonschema_package["capabilities"]
    assert validator_prompt["kind"] == "prompt"
    assert validator_prompt["storage"]["type"] == "inline"
    assert validator_prompt["input_schema"]["required"] == ["result_json", "html"]

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
            {"location": "Wejherowo", "country": "PL"},
        )
    )

    assert result["ok"] is True
    assert result["type"] == "weather.current.result"
    assert result["uri"] == "tellm://service/weather/current"
    assert result["data"]["city"] == "Wejherowo"
    assert result["data"]["temperature_c"] == 15.0
    assert result["data"]["source"] == "open_meteo"
    assert "deszcz" in result["data"]["description"]
    assert result["data"]["timings"]["geocoding_ms"] >= 0
    assert result["data"]["timings"]["forecast_ms"] >= 0
    assert result["data"]["timings"]["provider_total_ms"] >= 0


def test_weather_service_normalizes_country_and_falls_back_geocoding(tmp_path, monkeypatch):
    from urllib import parse
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    geocoding_queries = []

    def fake_http_json(url, timeout=8):
        if "geocoding-api.open-meteo.com" in url:
            query = parse.parse_qs(parse.urlparse(url).query)
            geocoding_queries.append(query)
            if query.get("countryCode") == ["PL"]:
                return {"results": []}
            assert "countryCode" not in query
            return {
                "results": [
                    {
                        "name": "Wejherowo",
                        "country_code": "PL",
                        "latitude": 54.6057,
                        "longitude": 18.2356,
                        "population": 46820,
                    }
                ]
            }
        if "api.open-meteo.com" in url:
            return {
                "current": {
                    "time": "2026-06-14T12:00",
                    "temperature_2m": 16.5,
                    "relative_humidity_2m": 70,
                    "apparent_temperature": 15.9,
                    "weather_code": 2,
                    "wind_speed_10m": 8.0,
                    "wind_direction_10m": 200,
                }
            }
        raise AssertionError(url)

    monkeypatch.setattr(bot, "_http_json", fake_http_json)

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/weather/current",
            {"location": "Wejherowo", "country": "POLAND"},
        )
    )

    assert result["ok"] is True
    assert result["data"]["country"] == "PL"
    assert result["data"]["source"] == "open_meteo"
    assert result["data"]["geocoding"]["query"] == {
        "name": "Wejherowo",
        "country": "POLAND",
        "normalized_country": "PL",
    }
    assert geocoding_queries[0]["countryCode"] == ["PL"]
    assert "countryCode" not in geocoding_queries[1]
    assert len(result["data"]["geocoding"]["attempts"]) == 2


def test_weather_service_returns_location_not_found_diagnostics(tmp_path, monkeypatch):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    def fake_http_json(url, timeout=8):
        if "geocoding-api.open-meteo.com" in url:
            return {"results": []}
        raise AssertionError(url)

    monkeypatch.setattr(bot, "_http_json", fake_http_json)

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/weather/current",
            {"location": "Wejherowo", "country": "POLAND"},
        )
    )

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "LOCATION_NOT_FOUND"
    assert result["errors"][0]["provider"] == "open_meteo_geocoding"
    assert "Location not found" in result["errors"][0]["detail"]
    assert result["errors"][0]["query"] == {
        "name": "Wejherowo",
        "country": "POLAND",
        "normalized_country": "PL",
    }
    assert len(result["errors"][0]["attempts"]) == 2
    assert result["input"]["geocoding"]["query"]["normalized_country"] == "PL"


def test_weather_service_rejects_country_level_location(tmp_path, monkeypatch):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    def fail_http_json(url, timeout=8):
        raise AssertionError("country-level location should not call Open-Meteo: " + url)

    monkeypatch.setattr(bot, "_http_json", fail_http_json)

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/weather/current",
            {"location": "Polska", "country": "PL"},
        )
    )

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "LOCATION_TOO_BROAD"
    assert result["errors"][0]["provider"] == "tellm_location_normalizer"
    assert result["errors"][0]["query"] == {
        "name": "Polska",
        "country": "PL",
        "normalized_country": "PL",
    }
    assert result["input"]["location"] == "Polska"
    assert result["render"]["severity"] == "error"


def test_weather_service_returns_standard_error_when_network_denied(tmp_path, monkeypatch):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    def fake_http_json(url, timeout=8):
        raise PermissionError("Network access is required but not allowed.")

    monkeypatch.setattr(bot, "_http_json", fake_http_json)

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/weather/current",
            {"location": "Wejherowo", "country": "PL"},
        )
    )

    assert result["ok"] is False
    assert result["uri"] == "tellm://service/weather/current"
    assert result["type"] == "weather.current.result"
    assert result["data"] is None
    assert result["input"]["location"] == "Wejherowo"
    assert result["input"]["country"] == "PL"
    assert result["errors"][0]["code"] == "NETWORK_ACCESS_NOT_ALLOWED"
    assert result["errors"][0]["source"] == "tellm://service/weather/current"
    assert result["errors"][0]["recoverable"] is True


def test_price_service_extracts_visible_prices_from_supported_source(tmp_path, monkeypatch):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    requested_urls = []

    def fake_http_text(url, timeout=8):
        requested_urls.append(url)
        return """
        <html><body>
          <h1>Cukier biały</h1>
          <span>Oferta 1: 4,99 zł</span>
          <span>Oferta 2: 5.49 PLN</span>
        </body></html>
        """

    monkeypatch.setattr(bot, "_http_text", fake_http_text)

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/price/search",
            {"query": "cukier", "site": "skapiec.pl"},
        )
    )

    assert result["ok"] is True
    assert result["uri"] == "tellm://service/price/search"
    assert result["type"] == "price.search.result"
    assert result["data"]["source"] == "skapiec.pl"
    assert result["data"]["price_count"] == 2
    assert result["data"]["min_price"] == 4.99
    assert result["data"]["max_price"] == 5.49
    assert result["data"]["timings"]["provider_total_ms"] >= 0
    assert requested_urls == ["https://www.skapiec.pl/szukaj/w_calym_serwisie/cukier"]


def test_price_service_rejects_prices_unrelated_to_requested_product(tmp_path, monkeypatch):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    monkeypatch.setattr(
        bot,
        "_http_text",
        lambda url, timeout=8: """
        <html><body>
          <h1>Wyniki wyszukiwania</h1>
          <article>Taśma TZ-FX751 flexi, czarny druk / zielony podkład od 47 ,01 zł</article>
          <article>Uchwyt meblowy podłużny drewniany brzoza od 20 ,00 zł</article>
          <article>Epson T2431 XL czarny tusz zamiennik od 9 ,80 zł</article>
        </body></html>
        """,
    )

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/price/search",
            {"query": "cukier", "site": "skapiec.pl"},
        )
    )

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "PRICE_RESULT_NOT_RELEVANT"
    diagnostics = result["input"]["candidate_diagnostics"]
    assert diagnostics["raw_candidate_count"] == 3
    assert diagnostics["irrelevant_candidate_count"] == 3
    assert diagnostics["matched_candidate_count"] == 0
    assert diagnostics["relevance_tokens"] == ["cukier"]


def test_price_service_uses_skapiec_category_fallback(tmp_path, monkeypatch):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    requested_urls = []

    def fake_http_text(url, timeout=8):
        requested_urls.append(url)
        if url.endswith("/cat/4235-cukier-i-slodziki.html"):
            return """
            <html><body>
              <article>Diamant CUKIER ŻELUJĄCY 3:1 500 G Brak opinii od 7 ,83 zł w Allegro.pl</article>
              <article>Cukier Królewski biały kryształ 1 kg Brak opinii od 5 ,81 zł w Allegro.pl</article>
            </body></html>
            """
        return """
        <html><body>
          <nav><a href="/cat/4235-cukier-i-slodziki.html">Cukier</a></nav>
          <article>Taśma TZ-FX751 flexi, czarny druk / zielony podkład od 47 ,01 zł</article>
          <article>Uchwyt meblowy podłużny drewniany brzoza od 20 ,00 zł</article>
        </body></html>
        """

    monkeypatch.setattr(bot, "_http_text", fake_http_text)

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/price/search",
            {"query": "cukier", "site": "skapiec.pl"},
        )
    )

    assert result["ok"] is True
    assert result["data"]["price_count"] == 2
    assert result["data"]["min_price"] == 5.81
    assert result["data"]["max_price"] == 7.83
    assert result["data"]["url"] == "https://www.skapiec.pl/cat/4235-cukier-i-slodziki.html"
    assert result["data"]["requested_url"] == "https://www.skapiec.pl/szukaj/w_calym_serwisie/cukier"
    assert result["data"]["source_discovery"]["provider"] == "skapiec_category"
    assert requested_urls == [
        "https://www.skapiec.pl/szukaj/w_calym_serwisie/cukier",
        "https://www.skapiec.pl/cat/4235-cukier-i-slodziki.html",
    ]


def test_price_service_returns_structured_not_found_error(tmp_path, monkeypatch):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    monkeypatch.setattr(bot, "_http_text", lambda url, timeout=8: "<html>brak ceny</html>")

    result = asyncio.run(
        bot.execute_resource(
            "tellm://service/price/search",
            {"query": "cukier", "site": "allegro.pl"},
        )
    )

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "PRICE_NOT_FOUND"
    assert result["errors"][0]["provider"] == "allegro.pl"
    assert result["input"]["query"] == "cukier"
    assert result["input"]["site"] == "allegro.pl"
    assert result["render"]["severity"] == "error"


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


def test_autoimprove_finds_provider_location_resolution_failure(tmp_path):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    bot.record_execution(
        uri="tellm://service/weather/current",
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
                "summary": "Nie znaleziono lokalizacji",
            },
            "errors": [
                {
                    "code": "LOCATION_NOT_FOUND",
                    "source": "tellm://service/weather/current",
                    "provider": "open_meteo_geocoding",
                    "detail": {
                        "query": {
                            "name": "Wejherowo",
                            "country": "POLAND",
                            "normalized_country": "PL",
                        }
                    },
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

    assert "provider_location_resolution_failed" in finding_types
    assert result["data"]["summary"]["provider_location_resolution_failed"] == 1


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
        assert "tellm://service/price/search" in messages[0]["content"]
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
        raise AssertionError("weather query should use local registry router")

    monkeypatch.setattr(bot, "_completion", fake_completion)

    task = asyncio.run(bot.analyze_query("Jaka jest pogoda w Wejherowie?"))

    assert task.function_name == "tellm://service/weather/current"
    assert task.parameters == {"location": "Wejherowo", "country": "PL"}
    assert task.processes == []
    assert task.code == ""
    assert task.view["_router"] == "local_weather"


def test_analyze_query_routes_price_to_registry_service(tmp_path, monkeypatch):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    def fake_completion(messages):
        raise AssertionError("price query should use local registry router")

    monkeypatch.setattr(bot, "_completion", fake_completion)

    task = asyncio.run(bot.analyze_query("jaka jest cena cukru na skapiec.pl"))

    assert task.function_name == "tellm://service/price/search"
    assert task.parameters == {
        "query": "cukier",
        "site": "skapiec.pl",
        "original_query": "jaka jest cena cukru na skapiec.pl",
    }
    assert task.processes == []
    assert task.code == ""
    assert task.view["_router"] == "local_price"


def test_analyze_query_can_still_rewrite_ad_hoc_weather_llm_response(tmp_path, monkeypatch):
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

    task = asyncio.run(bot.analyze_query("pogoda"))

    assert task.function_name == "tellm://service/weather/current"
    assert task.parameters == {"location": "", "country": "PL"}
    assert task.processes == []
    assert task.code == ""


def test_analyze_query_reads_json_from_reasoning_when_content_is_empty(tmp_path, monkeypatch):
    from tellm import create_bot

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))

    def fake_completion(messages):
        class Message:
            content = None
            reasoning_content = (
                "Model notes {\"ignored\": true}\n"
                "{\"type\":\"now\",\"function_name\":\"run\",\"parameters\":{\"x\":1},"
                "\"processes\":[],\"code\":\"\"}"
            )

        class Choice:
            message = Message()

        class Response:
            choices = [Choice()]

        return Response()

    monkeypatch.setattr(bot, "_completion", fake_completion)

    task = asyncio.run(bot.analyze_query("policz"))

    assert task.function_name == "run"
    assert task.parameters == {"x": 1}
    assert task.processes == []


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
            response = await reader.read(50000)
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
    assert b'id="copyWorkflowLogs"' in response
    assert b"workflowLogsText" in response
    assert b"restoreWorkflowLogs" in response
    assert b"tellm://artifact/json/workflow-result/" in response
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
            response = await reader.read(200000)
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
    assert b"/schema?uri=tellm://..." in response
    assert b"/schema/input?uri=tellm://..." in response
    assert b"/schema/output?uri=tellm://..." in response
    assert b"/describe?uri=tellm://..." in response
    assert b"/permissions?uri=tellm://..." in response
    assert b"/health?uri=tellm://..." in response
    assert b"/history?uri=tellm://..." in response
    assert b"/validate-input?uri=" in response
    assert b"/validate-output?uri=" in response
    assert b"Adresowalne artefakty" in response
    assert b"tellm://artifact/audio/weather-query-sample" in response
    assert b"tellm://command/shell/pytest" in response
    assert b"tellm://package/python/litellm" in response
    assert b"tellm://package/python/jsonschema" in response
    assert b"tellm://workflow/run/35" in response
    assert b"tellm://view/workflow/35" in response
    assert b"tellm://log/workflow/35" in response
    assert b"include_value=true" in response
    assert b"tellm://function/weather_wejherowo" in response
    assert b"capability=weather.current" in response
    assert b"status=deprecated" in response
    assert b"Tellm Resource Manifest 1.0" in response
    assert b"Tellm Service Result 1.0" in response


def test_server_registry_http_endpoints(tmp_path):
    from tellm import Task, TaskType, create_bot
    from tellm.server import TellmServer

    bot = create_bot(db_path=str(tmp_path / "tellm.db"))
    saved_view = bot.generate_view(
        "runtime view",
        Task(TaskType.NOW, "tellm://function/system/echo", {"text": "runtime"}),
        {"ok": True, "value": "runtime"},
    )
    view_id = saved_view.view_id

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
    weather_registry_response = asyncio.run(
        request("/registry?kind=service&tag=weather")
    )
    weather_domain_registry_response = asyncio.run(request("/registry?domain=weather"))
    weather_capability_registry_response = asyncio.run(
        request("/registry?capability=weather.current")
    )
    deprecated_registry_response = asyncio.run(request("/registry?status=deprecated"))
    artifact_registry_response = asyncio.run(request("/registry?kind=artifact"))
    command_registry_response = asyncio.run(request("/registry?kind=command"))
    package_registry_response = asyncio.run(request("/registry?kind=package"))
    manifest_response = asyncio.run(request("/manifest"))
    openapi_response = asyncio.run(request("/openapi.json"))
    asyncapi_response = asyncio.run(request("/asyncapi.json"))
    execute_response = asyncio.run(request("/execute"))
    resource_response = asyncio.run(
        request("/resource?uri=tellm://function/system/now")
    )
    weather_resource_response = asyncio.run(
        request("/resource?uri=tellm://service/weather/current")
    )
    weather_alias_resource_response = asyncio.run(
        request("/resource?uri=tellm://function/weather_wejherowo")
    )
    weather_input_schema_resource_response = asyncio.run(
        request("/resource?uri=tellm://schema/service/weather.current/input")
    )
    audio_artifact_response = asyncio.run(
        request("/resource?uri=tellm://artifact/audio/weather-query-sample")
    )
    pytest_command_response = asyncio.run(
        request("/resource?uri=tellm://command/shell/pytest")
    )
    litellm_package_response = asyncio.run(
        request("/resource?uri=tellm://package/python/litellm")
    )
    workflow_run_response = asyncio.run(
        request("/resource?uri=tellm://workflow/run/%d" % view_id)
    )
    runtime_view_response = asyncio.run(
        request("/resource?uri=tellm://view/workflow/%d" % view_id)
    )
    workflow_log_response = asyncio.run(
        request("/resource?uri=tellm://log/workflow/%d" % view_id)
    )
    runtime_json_artifact_response = asyncio.run(
        request("/resource?uri=tellm://artifact/json/workflow-result/%d" % view_id)
    )
    schema_response = asyncio.run(
        request("/schema?uri=tellm://service/weather/current")
    )
    input_schema_response = asyncio.run(
        request("/schema/input?uri=tellm://service/weather/current")
    )
    output_schema_response = asyncio.run(
        request("/schema/output?uri=tellm://service/weather/current")
    )
    describe_response = asyncio.run(
        request("/describe?uri=tellm://service/weather/current")
    )
    permissions_response = asyncio.run(
        request("/permissions?uri=tellm://service/weather/current")
    )
    health_response = asyncio.run(
        request("/health?uri=tellm://service/weather/current")
    )
    history_response = asyncio.run(
        request("/history?uri=tellm://service/weather/current")
    )
    valid_input_response = asyncio.run(
        request(
            "/validate-input?uri=tellm://service/weather/current&input=%7B%22location%22%3A%22Wejherowo%22%2C%22country%22%3A%22PL%22%7D"
        )
    )
    invalid_input_response = asyncio.run(
        request(
            "/validate-input?uri=tellm://service/weather/current&input=%7B%22country%22%3A%22PL%22%7D"
        )
    )
    resolve_response = asyncio.run(
        request("/resolve?uri=tellm://service/domain/check")
    )
    resolve_audio_response = asyncio.run(
        request("/resolve?uri=tellm://artifact/audio/weather-query-sample")
    )
    resolve_alias_response = asyncio.run(
        request("/resolve?uri=tellm://function/weather_wejherowo")
    )
    resolve_legacy_input_response = asyncio.run(
        request(
            "/resolve?uri=tellm://service/weather/get&input=%7B%22city%22%3A%22Wejherowo%22%2C%22country_code%22%3A%22PL%22%7D"
        )
    )
    resolve_prompt_value_response = asyncio.run(
        request("/resolve?uri=tellm://prompt/validator/workflow-result&include_value=true")
    )
    resolve_view_value_response = asyncio.run(
        request("/resolve?uri=tellm://view/workflow/%d&include_value=true" % view_id)
    )

    assert registry_response.startswith(b"HTTP/1.1 200 OK")
    assert b"application/json" in registry_response
    assert b"tellm://service/domain/check" in registry_response
    assert b"OPENROUTER_API_KEY" in registry_response
    assert b"secret-value" not in registry_response

    assert weather_registry_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"items"' in weather_registry_response
    assert b"tellm://service/weather/current" in weather_registry_response
    assert b"tellm://service/domain/check" not in weather_registry_response

    assert weather_domain_registry_response.startswith(b"HTTP/1.1 200 OK")
    assert b"tellm://service/weather/current" in weather_domain_registry_response
    assert b"tellm://function/weather_wejherowo" in weather_domain_registry_response

    assert weather_capability_registry_response.startswith(b"HTTP/1.1 200 OK")
    assert b"tellm://service/weather/current" in weather_capability_registry_response
    assert b"weather.current" in weather_capability_registry_response
    assert b"tellm://service/domain/check" not in weather_capability_registry_response

    assert deprecated_registry_response.startswith(b"HTTP/1.1 200 OK")
    assert b"tellm://function/weather_wejherowo" in deprecated_registry_response
    assert b"tellm://service/weather/get" in deprecated_registry_response

    assert artifact_registry_response.startswith(b"HTTP/1.1 200 OK")
    assert b"tellm://artifact/audio/weather-query-sample" in artifact_registry_response
    assert b'"storage_type": "local_file"' in artifact_registry_response

    assert command_registry_response.startswith(b"HTTP/1.1 200 OK")
    assert b"tellm://command/shell/pytest" in command_registry_response
    assert b'"run_tests"' in command_registry_response

    assert package_registry_response.startswith(b"HTTP/1.1 200 OK")
    assert b"tellm://package/python/litellm" in package_registry_response
    assert b'"llm_client"' in package_registry_response

    assert manifest_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"manifest_version": "1.0.0"' in manifest_response
    assert b'"$schema": "https://json-schema.org/draft/2020-12/schema"' in manifest_response
    assert b"tellm://schema/tellm/service-result" in manifest_response

    assert openapi_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"openapi": "3.1.0"' in openapi_response
    assert b'TellmServiceResult' in openapi_response
    assert b'"/execute"' in openapi_response
    assert b'"/schema/input"' in openapi_response
    assert b'"/validate-input"' in openapi_response
    assert b'"post"' in openapi_response
    assert b"ExecuteRequest" in openapi_response

    assert asyncapi_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"asyncapi": "3.1.0"' in asyncapi_response
    assert b"ClientExecute" in asyncapi_response

    assert execute_response.startswith(b"HTTP/1.1 501 Not Implemented")
    assert b"HTTP_BODY_TRANSPORT_NOT_ENABLED" in execute_response

    assert resource_response.startswith(b"HTTP/1.1 200 OK")
    assert b"tellm://function/system/now" in resource_response

    assert weather_resource_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"canonical_uri": "tellm://service/weather/current"' in weather_resource_response
    assert b'"domain": "weather"' in weather_resource_response
    assert b'"weather.current"' in weather_resource_response
    assert b'"location"' in weather_resource_response
    assert b'"required": ["location"]' in weather_resource_response

    assert weather_alias_resource_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"kind": "alias"' in weather_alias_resource_response
    assert b'"target": "tellm://service/weather/current"' in weather_alias_resource_response
    assert b'"default_input": {"location": "Wejherowo", "country": "PL"}' in weather_alias_resource_response

    assert weather_input_schema_resource_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"kind": "schema"' in weather_input_schema_resource_response
    assert b'"resource_uri": "tellm://service/weather/current"' in weather_input_schema_resource_response
    assert b'"required": ["location"]' in weather_input_schema_resource_response

    assert audio_artifact_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"kind": "artifact"' in audio_artifact_response
    assert b'"media_type": "audio/webm"' in audio_artifact_response
    assert b'"path": "output/test-audio/tellm-pl-pogoda.webm"' in audio_artifact_response

    assert pytest_command_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"kind": "command"' in pytest_command_response
    assert b'"command_template": "python -m pytest -q {path}"' in pytest_command_response

    assert litellm_package_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"kind": "package"' in litellm_package_response
    assert b'"ecosystem": "python"' in litellm_package_response

    assert workflow_run_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"uri": "tellm://workflow/run/' in workflow_run_response
    assert b'"kind": "workflow"' in workflow_run_response
    assert b'"output_artifacts"' in workflow_run_response
    assert b'"tellm://log/workflow/' in workflow_run_response

    assert runtime_view_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"uri": "tellm://view/workflow/' in runtime_view_response
    assert b'"storage": {"type": "sqlite", "table": "views"' in runtime_view_response
    assert b'"content_type": "text/html"' in runtime_view_response

    assert workflow_log_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"uri": "tellm://log/workflow/' in workflow_log_response
    assert b'"kind": "log"' in workflow_log_response
    assert b'"describes"' in workflow_log_response

    assert runtime_json_artifact_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"uri": "tellm://artifact/json/workflow-result/' in runtime_json_artifact_response
    assert b'"rendered_as"' in runtime_json_artifact_response

    assert schema_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"schemas"' in schema_response
    assert b'"input"' in schema_response
    assert b'"output"' in schema_response

    assert input_schema_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"schema": "input"' in input_schema_response
    assert b'"required": ["location"]' in input_schema_response

    assert output_schema_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"schema": "output"' in output_schema_response
    assert b'"required": ["ok", "type", "data", "message", "errors"]' in output_schema_response

    assert describe_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"can_execute": true' in describe_response
    assert b'"input_required": ["location"]' in describe_response
    assert b"weather.current.result" in describe_response

    assert permissions_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"network": true' in permissions_response

    assert health_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"recent_executions"' in health_response

    assert history_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"history"' in history_response

    assert valid_input_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"valid": true' in valid_input_response

    assert invalid_input_response.startswith(b"HTTP/1.1 400 Bad Request")
    assert b'"valid": false' in invalid_input_response
    assert b"$.location" in invalid_input_response

    assert resolve_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"has_callable": true' in resolve_response
    assert b'"resolved"' in resolve_response

    assert resolve_audio_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"storage_type": "local_file"' in resolve_audio_response
    assert b'"base": "project"' in resolve_audio_response
    assert b'"path": "output/test-audio/tellm-pl-pogoda.webm"' in resolve_audio_response
    assert b'"binary_or_non_text_content"' in resolve_audio_response or b'"value_included": false' in resolve_audio_response

    assert resolve_alias_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"requested_uri": "tellm://function/weather_wejherowo"' in resolve_alias_response
    assert b'"canonical_uri": "tellm://service/weather/current"' in resolve_alias_response
    assert b'"DEPRECATED_URI"' in resolve_alias_response
    assert b'"location": "Wejherowo"' in resolve_alias_response

    assert resolve_legacy_input_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"canonical_uri": "tellm://service/weather/current"' in resolve_legacy_input_response
    assert b'"location": "Wejherowo"' in resolve_legacy_input_response
    assert b'"country": "PL"' in resolve_legacy_input_response

    assert resolve_prompt_value_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"storage_type": "inline"' in resolve_prompt_value_response
    assert b'"value_included": true' in resolve_prompt_value_response
    assert b"Sprawd" in resolve_prompt_value_response

    assert resolve_view_value_response.startswith(b"HTTP/1.1 200 OK")
    assert b'"storage_type": "sqlite"' in resolve_view_value_response
    assert b'"value_included": true' in resolve_view_value_response
    assert b"runtime view" in resolve_view_value_response


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


def test_server_local_validation_skips_llm_for_trusted_registry_result(tmp_path, monkeypatch):
    from tellm import Task, TaskType
    from tellm.server import TellmServer

    class DummyWebSocket:
        def __init__(self):
            self.events = []

        async def send(self, raw):
            self.events.append(json.loads(raw))

    def fail_completion(*args, **kwargs):
        raise AssertionError("trusted registry result should not call LLM validation")

    server = TellmServer(
        host="127.0.0.1",
        port=0,
        db_path=str(tmp_path / "tellm.db"),
    )
    monkeypatch.setattr("tellm.server.completion", fail_completion)
    task = Task(
        TaskType.NOW,
        "tellm://service/weather/current",
        {"location": "Szemud", "country": "PL"},
    )
    result = {
        "ok": True,
        "uri": "tellm://service/weather/current",
        "type": "weather.current.result",
        "data": {
            "city": "Szemud",
            "country": "PL",
            "temperature_c": 11.8,
            "description": "lekki deszcz",
            "source": "open_meteo",
            "provider": "open_meteo",
        },
        "message": {
            "title": "Pogoda w Szemud",
            "summary": "Aktualnie 11.8°C, lekki deszcz.",
            "details": "Realny provider.",
        },
        "errors": [],
        "warnings": [],
        "render": {"renderer": "auto", "template": "weather_current"},
    }
    view = server.bot.generate_view("Jaka jest pogoda w Szemud", task, result)
    logs = server._render_logs("Jaka jest pogoda w Szemud", task, result, view, view.to_html())
    websocket = DummyWebSocket()

    validated_view, answer, render_logs = asyncio.run(
        server._validate_and_repair(
            websocket,
            "Jaka jest pogoda w Szemud",
            task,
            result,
            view,
            logs,
            client_logs=[],
        )
    )

    assert validated_view is view
    assert answer == "Aktualnie 11.8°C, lekki deszcz."
    assert render_logs == logs
    assert any(event["stage"] == "local_validation" and event["status"] == "ok" for event in websocket.events)
    assert not any(event["stage"] == "llm_validation" for event in websocket.events)


def test_server_local_validation_skips_llm_for_structured_service_error(tmp_path, monkeypatch):
    from tellm import Task, TaskType
    from tellm.server import TellmServer

    class DummyWebSocket:
        def __init__(self):
            self.events = []

        async def send(self, raw):
            self.events.append(json.loads(raw))

    def fail_completion(*args, **kwargs):
        raise AssertionError("schema-valid service error should not call LLM validation")

    server = TellmServer(
        host="127.0.0.1",
        port=0,
        db_path=str(tmp_path / "tellm.db"),
    )
    monkeypatch.setattr("tellm.server.completion", fail_completion)
    task = Task(
        TaskType.NOW,
        "tellm://service/weather/current",
        {"location": "Polska", "country": "PL"},
    )
    result = {
        "ok": False,
        "uri": "tellm://service/weather/current",
        "type": "weather.current.result",
        "data": None,
        "message": {
            "title": "Podaj konkretną lokalizację",
            "summary": "Zapytanie wskazuje zbyt szeroki obszar.",
            "details": "Podaj miasto albo współrzędne.",
        },
        "errors": [
            {
                "code": "LOCATION_TOO_BROAD",
                "source": "tellm://service/weather/current",
                "detail": "Location is too broad for current weather: Polska",
                "provider": "tellm_location_normalizer",
                "recoverable": True,
            }
        ],
        "warnings": [],
        "meta": {"source": None, "fetched_at": None},
        "render": {"renderer": "auto", "template": "status_card", "severity": "error"},
    }
    view = server.bot.generate_view("Jaka jest pogoda w Polska", task, result)
    logs = server._render_logs("Jaka jest pogoda w Polska", task, result, view, view.to_html())
    websocket = DummyWebSocket()

    validated_view, answer, render_logs = asyncio.run(
        server._validate_and_repair(
            websocket,
            "Jaka jest pogoda w Polska",
            task,
            result,
            view,
            logs,
            client_logs=[],
        )
    )

    assert validated_view is view
    assert answer == "Zapytanie wskazuje zbyt szeroki obszar."
    assert render_logs == logs
    assert any(event["stage"] == "local_validation" and event["status"] == "ok" for event in websocket.events)
    assert not any(event["stage"] == "llm_validation" for event in websocket.events)


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
