# tellm v4 - STT+TTS+LLM+SQLite+HTML

tellm v4 - STT+TTS+LLM+SQLite+HTML

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Code Analysis](#code-analysis)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `tellm`
- **version**: `0.0.0`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: requirements.txt, testql(1), app.doql.less, goal.yaml, .env.example, src(4 mod), project/(3 analysis files)

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

## Interfaces

### testql Scenarios

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

CONFIG[2]{key, value}:
  base_url, ${api_url:-http://localhost:8101}
  timeout_ms, 10000

# NOTE: Python pytest files were detected but no convertible HTTP calls or assertions were found.
# To run pytest tests directly, use: pytest <test_file>
```

## Configuration

```yaml
project:
  name: tellm
  version: 0.0.0
  env: local
```

## Deployment

```bash markpact:run
pip install tellm

# development install
pip install -e .[dev]
```

### Requirements Files

#### `requirements.txt`

- `litellm>=1.0.0`
- `websockets>=12.0`
- `python-dotenv>=1.0.0`
- `pyttsx3>=2.90`
- `faster-whisper>=0.11.0`

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `twoj_key` |  |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` |  |
| `HOST` | `localhost` |  |
| `PORT` | `8000` |  |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`tellm`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `setup.py:version`, `tellm/__init__.py:__version__`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# tellm | 17f 10771L | python:14,shell:2,less:1 | 2026-06-14
# stats: 87 func | 15 cls | 17 mod | CC̄=7.7 | critical:13 | cycles:0
# alerts[5]: CC test_server_registry_http_endpoints=138; CC test_server_docs_describe_text_and_speech_api=59; CC test_registry_manifest_uses_tellm_standards=55; CC test_server_handles_plain_http_request=24; CC validate_schema=23
# hotspots[5]: test_server_accepts_text_websocket_messages fan=21; test_server_validation_can_repair_render_data fan=19; test_server_blocks_parallel_query_and_accepts_cancel fan=19; test_server_registry_http_endpoints fan=18; test_server_returns_saved_view_by_id fan=18
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[17]:
  app.doql.less,27
  project.sh,59
  scripts/generate_test_audio.py,110
  scripts/protocol_smoke.py,234
  setup.py,19
  tellm/__init__.py,21
  tellm/bot.py,2900
  tellm/config.py,12
  tellm/improvement/__init__.py,5
  tellm/improvement/history.py,132
  tellm/improvement/runner.py,499
  tellm/main.py,16
  tellm/registry/__init__.py,32
  tellm/registry/core.py,975
  tellm/server.py,3510
  tests/test_tellm.py,2218
  tree.sh,2
D:
  scripts/generate_test_audio.py:
    e: run,require_tool,generate_fixture,main
    run(cmd)
    require_tool(name)
    generate_fixture(output_dir;fixture)
    main()
  scripts/protocol_smoke.py:
    e: ws_url_from_http,get_url,check_http,mime_for_audio,audio_data_url,ws_ssl_context,send_ws_payload,check_ws_text,check_ws_audio,write_webrtc_html,async_main,main
    ws_url_from_http(base_url)
    get_url(url;insecure)
    check_http(base_url;insecure)
    mime_for_audio(path)
    audio_data_url(path)
    ws_ssl_context(ws_url;insecure)
    send_ws_payload(ws_url;payload;timeout;insecure)
    check_ws_text(ws_url;text;timeout;insecure)
    check_ws_audio(ws_url;audio_path;transcription;real_stt;timeout;insecure)
    write_webrtc_html(path;ws_url;transcription)
    async_main(args)
    main()
  setup.py:
  tellm/__init__.py:
    e: create_bot,run_server
    create_bot(db_path)
    run_server(host;port;db_path)
  tellm/bot.py:
    e: TaskType,WeatherLocationResolutionError,WeatherLocationTooBroadError,Task,ViewData,TellmBot
    TaskType:
    WeatherLocationResolutionError: __init__(4)
    WeatherLocationTooBroadError: __init__(3)
    Task:
    ViewData: to_dict(0),_safe_json(1),_safe_text(1),_render_items(1),_render_table(1),_render_block(1),_render_dynamic(0),to_html(0)
    TellmBot: __init__(2),_init_db(0),record_execution(8),save_autoimprovement_report(2),update_autoimprovement_report_html(3),get_latest_autoimprovement_report(0),get_latest_autoimprovement_html(0),save_task(3),save_evolution(2),save_view(1),get_view_html(1),get_view_record(1),_is_text_content_type(1),_storage_base_path(1),_value_preview(1),resolve_resource_document(4),resolve_resource(4),get_tasks(1),register_function(2),_package_version(1),_register_file_resource(6),_register_package_resource(4),_register_artifact_resources(0),_register_uri_aliases(0),_init_registry(0),_registry_now(1),_registry_echo(1),_registry_autoimprove(1),_weather_code_description(1),_http_json(2),_http_text(2),_normalize_country_code(1),_is_country_level_weather_location(2),_score_geocode_result(3),_geocode_city(2),_registry_weather_current(1),_normalize_domain(1),_registry_domain_check(1),_normalize_price_site(1),_commerce_search_url(2),_text_from_html(1),_parse_price_amount(1),_price_relevance_tokens(1),_price_relevance(2),_extract_price_candidates(5),_price_error_result(11),_registry_price_search(1),execute_resource(2),_completion(1),_message_text(1),_parse_json_response(1),_normalize_processes(1),_ensure_function_state(1),_restricted_import(5),_process_globals(0),_execute_registered_function(2),_execute_python_process(2),execute_processes(1),_get_stt_model(0),_get_tts(0),_looks_like_weather_query(1),_normalize_weather_location(1),_weather_location_from_query(2),_route_weather_task(2),_local_weather_task_from_query(1),_looks_like_price_query(1),_price_site_from_query(2),_normalize_price_product(1),_price_query_from_query(2),_route_price_task(2),_local_price_task_from_query(1),_local_task_from_query(1),analyze_query(1),evolve_function(1),execute_task(1),transcribe(2),speak(1),_render_autoimprovement_data(2),_render_data_from_service_result(1),generate_view(3)
  tellm/config.py:
    e: load_config,Config
    Config:
    load_config()
  tellm/improvement/__init__.py:
  tellm/improvement/history.py:
    e: ExecutionHistoryStore
    ExecutionHistoryStore: __init__(1),now(0),init_db(0),record(8),_decode_row(1),recent(2),count_since_id(1),latest_id(0)
  tellm/improvement/runner.py:
    e: AutoimprovementRunner
    AutoimprovementRunner: __init__(2),now(0),_finding(6),_collect_source_values(1),_collect_error_objects(1),_looks_like_weather_identifier(2),_looks_like_ad_hoc_weather_function(2),_schema_health(1),_history_health(3),_patches_from_findings(2),_suggested_actions(1),registry_health(0),run(1)
  tellm/main.py:
    e: main
    main()
  tellm/registry/__init__.py:
  tellm/registry/core.py:
    e: validate_tellm_uri,uri_parts,uri_domain,uri_name,normalize_schema,_schema_types,_matches_type,validate_schema,_issue_code_from_text,normalize_issue_list,json_like,service_result,service_result_schema,registry_manifest_schema,RegistryError,RegistryPermissionError,RegistryValidationError,RegistryEntry,ResourceRegistry
    RegistryError:
    RegistryPermissionError:
    RegistryValidationError:
    RegistryEntry: __post_init__(0),_transport_manifest(0),to_dict(1)
    ResourceRegistry: __init__(0),register(1),register_alias(9),register_value(36),register_callable(33),get(1),get_canonical(1),require(1),list(1),find(5),find_capability(2),discover_for_llm(0),manifest(0),check_permission(3),_apply_alias_input(2),_resolve_internal(3),canonicalize(1),resolve_uri(2),resolve(1),read(1),execute(3),_call(2)
    validate_tellm_uri(uri;expected_kind)
    uri_parts(uri)
    uri_domain(uri)
    uri_name(uri)
    normalize_schema(schema;schema_id)
    _schema_types(schema_type)
    _matches_type(value;schema_type)
    validate_schema(schema;value;path)
    _issue_code_from_text(detail;default_code)
    normalize_issue_list(issues;default_source;default_code;recoverable)
    json_like(value)
    service_result(ok;result_type;data;title;summary;details;errors;view;uri;warnings;meta;render)
    service_result_schema()
    registry_manifest_schema()
  tellm/server.py:
    e: _websocket_logger,_browser_client_html,_docs_html,_registry_ui_html,_autoimprovement_html,_openapi_document,_asyncapi_document,TellmServer
    TellmServer: __init__(3),register_function(2),_http_response(3),_json_response(2),_resource_entry_response(1),_registry_item_summary(1),_virtual_schema_resource(1),_virtual_view_resource(1),_schema_bundle(1),_describe_entry(1),_validation_error(1),_validate_payload(3),_payload_from_query(2),process_request(2),_call_maybe_async(1),_run_blocking(1),_send_log(5),_send_state(3),_compact(2),_collect_source_values(1),_requires_real_world_data(2),_registry_entry_for_task(1),_data_source_findings(3),_append_data_quality_warnings(2),_log_details(2),_result_business_ok(1),_service_result_log(2),_workflow_history_status(3),_render_logs(6),_local_validation_verdict(4),_validate_and_repair(8),_answer_from_service_result(1),_looks_executable_query(1),_repair_count(1),_duration_ms(1),_handle_transcription(4),_handle_resource_execution(5),_handle_test_transcription(4),_audio_payload(1),_process_message(2),handle(2),serve_forever(0),run(0)
    _websocket_logger()
    _browser_client_html(host)
    _docs_html(host)
    _registry_ui_html(bot;host)
    _autoimprovement_html(host)
    _openapi_document(host)
    _asyncapi_document(host)
  tests/test_tellm.py:
    e: test_import,test_sqlite_save_and_get_tasks,test_view_html_escapes_user_content,test_view_html_renders_dynamic_json_structure,test_execute_task_supports_sync_functions,test_registry_executes_typed_local_resource,test_registry_manifest_uses_tellm_standards,test_registry_masks_env_and_exposes_discovery,test_weather_service_fetches_open_meteo_data,test_weather_service_normalizes_country_and_falls_back_geocoding,test_weather_service_returns_location_not_found_diagnostics,test_weather_service_rejects_country_level_location,test_weather_service_returns_standard_error_when_network_denied,test_price_service_extracts_visible_prices_from_supported_source,test_price_service_rejects_prices_unrelated_to_requested_product,test_price_service_returns_structured_not_found_error,test_autoimprove_service_returns_and_saves_schema_valid_report,test_autoimprove_finds_missing_schema,test_autoimprove_finds_repeated_service_failures,test_autoimprove_finds_direct_llm_answer_violation,test_autoimprove_finds_simulated_data_for_real_world_query,test_autoimprove_finds_missing_weather_provider_and_ad_hoc_function,test_autoimprove_finds_provider_location_resolution_failure,test_autoimprovement_report_renders_as_html,test_analyze_query_reads_llm_json_view_and_processes,test_analyze_query_routes_weather_to_registry_service,test_analyze_query_routes_price_to_registry_service,test_analyze_query_can_still_rewrite_ad_hoc_weather_llm_response,test_analyze_query_reads_json_from_reasoning_when_content_is_empty,test_execute_task_runs_python_process,test_server_starts_inside_running_event_loop,test_server_handles_plain_http_request,test_server_docs_describe_text_and_speech_api,test_server_registry_http_endpoints,test_server_registry_ui_and_autoimprovement_pages,test_server_returns_saved_view_by_id,test_server_audio_payload_reads_data_url_suffix,test_server_validation_can_repair_render_data,test_server_local_validation_skips_llm_for_trusted_registry_result,test_server_local_validation_skips_llm_for_structured_service_error,test_server_flags_simulated_weather_source,test_server_logs_execution_and_service_result_separately,test_server_blocks_parallel_query_and_accepts_cancel,test_server_test_mode_returns_echo_without_llm,test_server_executes_registry_uri_over_websocket,test_server_accepts_text_websocket_messages
    test_import()
    test_sqlite_save_and_get_tasks(tmp_path)
    test_view_html_escapes_user_content()
    test_view_html_renders_dynamic_json_structure()
    test_execute_task_supports_sync_functions(tmp_path)
    test_registry_executes_typed_local_resource(tmp_path)
    test_registry_manifest_uses_tellm_standards(tmp_path)
    test_registry_masks_env_and_exposes_discovery(tmp_path;monkeypatch)
    test_weather_service_fetches_open_meteo_data(tmp_path;monkeypatch)
    test_weather_service_normalizes_country_and_falls_back_geocoding(tmp_path;monkeypatch)
    test_weather_service_returns_location_not_found_diagnostics(tmp_path;monkeypatch)
    test_weather_service_rejects_country_level_location(tmp_path;monkeypatch)
    test_weather_service_returns_standard_error_when_network_denied(tmp_path;monkeypatch)
    test_price_service_extracts_visible_prices_from_supported_source(tmp_path;monkeypatch)
    test_price_service_rejects_prices_unrelated_to_requested_product(tmp_path;monkeypatch)
    test_price_service_returns_structured_not_found_error(tmp_path;monkeypatch)
    test_autoimprove_service_returns_and_saves_schema_valid_report(tmp_path)
    test_autoimprove_finds_missing_schema(tmp_path)
    test_autoimprove_finds_repeated_service_failures(tmp_path)
    test_autoimprove_finds_direct_llm_answer_violation(tmp_path)
    test_autoimprove_finds_simulated_data_for_real_world_query(tmp_path)
    test_autoimprove_finds_missing_weather_provider_and_ad_hoc_function(tmp_path)
    test_autoimprove_finds_provider_location_resolution_failure(tmp_path)
    test_autoimprovement_report_renders_as_html(tmp_path)
    test_analyze_query_reads_llm_json_view_and_processes(tmp_path;monkeypatch)
    test_analyze_query_routes_weather_to_registry_service(tmp_path;monkeypatch)
    test_analyze_query_routes_price_to_registry_service(tmp_path;monkeypatch)
    test_analyze_query_can_still_rewrite_ad_hoc_weather_llm_response(tmp_path;monkeypatch)
    test_analyze_query_reads_json_from_reasoning_when_content_is_empty(tmp_path;monkeypatch)
    test_execute_task_runs_python_process(tmp_path)
    test_server_starts_inside_running_event_loop(tmp_path)
    test_server_handles_plain_http_request(tmp_path)
    test_server_docs_describe_text_and_speech_api(tmp_path)
    test_server_registry_http_endpoints(tmp_path)
    test_server_registry_ui_and_autoimprovement_pages(tmp_path)
    test_server_returns_saved_view_by_id(tmp_path)
    test_server_audio_payload_reads_data_url_suffix(tmp_path)
    test_server_validation_can_repair_render_data(tmp_path;monkeypatch)
    test_server_local_validation_skips_llm_for_trusted_registry_result(tmp_path;monkeypatch)
    test_server_local_validation_skips_llm_for_structured_service_error(tmp_path;monkeypatch)
    test_server_flags_simulated_weather_source(tmp_path)
    test_server_logs_execution_and_service_result_separately(tmp_path)
    test_server_blocks_parallel_query_and_accepts_cancel(tmp_path;monkeypatch)
    test_server_test_mode_returns_echo_without_llm(tmp_path)
    test_server_executes_registry_uri_over_websocket(tmp_path;monkeypatch)
    test_server_accepts_text_websocket_messages(tmp_path;monkeypatch)
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('tellm', '0.0.0', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 27, 'less').
project_file('project.sh', 59, 'shell').
project_file('scripts/generate_test_audio.py', 110, 'python').
project_file('scripts/protocol_smoke.py', 234, 'python').
project_file('setup.py', 19, 'python').
project_file('tellm/__init__.py', 21, 'python').
project_file('tellm/bot.py', 2900, 'python').
project_file('tellm/config.py', 12, 'python').
project_file('tellm/improvement/__init__.py', 5, 'python').
project_file('tellm/improvement/history.py', 132, 'python').
project_file('tellm/improvement/runner.py', 499, 'python').
project_file('tellm/main.py', 16, 'python').
project_file('tellm/registry/__init__.py', 32, 'python').
project_file('tellm/registry/core.py', 975, 'python').
project_file('tellm/server.py', 3510, 'python').
project_file('tests/test_tellm.py', 2218, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('scripts/generate_test_audio.py', 'run', 1, 1, 1).
python_function('scripts/generate_test_audio.py', 'require_tool', 1, 2, 2).
python_function('scripts/generate_test_audio.py', 'generate_fixture', 2, 2, 6).
python_function('scripts/generate_test_audio.py', 'main', 0, 4, 8).
python_function('scripts/protocol_smoke.py', 'ws_url_from_http', 1, 2, 1).
python_function('scripts/protocol_smoke.py', 'get_url', 2, 3, 4).
python_function('scripts/protocol_smoke.py', 'check_http', 2, 3, 7).
python_function('scripts/protocol_smoke.py', 'mime_for_audio', 1, 3, 1).
python_function('scripts/protocol_smoke.py', 'audio_data_url', 1, 1, 4).
python_function('scripts/protocol_smoke.py', 'ws_ssl_context', 2, 3, 2).
python_function('scripts/protocol_smoke.py', 'send_ws_payload', 4, 4, 9).
python_function('scripts/protocol_smoke.py', 'check_ws_text', 4, 3, 4).
python_function('scripts/protocol_smoke.py', 'check_ws_audio', 6, 4, 5).
python_function('scripts/protocol_smoke.py', 'write_webrtc_html', 3, 1, 2).
python_function('scripts/protocol_smoke.py', 'async_main', 1, 7, 3).
python_function('scripts/protocol_smoke.py', 'main', 0, 5, 10).
python_function('tellm/__init__.py', 'create_bot', 1, 1, 1).
python_function('tellm/__init__.py', 'run_server', 3, 1, 2).
python_function('tellm/config.py', 'load_config', 0, 1, 3).
python_function('tellm/main.py', 'main', 0, 3, 8).
python_function('tellm/registry/core.py', 'validate_tellm_uri', 2, 9, 3).
python_function('tellm/registry/core.py', 'uri_parts', 1, 3, 2).
python_function('tellm/registry/core.py', 'uri_domain', 1, 2, 1).
python_function('tellm/registry/core.py', 'uri_name', 1, 2, 1).
python_function('tellm/registry/core.py', 'normalize_schema', 2, 4, 3).
python_function('tellm/registry/core.py', '_schema_types', 1, 4, 2).
python_function('tellm/registry/core.py', '_matches_type', 2, 11, 1).
python_function('tellm/registry/core.py', 'validate_schema', 3, 23, 14).
python_function('tellm/registry/core.py', '_issue_code_from_text', 2, 10, 1).
python_function('tellm/registry/core.py', 'normalize_issue_list', 4, 11, 8).
python_function('tellm/registry/core.py', 'json_like', 1, 2, 2).
python_function('tellm/registry/core.py', 'service_result', 12, 6, 4).
python_function('tellm/registry/core.py', 'service_result_schema', 0, 1, 0).
python_function('tellm/registry/core.py', 'registry_manifest_schema', 0, 1, 1).
python_function('tellm/server.py', '_websocket_logger', 0, 1, 4).
python_function('tellm/server.py', '_browser_client_html', 1, 1, 0).
python_function('tellm/server.py', '_docs_html', 1, 1, 1).
python_function('tellm/server.py', '_registry_ui_html', 2, 6, 7).
python_function('tellm/server.py', '_autoimprovement_html', 1, 1, 1).
python_function('tellm/server.py', '_openapi_document', 1, 1, 2).
python_function('tellm/server.py', '_asyncapi_document', 1, 1, 1).
python_function('tests/test_tellm.py', 'test_import', 0, 3, 1).
python_function('tests/test_tellm.py', 'test_sqlite_save_and_get_tasks', 1, 4, 7).
python_function('tests/test_tellm.py', 'test_view_html_escapes_user_content', 0, 5, 3).
python_function('tests/test_tellm.py', 'test_view_html_renders_dynamic_json_structure', 0, 7, 3).
python_function('tests/test_tellm.py', 'test_execute_task_supports_sync_functions', 1, 2, 6).
python_function('tests/test_tellm.py', 'test_registry_executes_typed_local_resource', 1, 5, 5).
python_function('tests/test_tellm.py', 'test_registry_manifest_uses_tellm_standards', 1, 55, 14).
python_function('tests/test_tellm.py', 'test_registry_masks_env_and_exposes_discovery', 2, 4, 7).
python_function('tests/test_tellm.py', 'test_weather_service_fetches_open_meteo_data', 2, 11, 6).
python_function('tests/test_tellm.py', 'test_weather_service_normalizes_country_and_falls_back_geocoding', 2, 8, 11).
python_function('tests/test_tellm.py', 'test_weather_service_returns_location_not_found_diagnostics', 2, 8, 7).
python_function('tests/test_tellm.py', 'test_weather_service_rejects_country_level_location', 2, 7, 6).
python_function('tests/test_tellm.py', 'test_weather_service_returns_standard_error_when_network_denied', 2, 10, 6).
python_function('tests/test_tellm.py', 'test_price_service_extracts_visible_prices_from_supported_source', 2, 10, 6).
python_function('tests/test_tellm.py', 'test_price_service_rejects_prices_unrelated_to_requested_product', 2, 7, 5).
python_function('tests/test_tellm.py', 'test_price_service_returns_structured_not_found_error', 2, 7, 5).
python_function('tests/test_tellm.py', 'test_autoimprove_service_returns_and_saves_schema_valid_report', 1, 10, 7).
python_function('tests/test_tellm.py', 'test_autoimprove_finds_missing_schema', 1, 4, 6).
python_function('tests/test_tellm.py', 'test_autoimprove_finds_repeated_service_failures', 1, 4, 7).
python_function('tests/test_tellm.py', 'test_autoimprove_finds_direct_llm_answer_violation', 1, 3, 6).
python_function('tests/test_tellm.py', 'test_autoimprove_finds_simulated_data_for_real_world_query', 1, 3, 6).
python_function('tests/test_tellm.py', 'test_autoimprove_finds_missing_weather_provider_and_ad_hoc_function', 1, 6, 5).
python_function('tests/test_tellm.py', 'test_autoimprove_finds_provider_location_resolution_failure', 1, 4, 5).
python_function('tests/test_tellm.py', 'test_autoimprovement_report_renders_as_html', 1, 4, 7).
python_function('tests/test_tellm.py', 'test_analyze_query_reads_llm_json_view_and_processes', 2, 6, 9).
python_function('tests/test_tellm.py', 'test_analyze_query_routes_weather_to_registry_service', 2, 6, 6).
python_function('tests/test_tellm.py', 'test_analyze_query_routes_price_to_registry_service', 2, 6, 6).
python_function('tests/test_tellm.py', 'test_analyze_query_can_still_rewrite_ad_hoc_weather_llm_response', 2, 5, 9).
python_function('tests/test_tellm.py', 'test_analyze_query_reads_json_from_reasoning_when_content_is_empty', 2, 4, 8).
python_function('tests/test_tellm.py', 'test_execute_task_runs_python_process', 1, 2, 5).
python_function('tests/test_tellm.py', 'test_server_starts_inside_running_event_loop', 1, 1, 7).
python_function('tests/test_tellm.py', 'test_server_handles_plain_http_request', 1, 24, 14).
python_function('tests/test_tellm.py', 'test_server_docs_describe_text_and_speech_api', 1, 59, 14).
python_function('tests/test_tellm.py', 'test_server_registry_http_endpoints', 1, 138, 18).
python_function('tests/test_tellm.py', 'test_server_registry_ui_and_autoimprovement_pages', 1, 10, 16).
python_function('tests/test_tellm.py', 'test_server_returns_saved_view_by_id', 1, 4, 18).
python_function('tests/test_tellm.py', 'test_server_audio_payload_reads_data_url_suffix', 1, 3, 5).
python_function('tests/test_tellm.py', 'test_server_validation_can_repair_render_data', 2, 5, 19).
python_function('tests/test_tellm.py', 'test_server_local_validation_skips_llm_for_trusted_registry_result', 2, 6, 14).
python_function('tests/test_tellm.py', 'test_server_local_validation_skips_llm_for_structured_service_error', 2, 6, 14).
python_function('tests/test_tellm.py', 'test_server_flags_simulated_weather_source', 1, 5, 9).
python_function('tests/test_tellm.py', 'test_server_logs_execution_and_service_result_separately', 1, 5, 8).
python_function('tests/test_tellm.py', 'test_server_blocks_parallel_query_and_accepts_cancel', 2, 7, 19).
python_function('tests/test_tellm.py', 'test_server_test_mode_returns_echo_without_llm', 1, 6, 16).
python_function('tests/test_tellm.py', 'test_server_executes_registry_uri_over_websocket', 2, 6, 18).
python_function('tests/test_tellm.py', 'test_server_accepts_text_websocket_messages', 2, 8, 21).

% ── Python Classes ───────────────────────────────────────
python_class('tellm/bot.py', 'TaskType').
python_class('tellm/bot.py', 'WeatherLocationResolutionError').
python_method('WeatherLocationResolutionError', '__init__', 4, 2, 2).
python_class('tellm/bot.py', 'WeatherLocationTooBroadError').
python_method('WeatherLocationTooBroadError', '__init__', 3, 2, 2).
python_class('tellm/bot.py', 'Task').
python_class('tellm/bot.py', 'ViewData').
python_method('ViewData', 'to_dict', 0, 1, 0).
python_method('ViewData', '_safe_json', 1, 1, 2).
python_method('ViewData', '_safe_text', 1, 2, 2).
python_method('ViewData', '_render_items', 1, 5, 4).
python_method('ViewData', '_render_table', 1, 11, 5).
python_method('ViewData', '_render_block', 1, 11, 11).
python_method('ViewData', '_render_dynamic', 0, 6, 5).
python_method('ViewData', 'to_html', 0, 5, 5).
python_class('tellm/bot.py', 'TellmBot').
python_method('TellmBot', '__init__', 2, 2, 5).
python_method('TellmBot', '_init_db', 0, 1, 5).
python_method('TellmBot', 'record_execution', 8, 3, 1).
python_method('TellmBot', 'save_autoimprovement_report', 2, 5, 13).
python_method('TellmBot', 'update_autoimprovement_report_html', 3, 1, 6).
python_method('TellmBot', 'get_latest_autoimprovement_report', 0, 2, 6).
python_method('TellmBot', 'get_latest_autoimprovement_html', 0, 3, 5).
python_method('TellmBot', 'save_task', 3, 1, 6).
python_method('TellmBot', 'save_evolution', 2, 1, 5).
python_method('TellmBot', 'save_view', 1, 1, 8).
python_method('TellmBot', 'get_view_html', 1, 2, 5).
python_method('TellmBot', 'get_view_record', 1, 4, 6).
python_method('TellmBot', '_is_text_content_type', 1, 3, 3).
python_method('TellmBot', '_storage_base_path', 1, 2, 6).
python_method('TellmBot', '_value_preview', 1, 5, 6).
python_method('TellmBot', 'resolve_resource_document', 4, 47, 17).
python_method('TellmBot', 'resolve_resource', 4, 2, 2).
python_method('TellmBot', 'get_tasks', 1, 2, 6).
python_method('TellmBot', 'register_function', 2, 1, 1).
python_method('TellmBot', '_package_version', 1, 2, 1).
python_method('TellmBot', '_register_file_resource', 6, 1, 1).
python_method('TellmBot', '_register_package_resource', 4, 1, 2).
python_method('TellmBot', '_register_artifact_resources', 0, 3, 4).
python_method('TellmBot', '_register_uri_aliases', 0, 1, 2).
python_method('TellmBot', '_init_registry', 0, 3, 13).
python_method('TellmBot', '_registry_now', 1, 1, 3).
python_method('TellmBot', '_registry_echo', 1, 1, 1).
python_method('TellmBot', '_registry_autoimprove', 1, 2, 5).
python_method('TellmBot', '_weather_code_description', 1, 2, 2).
python_method('TellmBot', '_http_json', 2, 1, 5).
python_method('TellmBot', '_http_text', 2, 2, 5).
python_method('TellmBot', '_normalize_country_code', 1, 4, 6).
python_method('TellmBot', '_is_country_level_weather_location', 2, 5, 8).
python_method('TellmBot', '_score_geocode_result', 3, 6, 6).
python_method('TellmBot', '_geocode_city', 2, 5, 18).
python_method('TellmBot', '_registry_weather_current', 1, 29, 23).
python_method('TellmBot', '_normalize_domain', 1, 2, 4).
python_method('TellmBot', '_registry_domain_check', 1, 14, 12).
python_method('TellmBot', '_normalize_price_site', 1, 3, 3).
python_method('TellmBot', '_commerce_search_url', 2, 3, 2).
python_method('TellmBot', '_text_from_html', 1, 1, 4).
python_method('TellmBot', '_parse_price_amount', 1, 6, 4).
python_method('TellmBot', '_price_relevance_tokens', 1, 6, 9).
python_method('TellmBot', '_price_relevance', 2, 5, 3).
python_method('TellmBot', '_extract_price_candidates', 5, 7, 18).
python_method('TellmBot', '_price_error_result', 11, 3, 2).
python_method('TellmBot', '_registry_price_search', 1, 30, 21).
python_method('TellmBot', 'execute_resource', 2, 9, 8).
python_method('TellmBot', '_completion', 1, 1, 1).
python_method('TellmBot', '_message_text', 1, 14, 6).
python_method('TellmBot', '_parse_json_response', 1, 18, 17).
python_method('TellmBot', '_normalize_processes', 1, 5, 1).
python_method('TellmBot', '_ensure_function_state', 1, 1, 1).
python_method('TellmBot', '_restricted_import', 5, 2, 3).
python_method('TellmBot', '_process_globals', 0, 1, 1).
python_method('TellmBot', '_execute_registered_function', 2, 2, 1).
python_method('TellmBot', '_execute_python_process', 2, 22, 15).
python_method('TellmBot', 'execute_processes', 1, 7, 5).
python_method('TellmBot', '_get_stt_model', 0, 2, 1).
python_method('TellmBot', '_get_tts', 0, 2, 2).
python_method('TellmBot', '_looks_like_weather_query', 1, 2, 2).
python_method('TellmBot', '_normalize_weather_location', 1, 6, 8).
python_method('TellmBot', '_weather_location_from_query', 2, 5, 6).
python_method('TellmBot', '_route_weather_task', 2, 7, 9).
python_method('TellmBot', '_local_weather_task_from_query', 1, 3, 3).
python_method('TellmBot', '_looks_like_price_query', 1, 2, 2).
python_method('TellmBot', '_price_site_from_query', 2, 4, 5).
python_method('TellmBot', '_normalize_price_product', 1, 2, 5).
python_method('TellmBot', '_price_query_from_query', 2, 5, 4).
python_method('TellmBot', '_route_price_task', 2, 6, 7).
python_method('TellmBot', '_local_price_task_from_query', 1, 4, 4).
python_method('TellmBot', '_local_task_from_query', 1, 3, 1).
python_method('TellmBot', 'analyze_query', 1, 13, 15).
python_method('TellmBot', 'evolve_function', 1, 4, 8).
python_method('TellmBot', 'execute_task', 1, 8, 5).
python_method('TellmBot', 'transcribe', 2, 5, 9).
python_method('TellmBot', 'speak', 1, 1, 3).
python_method('TellmBot', '_render_autoimprovement_data', 2, 10, 5).
python_method('TellmBot', '_render_data_from_service_result', 1, 13, 5).
python_method('TellmBot', 'generate_view', 3, 4, 6).
python_class('tellm/config.py', 'Config').
python_class('tellm/improvement/history.py', 'ExecutionHistoryStore').
python_method('ExecutionHistoryStore', '__init__', 1, 1, 1).
python_method('ExecutionHistoryStore', 'now', 0, 1, 2).
python_method('ExecutionHistoryStore', 'init_db', 0, 1, 5).
python_method('ExecutionHistoryStore', 'record', 8, 4, 8).
python_method('ExecutionHistoryStore', '_decode_row', 1, 4, 2).
python_method('ExecutionHistoryStore', 'recent', 2, 3, 6).
python_method('ExecutionHistoryStore', 'count_since_id', 1, 1, 6).
python_method('ExecutionHistoryStore', 'latest_id', 0, 1, 6).
python_class('tellm/improvement/runner.py', 'AutoimprovementRunner').
python_method('AutoimprovementRunner', '__init__', 2, 1, 0).
python_method('AutoimprovementRunner', 'now', 0, 1, 2).
python_method('AutoimprovementRunner', '_finding', 6, 2, 0).
python_method('AutoimprovementRunner', '_collect_source_values', 1, 6, 7).
python_method('AutoimprovementRunner', '_collect_error_objects', 1, 9, 7).
python_method('AutoimprovementRunner', '_looks_like_weather_identifier', 2, 2, 2).
python_method('AutoimprovementRunner', '_looks_like_ad_hoc_weather_function', 2, 3, 2).
python_method('AutoimprovementRunner', '_schema_health', 1, 15, 6).
python_method('AutoimprovementRunner', '_history_health', 3, 39, 18).
python_method('AutoimprovementRunner', '_patches_from_findings', 2, 6, 4).
python_method('AutoimprovementRunner', '_suggested_actions', 1, 2, 1).
python_method('AutoimprovementRunner', 'registry_health', 0, 2, 6).
python_method('AutoimprovementRunner', 'run', 1, 11, 15).
python_class('tellm/registry/core.py', 'RegistryError').
python_class('tellm/registry/core.py', 'RegistryPermissionError').
python_class('tellm/registry/core.py', 'RegistryValidationError').
python_class('tellm/registry/core.py', 'RegistryEntry').
python_method('RegistryEntry', '__post_init__', 0, 17, 7).
python_method('RegistryEntry', '_transport_manifest', 0, 4, 3).
python_method('RegistryEntry', 'to_dict', 1, 3, 1).
python_class('tellm/registry/core.py', 'ResourceRegistry').
python_method('ResourceRegistry', '__init__', 0, 1, 0).
python_method('ResourceRegistry', 'register', 1, 2, 0).
python_method('ResourceRegistry', 'register_alias', 9, 11, 2).
python_method('ResourceRegistry', 'register_value', 36, 14, 2).
python_method('ResourceRegistry', 'register_callable', 33, 14, 2).
python_method('ResourceRegistry', 'get', 1, 2, 1).
python_method('ResourceRegistry', 'get_canonical', 1, 2, 1).
python_method('ResourceRegistry', 'require', 1, 2, 2).
python_method('ResourceRegistry', 'list', 1, 4, 3).
python_method('ResourceRegistry', 'find', 5, 14, 1).
python_method('ResourceRegistry', 'find_capability', 2, 3, 1).
python_method('ResourceRegistry', 'discover_for_llm', 0, 3, 4).
python_method('ResourceRegistry', 'manifest', 0, 2, 4).
python_method('ResourceRegistry', 'check_permission', 3, 6, 3).
python_method('ResourceRegistry', '_apply_alias_input', 2, 5, 4).
python_method('ResourceRegistry', '_resolve_internal', 3, 17, 7).
python_method('ResourceRegistry', 'canonicalize', 1, 1, 1).
python_method('ResourceRegistry', 'resolve_uri', 2, 1, 3).
python_method('ResourceRegistry', 'resolve', 1, 1, 1).
python_method('ResourceRegistry', 'read', 1, 3, 5).
python_method('ResourceRegistry', 'execute', 3, 5, 7).
python_method('ResourceRegistry', '_call', 2, 4, 5).
python_class('tellm/server.py', 'TellmServer').
python_method('TellmServer', '__init__', 3, 1, 1).
python_method('TellmServer', 'register_function', 2, 1, 1).
python_method('TellmServer', '_http_response', 3, 1, 4).
python_method('TellmServer', '_json_response', 2, 1, 3).
python_method('TellmServer', '_resource_entry_response', 1, 4, 2).
python_method('TellmServer', '_registry_item_summary', 1, 2, 2).
python_method('TellmServer', '_virtual_schema_resource', 1, 5, 3).
python_method('TellmServer', '_virtual_view_resource', 1, 9, 5).
python_method('TellmServer', '_schema_bundle', 1, 2, 0).
python_method('TellmServer', '_describe_entry', 1, 6, 4).
python_method('TellmServer', '_validation_error', 1, 2, 2).
python_method('TellmServer', '_validate_payload', 3, 4, 5).
python_method('TellmServer', '_payload_from_query', 2, 4, 4).
python_method('TellmServer', 'process_request', 2, 95, 43).
python_method('TellmServer', '_call_maybe_async', 1, 2, 3).
python_method('TellmServer', '_run_blocking', 1, 1, 1).
python_method('TellmServer', '_send_log', 5, 2, 2).
python_method('TellmServer', '_send_state', 3, 2, 2).
python_method('TellmServer', '_compact', 2, 2, 2).
python_method('TellmServer', '_collect_source_values', 1, 6, 7).
python_method('TellmServer', '_requires_real_world_data', 2, 3, 2).
python_method('TellmServer', '_registry_entry_for_task', 1, 2, 2).
python_method('TellmServer', '_data_source_findings', 3, 21, 15).
python_method('TellmServer', '_append_data_quality_warnings', 2, 8, 6).
python_method('TellmServer', '_log_details', 2, 4, 2).
python_method('TellmServer', '_result_business_ok', 1, 10, 5).
python_method('TellmServer', '_service_result_log', 2, 8, 3).
python_method('TellmServer', '_workflow_history_status', 3, 3, 1).
python_method('TellmServer', '_render_logs', 6, 12, 11).
python_method('TellmServer', '_local_validation_verdict', 4, 23, 8).
python_method('TellmServer', '_validate_and_repair', 8, 12, 17).
python_method('TellmServer', '_answer_from_service_result', 1, 5, 3).
python_method('TellmServer', '_looks_executable_query', 1, 2, 2).
python_method('TellmServer', '_repair_count', 1, 5, 2).
python_method('TellmServer', '_duration_ms', 1, 1, 3).
python_method('TellmServer', '_handle_transcription', 4, 13, 26).
python_method('TellmServer', '_handle_resource_execution', 5, 14, 23).
python_method('TellmServer', '_handle_test_transcription', 4, 2, 8).
python_method('TellmServer', '_audio_payload', 1, 5, 8).
python_method('TellmServer', '_process_message', 2, 15, 15).
python_method('TellmServer', 'handle', 2, 10, 14).
python_method('TellmServer', 'serve_forever', 0, 1, 5).
python_method('TellmServer', 'run', 0, 2, 3).

% ── Dependencies ─────────────────────────────────────────
project_dependency('litellm>=1.0.0', 'requirements.txt').
project_dependency('websockets>=12.0', 'requirements.txt').
project_dependency('python-dotenv>=1.0.0', 'requirements.txt').
project_dependency('pyttsx3>=2.90', 'requirements.txt').
project_dependency('faster-whisper>=0.11.0', 'requirements.txt').

% ── Makefile Targets ─────────────────────────────────────

% ── Taskfile Tasks ───────────────────────────────────────

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', 'twoj_key', '').
env_variable('LLM_MODEL', 'openrouter/qwen/qwen3-coder-next', '').
env_variable('HOST', 'localhost', '').
env_variable('PORT', '8000', '').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-from-pytests.testql.toon.yaml', 'integration').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
```

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

## Intent

tellm v4 - STT+TTS+LLM+SQLite+HTML
