# tellm v4 - STT+TTS+LLM+SQLite+HTML

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `tellm`
- **version**: `0.0.0`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: requirements.txt, testql(1), app.doql.less, goal.yaml, .env.example, src(4 mod), project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: tellm;
  version: 0.1.0;
}

tests {
  import: testql-scenarios/**/*.testql.toon.yaml;
}

env_vars {
  keys: OPENROUTER_API_KEY, LLM_MODEL, HOST, PORT;
}

deploy {
  target: docker-compose;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  template_file: .env.example;
  vars: HOST, LLM_MODEL, OPENROUTER_API_KEY, PORT;
  runtime_llm: OPENROUTER_API_KEY;
}
```

### Source Modules

- `tellm.bot`
- `tellm.config`
- `tellm.main`
- `tellm.server`

## Source Map

*Top 4 modules by symbol density — signatures for LLM orientation.*

### `tellm.bot` (`tellm/bot.py`)

```python
class TaskType:
class WeatherLocationResolutionError:
    def __init__(city, country, normalized_country, attempts)  # CC=2
class WeatherLocationTooBroadError:
    def __init__(location, country, normalized_country)  # CC=2
class Task:
class ViewData:
    def to_dict()  # CC=1
    def _safe_json(value)  # CC=1
    def _safe_text(value)  # CC=2
    def _render_items(items)  # CC=5
    def _render_table(block)  # CC=11 ⚠
    def _render_block(block)  # CC=11 ⚠
    def _render_dynamic()  # CC=6
    def to_html()  # CC=5
class TellmBot:
    def __init__(config, db_path)  # CC=2
    def _init_db()  # CC=1
    def record_execution(uri, kind, ok, status, error, result, logs, metadata)  # CC=3
    def save_autoimprovement_report(report, html)  # CC=5
    def update_autoimprovement_report_html(report_id, report, html)  # CC=1
    def get_latest_autoimprovement_report()  # CC=2
    def get_latest_autoimprovement_html()  # CC=3
    def save_task(task, result, transcription)  # CC=1
    def save_evolution(function_name, step)  # CC=1
    def save_view(view)  # CC=1
    def get_view_html(view_id)  # CC=2
    def get_view_record(view_id)  # CC=4
    def _is_text_content_type(content_type)  # CC=3
    def _storage_base_path(base)  # CC=2
    def _value_preview(value)  # CC=5
    def resolve_resource_document(resource, include_value, max_bytes, route_info)  # CC=47 ⚠
    def resolve_resource(uri, input_data, include_value, max_bytes)  # CC=2
    def get_tasks(limit)  # CC=2
    def register_function(name, func)  # CC=1
    def _package_version(package_name)  # CC=2
    def _register_file_resource(uri, name, path, content_type, description, tags)  # CC=1
    def _register_package_resource(package_name, import_name, capabilities, network)  # CC=1
    def _register_artifact_resources()  # CC=3
    def _register_uri_aliases()  # CC=1
    def _init_registry()  # CC=3
    def _registry_now(params)  # CC=1
    def _registry_echo(params)  # CC=1
    def _registry_autoimprove(params)  # CC=2
    def _weather_code_description(code)  # CC=2
    def _http_json(url, timeout)  # CC=1
    def _http_text(url, timeout)  # CC=2
    def _normalize_country_code(country)  # CC=4
    def _is_country_level_weather_location(cls, location)  # CC=5
    def _score_geocode_result(result, city, country_code)  # CC=6
    def _geocode_city(city, country)  # CC=5
    def _registry_weather_current(params)  # CC=29 ⚠
    def _normalize_domain(domain)  # CC=2
    def _registry_domain_check(params)  # CC=14 ⚠
    def _normalize_price_site(site)  # CC=3
    def _commerce_search_url(site, query)  # CC=3
    def _text_from_html(document)  # CC=1
    def _parse_price_amount(raw)  # CC=6
    def _price_relevance_tokens(query)  # CC=6
    def _price_relevance(snippet, tokens)  # CC=5
    def _extract_price_candidates(cls, document, limit, query, diagnostics)  # CC=7
    def _price_error_result(uri, code, title, summary, details, detail, query, site, source_url, provider, extra)  # CC=3
    def _registry_price_search(params)  # CC=30 ⚠
    def execute_resource(uri, payload)  # CC=9
    def _completion(messages)  # CC=1
    def _message_text(message)  # CC=14 ⚠
    def _parse_json_response(content)  # CC=18 ⚠
    def _normalize_processes(value)  # CC=5
    def _ensure_function_state(function_name)  # CC=1
    def _restricted_import(name, globals, locals, fromlist, level)  # CC=2
    def _process_globals()  # CC=1
    def _execute_registered_function(name, params)  # CC=2
    def _execute_python_process(process, fallback_params)  # CC=22 ⚠
    def execute_processes(task)  # CC=7
    def _get_stt_model()  # CC=2
    def _get_tts()  # CC=2
    def _looks_like_weather_query(query)  # CC=2
    def _normalize_weather_location(value)  # CC=6
    def _weather_location_from_query(query, parameters)  # CC=5
    def _route_weather_task(query, task)  # CC=7
    def _local_weather_task_from_query(query)  # CC=3
    def _looks_like_price_query(query)  # CC=2
    def _price_site_from_query(query, parameters)  # CC=4
    def _normalize_price_product(value)  # CC=2
    def _price_query_from_query(query, parameters)  # CC=5
    def _route_price_task(query, task)  # CC=6
    def _local_price_task_from_query(query)  # CC=4
    def _local_task_from_query(query)  # CC=3
    def analyze_query(query)  # CC=13 ⚠
    def evolve_function(task)  # CC=4
    def execute_task(task)  # CC=8
    def transcribe(audio_data, suffix)  # CC=5
    def speak(text)  # CC=1
    def _render_autoimprovement_data(data, message)  # CC=10 ⚠
    def _render_data_from_service_result(result)  # CC=13 ⚠
    def generate_view(transcription, task, result)  # CC=4
```

### `tellm.server` (`tellm/server.py`)

```python
def _websocket_logger()  # CC=1, fan=4
def _browser_client_html(host)  # CC=1, fan=0
def _docs_html(host)  # CC=1, fan=1
def _registry_ui_html(bot, host)  # CC=6, fan=7
def _autoimprovement_html(host)  # CC=1, fan=1
def _openapi_document(host)  # CC=1, fan=2
def _asyncapi_document(host)  # CC=1, fan=1
class TellmServer:
    def __init__(host, port, db_path)  # CC=1
    def register_function(name, func)  # CC=1
    def _http_response(body, content_type, status)  # CC=1
    def _json_response(data, status)  # CC=1
    def _resource_entry_response(uri)  # CC=4
    def _registry_item_summary(entry)  # CC=2
    def _virtual_schema_resource(uri)  # CC=5
    def _virtual_view_resource(uri)  # CC=9
    def _schema_bundle(entry)  # CC=2
    def _describe_entry(entry)  # CC=6
    def _validation_error(message)  # CC=2
    def _validate_payload(uri, payload, schema_kind)  # CC=4
    def _payload_from_query(params, field)  # CC=4
    def process_request(connection, request)  # CC=95 ⚠
    def _call_maybe_async(func)  # CC=2
    def _run_blocking(func)  # CC=1
    def _send_log(websocket, stage, status, message, details)  # CC=2
    def _send_state(websocket, state, label)  # CC=2
    def _compact(value, max_chars)  # CC=2
    def _collect_source_values(value)  # CC=6
    def _requires_real_world_data(text, task)  # CC=3
    def _registry_entry_for_task(task)  # CC=2
    def _data_source_findings(transcription, task, result)  # CC=21 ⚠
    def _append_data_quality_warnings(view, findings)  # CC=8
    def _log_details(logs, stage)  # CC=4
    def _result_business_ok(result)  # CC=10 ⚠
    def _service_result_log(cls, result)  # CC=8
    def _workflow_history_status(cls, result, data_quality_findings)  # CC=3
    def _render_logs(transcription, task, result, view, html, client_logs)  # CC=12 ⚠
    def _local_validation_verdict(task, result, view, render_logs)  # CC=23 ⚠
    def _validate_and_repair(websocket, transcription, task, result, view, render_logs, client_logs, max_attempts)  # CC=12 ⚠
    def _answer_from_service_result(result)  # CC=5
    def _looks_executable_query(text)  # CC=2
    def _repair_count(logs)  # CC=5
    def _duration_ms(start)  # CC=1
    def _handle_transcription(websocket, transcription, speak, client_logs)  # CC=13 ⚠
    def _handle_resource_execution(websocket, uri, payload, speak, client_logs)  # CC=14 ⚠
    def _handle_test_transcription(websocket, transcription, source, speak)  # CC=2
    def _audio_payload(audio)  # CC=5
    def _process_message(websocket, data)  # CC=15 ⚠
    def handle(websocket, path)  # CC=10 ⚠
    def serve_forever()  # CC=1
    def run()  # CC=2
```

### `tellm.config` (`tellm/config.py`)

```python
def load_config()  # CC=1, fan=3
class Config:
```

### `tellm.main` (`tellm/main.py`)

```python
def main()  # CC=3, fan=8
```

## Call Graph

*47 nodes · 39 edges · 7 modules · CC̄=5.5*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `_validate_and_repair` *(in tellm.server.TellmServer)* | 12 ⚠ | 0 | 40 | **40** |
| `validate_schema` *(in tellm.registry.core)* | 23 ⚠ | 9 | 27 | **36** |
| `normalize_issue_list` *(in tellm.registry.core)* | 11 ⚠ | 2 | 20 | **22** |
| `_registry_domain_check` *(in tellm.bot.TellmBot)* | 14 ⚠ | 0 | 22 | **22** |
| `_local_validation_verdict` *(in tellm.server.TellmServer)* | 23 ⚠ | 0 | 17 | **17** |
| `service_result` *(in tellm.registry.core)* | 6 | 8 | 7 | **15** |
| `generate_fixture` *(in scripts.generate_test_audio)* | 2 | 1 | 13 | **14** |
| `main` *(in main)* | 3 | 0 | 14 | **14** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/tellm
# generated in 0.02s
# nodes: 47 | edges: 39 | modules: 7
# CC̄=5.5

HUBS[20]:
  tellm.server.TellmServer._validate_and_repair
    CC=12  in:0  out:40  total:40
  tellm.registry.core.validate_schema
    CC=23  in:9  out:27  total:36
  tellm.registry.core.normalize_issue_list
    CC=11  in:2  out:20  total:22
  tellm.bot.TellmBot._registry_domain_check
    CC=14  in:0  out:22  total:22
  tellm.server.TellmServer._local_validation_verdict
    CC=23  in:0  out:17  total:17
  tellm.registry.core.service_result
    CC=6  in:8  out:7  total:15
  scripts.generate_test_audio.generate_fixture
    CC=2  in:1  out:13  total:14
  main.main
    CC=3  in:0  out:14  total:14
  scripts.protocol_smoke.send_ws_payload
    CC=4  in:2  out:10  total:12
  tellm.registry.core.RegistryEntry.__post_init__
    CC=17  in:0  out:12  total:12
  scripts.generate_test_audio.main
    CC=4  in:0  out:9  total:9
  config.load_config
    CC=1  in:3  out:6  total:9
  scripts.protocol_smoke.check_http
    CC=3  in:2  out:7  total:9
  tellm.registry.core.validate_tellm_uri
    CC=9  in:2  out:7  total:9
  tellm.registry.core.ResourceRegistry.execute
    CC=5  in:0  out:9  total:9
  scripts.protocol_smoke.check_ws_audio
    CC=4  in:1  out:8  total:9
  tellm.bot.TellmBot._price_relevance_tokens
    CC=6  in:0  out:9  total:9
  tellm.registry.core.ResourceRegistry._call
    CC=4  in:0  out:8  total:8
  scripts.protocol_smoke.check_ws_text
    CC=3  in:1  out:7  total:8
  tellm.registry.core.ResourceRegistry.list
    CC=4  in:3  out:4  total:7

MODULES:
  config  [1 funcs]
    load_config  CC=1  out:6
  main  [1 funcs]
    main  CC=3  out:14
  scripts.generate_test_audio  [4 funcs]
    generate_fixture  CC=2  out:13
    main  CC=4  out:9
    require_tool  CC=2  out:2
    run  CC=1  out:1
  scripts.protocol_smoke  [9 funcs]
    async_main  CC=7  out:3
    audio_data_url  CC=1  out:4
    check_http  CC=3  out:7
    check_ws_audio  CC=4  out:8
    check_ws_text  CC=3  out:7
    get_url  CC=3  out:4
    mime_for_audio  CC=3  out:1
    send_ws_payload  CC=4  out:10
    ws_ssl_context  CC=3  out:2
  tellm.bot  [6 funcs]
    __init__  CC=2  out:5
    _price_error_result  CC=3  out:2
    _price_relevance_tokens  CC=6  out:9
    _registry_domain_check  CC=14  out:22
    _registry_echo  CC=1  out:1
    _registry_now  CC=1  out:3
  tellm.registry.core  [19 funcs]
    __post_init__  CC=17  out:12
    _call  CC=4  out:8
    execute  CC=5  out:9
    list  CC=4  out:4
    manifest  CC=2  out:4
    read  CC=3  out:5
    register_alias  CC=11  out:2
    _schema_types  CC=4  out:3
    json_like  CC=2  out:2
    normalize_issue_list  CC=11  out:20
  tellm.server  [7 funcs]
    _local_validation_verdict  CC=23  out:17
    _validate_and_repair  CC=12  out:40
    _validate_payload  CC=4  out:6
    serve_forever  CC=1  out:5
    _asyncapi_document  CC=1  out:1
    _openapi_document  CC=1  out:2
    _websocket_logger  CC=1  out:4

EDGES:
  scripts.generate_test_audio.generate_fixture → scripts.generate_test_audio.run
  scripts.generate_test_audio.generate_fixture → scripts.generate_test_audio.require_tool
  scripts.generate_test_audio.main → scripts.generate_test_audio.generate_fixture
  scripts.protocol_smoke.check_http → scripts.protocol_smoke.get_url
  scripts.protocol_smoke.audio_data_url → scripts.protocol_smoke.mime_for_audio
  scripts.protocol_smoke.send_ws_payload → scripts.protocol_smoke.ws_ssl_context
  scripts.protocol_smoke.check_ws_text → scripts.protocol_smoke.send_ws_payload
  scripts.protocol_smoke.check_ws_audio → scripts.protocol_smoke.audio_data_url
  scripts.protocol_smoke.check_ws_audio → scripts.protocol_smoke.send_ws_payload
  scripts.protocol_smoke.async_main → scripts.protocol_smoke.check_ws_text
  scripts.protocol_smoke.async_main → scripts.protocol_smoke.check_ws_audio
  tellm.server._openapi_document → tellm.registry.core.registry_manifest_schema
  tellm.server._openapi_document → tellm.registry.core.service_result_schema
  tellm.server._asyncapi_document → tellm.registry.core.registry_manifest_schema
  tellm.server.TellmServer._validate_payload → tellm.registry.core.validate_schema
  tellm.server.TellmServer._local_validation_verdict → tellm.registry.core.validate_schema
  tellm.server.TellmServer._validate_and_repair → config.load_config
  tellm.server.TellmServer.serve_forever → tellm.server._websocket_logger
  tellm.bot.TellmBot.__init__ → config.load_config
  tellm.bot.TellmBot._registry_now → tellm.registry.core.service_result
  tellm.bot.TellmBot._registry_echo → tellm.registry.core.service_result
  tellm.bot.TellmBot._registry_domain_check → tellm.registry.core.service_result
  tellm.bot.TellmBot._price_relevance_tokens → tellm.registry.core.ResourceRegistry.list
  tellm.bot.TellmBot._price_error_result → tellm.registry.core.service_result
  main.main → config.load_config
  tellm.registry.core.uri_domain → tellm.registry.core.uri_parts
  tellm.registry.core.uri_name → tellm.registry.core.uri_parts
  tellm.registry.core.validate_schema → tellm.registry.core._schema_types
  tellm.registry.core.normalize_issue_list → tellm.registry.core.json_like
  tellm.registry.core.service_result → tellm.registry.core.normalize_issue_list
  tellm.registry.core.RegistryEntry.__post_init__ → tellm.registry.core.normalize_schema
  tellm.registry.core.RegistryEntry.__post_init__ → tellm.registry.core.validate_tellm_uri
  tellm.registry.core.RegistryEntry.__post_init__ → tellm.registry.core.uri_domain
  tellm.registry.core.ResourceRegistry.register_alias → tellm.registry.core.uri_name
  tellm.registry.core.ResourceRegistry.manifest → tellm.registry.core.registry_manifest_schema
  tellm.registry.core.ResourceRegistry.manifest → tellm.registry.core.service_result_schema
  tellm.registry.core.ResourceRegistry.read → tellm.registry.core.validate_schema
  tellm.registry.core.ResourceRegistry.execute → tellm.registry.core.validate_schema
  tellm.registry.core.ResourceRegistry._call → tellm.registry.core.ResourceRegistry.list
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Integration (1)

**`Auto-generated from Python Tests`**

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/tellm
# generated in 0.02s
# nodes: 47 | edges: 39 | modules: 7
# CC̄=5.5

HUBS[20]:
  tellm.server.TellmServer._validate_and_repair
    CC=12  in:0  out:40  total:40
  tellm.registry.core.validate_schema
    CC=23  in:9  out:27  total:36
  tellm.registry.core.normalize_issue_list
    CC=11  in:2  out:20  total:22
  tellm.bot.TellmBot._registry_domain_check
    CC=14  in:0  out:22  total:22
  tellm.server.TellmServer._local_validation_verdict
    CC=23  in:0  out:17  total:17
  tellm.registry.core.service_result
    CC=6  in:8  out:7  total:15
  scripts.generate_test_audio.generate_fixture
    CC=2  in:1  out:13  total:14
  main.main
    CC=3  in:0  out:14  total:14
  scripts.protocol_smoke.send_ws_payload
    CC=4  in:2  out:10  total:12
  tellm.registry.core.RegistryEntry.__post_init__
    CC=17  in:0  out:12  total:12
  scripts.generate_test_audio.main
    CC=4  in:0  out:9  total:9
  config.load_config
    CC=1  in:3  out:6  total:9
  scripts.protocol_smoke.check_http
    CC=3  in:2  out:7  total:9
  tellm.registry.core.validate_tellm_uri
    CC=9  in:2  out:7  total:9
  tellm.registry.core.ResourceRegistry.execute
    CC=5  in:0  out:9  total:9
  scripts.protocol_smoke.check_ws_audio
    CC=4  in:1  out:8  total:9
  tellm.bot.TellmBot._price_relevance_tokens
    CC=6  in:0  out:9  total:9
  tellm.registry.core.ResourceRegistry._call
    CC=4  in:0  out:8  total:8
  scripts.protocol_smoke.check_ws_text
    CC=3  in:1  out:7  total:8
  tellm.registry.core.ResourceRegistry.list
    CC=4  in:3  out:4  total:7

MODULES:
  config  [1 funcs]
    load_config  CC=1  out:6
  main  [1 funcs]
    main  CC=3  out:14
  scripts.generate_test_audio  [4 funcs]
    generate_fixture  CC=2  out:13
    main  CC=4  out:9
    require_tool  CC=2  out:2
    run  CC=1  out:1
  scripts.protocol_smoke  [9 funcs]
    async_main  CC=7  out:3
    audio_data_url  CC=1  out:4
    check_http  CC=3  out:7
    check_ws_audio  CC=4  out:8
    check_ws_text  CC=3  out:7
    get_url  CC=3  out:4
    mime_for_audio  CC=3  out:1
    send_ws_payload  CC=4  out:10
    ws_ssl_context  CC=3  out:2
  tellm.bot  [6 funcs]
    __init__  CC=2  out:5
    _price_error_result  CC=3  out:2
    _price_relevance_tokens  CC=6  out:9
    _registry_domain_check  CC=14  out:22
    _registry_echo  CC=1  out:1
    _registry_now  CC=1  out:3
  tellm.registry.core  [19 funcs]
    __post_init__  CC=17  out:12
    _call  CC=4  out:8
    execute  CC=5  out:9
    list  CC=4  out:4
    manifest  CC=2  out:4
    read  CC=3  out:5
    register_alias  CC=11  out:2
    _schema_types  CC=4  out:3
    json_like  CC=2  out:2
    normalize_issue_list  CC=11  out:20
  tellm.server  [7 funcs]
    _local_validation_verdict  CC=23  out:17
    _validate_and_repair  CC=12  out:40
    _validate_payload  CC=4  out:6
    serve_forever  CC=1  out:5
    _asyncapi_document  CC=1  out:1
    _openapi_document  CC=1  out:2
    _websocket_logger  CC=1  out:4

EDGES:
  scripts.generate_test_audio.generate_fixture → scripts.generate_test_audio.run
  scripts.generate_test_audio.generate_fixture → scripts.generate_test_audio.require_tool
  scripts.generate_test_audio.main → scripts.generate_test_audio.generate_fixture
  scripts.protocol_smoke.check_http → scripts.protocol_smoke.get_url
  scripts.protocol_smoke.audio_data_url → scripts.protocol_smoke.mime_for_audio
  scripts.protocol_smoke.send_ws_payload → scripts.protocol_smoke.ws_ssl_context
  scripts.protocol_smoke.check_ws_text → scripts.protocol_smoke.send_ws_payload
  scripts.protocol_smoke.check_ws_audio → scripts.protocol_smoke.audio_data_url
  scripts.protocol_smoke.check_ws_audio → scripts.protocol_smoke.send_ws_payload
  scripts.protocol_smoke.async_main → scripts.protocol_smoke.check_ws_text
  scripts.protocol_smoke.async_main → scripts.protocol_smoke.check_ws_audio
  tellm.server._openapi_document → tellm.registry.core.registry_manifest_schema
  tellm.server._openapi_document → tellm.registry.core.service_result_schema
  tellm.server._asyncapi_document → tellm.registry.core.registry_manifest_schema
  tellm.server.TellmServer._validate_payload → tellm.registry.core.validate_schema
  tellm.server.TellmServer._local_validation_verdict → tellm.registry.core.validate_schema
  tellm.server.TellmServer._validate_and_repair → config.load_config
  tellm.server.TellmServer.serve_forever → tellm.server._websocket_logger
  tellm.bot.TellmBot.__init__ → config.load_config
  tellm.bot.TellmBot._registry_now → tellm.registry.core.service_result
  tellm.bot.TellmBot._registry_echo → tellm.registry.core.service_result
  tellm.bot.TellmBot._registry_domain_check → tellm.registry.core.service_result
  tellm.bot.TellmBot._price_relevance_tokens → tellm.registry.core.ResourceRegistry.list
  tellm.bot.TellmBot._price_error_result → tellm.registry.core.service_result
  main.main → config.load_config
  tellm.registry.core.uri_domain → tellm.registry.core.uri_parts
  tellm.registry.core.uri_name → tellm.registry.core.uri_parts
  tellm.registry.core.validate_schema → tellm.registry.core._schema_types
  tellm.registry.core.normalize_issue_list → tellm.registry.core.json_like
  tellm.registry.core.service_result → tellm.registry.core.normalize_issue_list
  tellm.registry.core.RegistryEntry.__post_init__ → tellm.registry.core.normalize_schema
  tellm.registry.core.RegistryEntry.__post_init__ → tellm.registry.core.validate_tellm_uri
  tellm.registry.core.RegistryEntry.__post_init__ → tellm.registry.core.uri_domain
  tellm.registry.core.ResourceRegistry.register_alias → tellm.registry.core.uri_name
  tellm.registry.core.ResourceRegistry.manifest → tellm.registry.core.registry_manifest_schema
  tellm.registry.core.ResourceRegistry.manifest → tellm.registry.core.service_result_schema
  tellm.registry.core.ResourceRegistry.read → tellm.registry.core.validate_schema
  tellm.registry.core.ResourceRegistry.execute → tellm.registry.core.validate_schema
  tellm.registry.core.ResourceRegistry._call → tellm.registry.core.ResourceRegistry.list
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 21f 9667L | python:13,yaml:5,shell:2,txt:1 | 2026-06-14
# generated in 0.01s
# CC̅=5.5 | critical:14/220 | dups:0 | cycles:2

HEALTH[16]:
  🔴 GOD   tellm/bot.py = 2899L, 6 classes, 90m, max CC=47
  🔴 GOD   tellm/registry/core.py = 974L, 5 classes, 39m, max CC=23
  🟡 CC    process_request CC=95 (limit:15)
  🟡 CC    _data_source_findings CC=21 (limit:15)
  🟡 CC    _local_validation_verdict CC=23 (limit:15)
  🟡 CC    _process_message CC=15 (limit:15)
  🟡 CC    resolve_resource_document CC=47 (limit:15)
  🟡 CC    _registry_weather_current CC=29 (limit:15)
  🟡 CC    _registry_price_search CC=30 (limit:15)
  🟡 CC    _parse_json_response CC=18 (limit:15)
  🟡 CC    _execute_python_process CC=22 (limit:15)
  🟡 CC    _schema_health CC=15 (limit:15)
  🟡 CC    _history_health CC=39 (limit:15)
  🟡 CC    validate_schema CC=23 (limit:15)
  🟡 CC    __post_init__ CC=17 (limit:15)
  🟡 CC    _resolve_internal CC=17 (limit:15)

REFACTOR[4]:
  1. split tellm/bot.py  (god module)
  2. split tellm/registry/core.py  (god module)
  3. split 14 high-CC methods  (CC>15)
  4. break 2 circular dependencies

PIPELINES[177]:
  [1] Src [create_bot]: create_bot
      PURITY: 100% pure
  [2] Src [run_server]: run_server
      PURITY: 100% pure
  [3] Src [__init__]: __init__
      PURITY: 100% pure
  [4] Src [now]: now
      PURITY: 100% pure
  [5] Src [init_db]: init_db
      PURITY: 100% pure
  [6] Src [record]: record
      PURITY: 100% pure
  [7] Src [_decode_row]: _decode_row
      PURITY: 100% pure
  [8] Src [recent]: recent
      PURITY: 100% pure
  [9] Src [count_since_id]: count_since_id
      PURITY: 100% pure
  [10] Src [latest_id]: latest_id
      PURITY: 100% pure
  [11] Src [main]: main → generate_fixture → run
      PURITY: 100% pure
  [12] Src [main]: main → check_http → get_url
      PURITY: 100% pure
  [13] Src [__init__]: __init__
      PURITY: 100% pure
  [14] Src [register_function]: register_function
      PURITY: 100% pure
  [15] Src [_http_response]: _http_response
      PURITY: 100% pure
  [16] Src [_json_response]: _json_response
      PURITY: 100% pure
  [17] Src [_resource_entry_response]: _resource_entry_response
      PURITY: 100% pure
  [18] Src [_registry_item_summary]: _registry_item_summary
      PURITY: 100% pure
  [19] Src [_virtual_schema_resource]: _virtual_schema_resource
      PURITY: 100% pure
  [20] Src [_virtual_view_resource]: _virtual_view_resource
      PURITY: 100% pure
  [21] Src [_describe_entry]: _describe_entry
      PURITY: 100% pure
  [22] Src [_validation_error]: _validation_error
      PURITY: 100% pure
  [23] Src [_validate_payload]: _validate_payload → validate_schema → _schema_types
      PURITY: 100% pure
  [24] Src [_payload_from_query]: _payload_from_query
      PURITY: 100% pure
  [25] Src [process_request]: process_request → _openapi_document → registry_manifest_schema
      PURITY: 100% pure
  [26] Src [_call_maybe_async]: _call_maybe_async
      PURITY: 100% pure
  [27] Src [_run_blocking]: _run_blocking
      PURITY: 100% pure
  [28] Src [_send_log]: _send_log
      PURITY: 100% pure
  [29] Src [_send_state]: _send_state
      PURITY: 100% pure
  [30] Src [_compact]: _compact
      PURITY: 100% pure
  [31] Src [_collect_source_values]: _collect_source_values
      PURITY: 100% pure
  [32] Src [_requires_real_world_data]: _requires_real_world_data
      PURITY: 100% pure
  [33] Src [_registry_entry_for_task]: _registry_entry_for_task
      PURITY: 100% pure
  [34] Src [_data_source_findings]: _data_source_findings
      PURITY: 100% pure
  [35] Src [_append_data_quality_warnings]: _append_data_quality_warnings
      PURITY: 100% pure
  [36] Src [_log_details]: _log_details
      PURITY: 100% pure
  [37] Src [_result_business_ok]: _result_business_ok
      PURITY: 100% pure
  [38] Src [_service_result_log]: _service_result_log
      PURITY: 100% pure
  [39] Src [_workflow_history_status]: _workflow_history_status
      PURITY: 100% pure
  [40] Src [_render_logs]: _render_logs
      PURITY: 100% pure
  [41] Src [_local_validation_verdict]: _local_validation_verdict → validate_schema → _schema_types
      PURITY: 100% pure
  [42] Src [_validate_and_repair]: _validate_and_repair → load_config
      PURITY: 100% pure
  [43] Src [_answer_from_service_result]: _answer_from_service_result
      PURITY: 100% pure
  [44] Src [_looks_executable_query]: _looks_executable_query
      PURITY: 100% pure
  [45] Src [_repair_count]: _repair_count
      PURITY: 100% pure
  [46] Src [_duration_ms]: _duration_ms
      PURITY: 100% pure
  [47] Src [_handle_transcription]: _handle_transcription
      PURITY: 100% pure
  [48] Src [_handle_resource_execution]: _handle_resource_execution
      PURITY: 100% pure
  [49] Src [_handle_test_transcription]: _handle_test_transcription
      PURITY: 100% pure
  [50] Src [_audio_payload]: _audio_payload
      PURITY: 100% pure

LAYERS:
  tellm/                          CC̄=5.8    ←in:0  →out:17  !! split
  │ !! server                    3509L  1C   50m  CC=95     ←0
  │ !! bot                       2899L  6C   90m  CC=47     ←0
  │ !! core                       974L  5C   39m  CC=23     ←3
  │ !! runner                     498L  1C   13m  CC=39     ←0
  │ history                    131L  1C    8m  CC=4      ←0
  │ aliases.yaml                35L  0C    0m  CC=0.0    ←0
  │ __init__                    31L  0C    0m  CC=0.0    ←0
  │ __init__                    20L  0C    2m  CC=1      ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=3.0    ←in:0  →out:0
  │ protocol_smoke             233L  0C   12m  CC=7      ←0
  │ generate_test_audio        109L  0C    4m  CC=4      ←0
  │
  ./                              CC̄=2.0    ←in:0  →out:0
  │ !! planfile.yaml              526L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  511L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ project.sh                  59L  0C    0m  CC=0.0    ←0
  │ setup                       18L  0C    0m  CC=0.0    ←0
  │ requirements.txt             5L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │ config                       0L  1C    1m  CC=1      ←3
  │ main                         0L  0C    1m  CC=3      ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-from-pytests.testql.toon.yaml    10L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     config.py                                 0L
     main.py                                   0L

COUPLING:
                        tellm.registry              tellm             config  tellm.improvement               main
     tellm.registry                 ──                ←15                                    ←3                     hub
              tellm                 15                 ──                  2                                        !! fan-out
             config                                    ←2                 ──                                    ←1
  tellm.improvement                  3                                                       ──                   
               main                                                        1                                    ──
  CYCLES: 2
  HUB: tellm.registry/ (fan-in=18)
  SMELL: tellm/ fan-out=17 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 1 groups | 12f 8345L | 2026-06-14

SUMMARY:
  files_scanned: 12
  total_lines:   8345
  dup_groups:    1
  dup_fragments: 2
  saved_lines:   457
  scan_ms:       2495

HOTSPOTS[1] (files with most duplication):
  tellm/server.py  dup=571L  groups=1  frags=2  (6.8%)

DUPLICATES[1] (ranked by impact):
  [f8b3673c2f6f19bf] !! STRU  _docs_html  L=457 N=2 saved=457 sim=1.00
      tellm/server.py:787-1243  (_docs_html)
      tellm/server.py:1297-1410  (_autoimprovement_html)

REFACTOR[1] (ranked by priority):
  [1] ○ extract_module     → tellm/utils/_docs_html.py
      WHY: 2 occurrences of 457-line block across 1 files — saves 457 lines
      FILES: tellm/server.py

QUICK_WINS[1] (low risk, high savings — do first):
  [1] extract_module     saved=457L  → tellm/utils/_docs_html.py
      FILES: server.py

EFFORT_ESTIMATE (total ≈ 22.9h):
  hard   _docs_html                          saved=457L  ~1371min

METRICS-TARGET:
  dup_groups:  1 → 0
  saved_lines: 457 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 204 func | 8f | 2026-06-14
# generated in 0.00s

NEXT[10] (ranked by impact):
  [1] !! SPLIT           tellm/server.py
      WHY: 3509L, 1 classes, max CC=95
      EFFORT: ~4h  IMPACT: 333355

  [2] !! SPLIT           tellm/bot.py
      WHY: 2899L, 6 classes, max CC=47
      EFFORT: ~4h  IMPACT: 136253

  [3] !! SPLIT           tellm/registry/core.py
      WHY: 974L, 5 classes, max CC=23
      EFFORT: ~4h  IMPACT: 22402

  [4] !! SPLIT-FUNC      TellmServer.process_request  CC=95  fan=50
      WHY: CC=95 exceeds 15
      EFFORT: ~1h  IMPACT: 4750

  [5] !! SPLIT-FUNC      TellmBot.resolve_resource_document  CC=47  fan=24
      WHY: CC=47 exceeds 15
      EFFORT: ~1h  IMPACT: 1128

  [6] !! SPLIT-FUNC      AutoimprovementRunner._history_health  CC=39  fan=25
      WHY: CC=39 exceeds 15
      EFFORT: ~1h  IMPACT: 975

  [7] !! SPLIT-FUNC      TellmBot._registry_weather_current  CC=29  fan=28
      WHY: CC=29 exceeds 15
      EFFORT: ~1h  IMPACT: 812

  [8] !! SPLIT-FUNC      TellmBot._registry_price_search  CC=30  fan=22
      WHY: CC=30 exceeds 15
      EFFORT: ~1h  IMPACT: 660

  [9] !  SPLIT-FUNC      TellmServer._data_source_findings  CC=21  fan=17
      WHY: CC=21 exceeds 15
      EFFORT: ~1h  IMPACT: 357

  [10] !  SPLIT-FUNC      TellmBot._execute_python_process  CC=22  fan=16
      WHY: CC=22 exceeds 15
      EFFORT: ~1h  IMPACT: 352


RISKS[3]:
  ⚠ Splitting tellm/server.py may break 50 import paths
  ⚠ Splitting tellm/bot.py may break 90 import paths
  ⚠ Splitting tellm/registry/core.py may break 39 import paths

METRICS-TARGET:
  CC̄:          5.7 → ≤4.0
  max-CC:      95 → ≤20
  god-modules: 5 → 0
  high-CC(≥15): 14 → ≤7
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=5.0 → now CC̄=5.7
```

## Intent

tellm v4 - STT+TTS+LLM+SQLite+HTML
