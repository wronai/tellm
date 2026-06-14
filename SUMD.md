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
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `tellm`
- **version**: `0.0.0`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: requirements.txt, testql(1), app.doql.less, goal.yaml, .env.example, project/(3 analysis files)

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
- **version files**: `VERSION`, `setup.py:version`, `__init__.py:__version__`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# tellm | 12f 2492L | python:9,shell:2,less:1 | 2026-06-14
# stats: 36 func | 6 cls | 12 mod | CC̄=3.4 | critical:2 | cycles:0
# alerts[5]: CC test_server_handles_plain_http_request=11; CC test_server_docs_describe_text_and_speech_api=11; CC async_main=7; CC test_view_html_renders_dynamic_json_structure=7; CC test_server_accepts_text_websocket_messages=7
# hotspots[5]: test_server_accepts_text_websocket_messages fan=18; test_server_handles_plain_http_request fan=14; test_server_docs_describe_text_and_speech_api fan=14; test_server_test_mode_returns_echo_without_llm fan=11; main fan=10
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[12]:
  __init__.py,9
  app.doql.less,23
  bot.py,565
  config.py,12
  main.py,16
  project.sh,59
  scripts/generate_test_audio.py,110
  scripts/protocol_smoke.py,234
  server.py,1017
  setup.py,18
  tests/test_tellm.py,427
  tree.sh,2
D:
  __init__.py:
    e: create_bot,run_server
    create_bot(db_path)
    run_server(host;port;db_path)
  bot.py:
    e: TaskType,Task,ViewData,TellmBot
    TaskType:
    Task:
    ViewData: to_dict(0),_safe_json(1),_safe_text(1),_render_items(1),_render_table(1),_render_block(1),_render_dynamic(0),to_html(0)
    TellmBot: __init__(2),_init_db(0),save_task(3),save_evolution(2),save_view(1),get_view_html(1),get_tasks(1),register_function(2),_completion(1),_parse_json_response(1),_normalize_processes(1),_ensure_function_state(1),_restricted_import(5),_process_globals(0),_execute_registered_function(2),_execute_python_process(2),execute_processes(1),_get_stt_model(0),_get_tts(0),analyze_query(1),evolve_function(1),execute_task(1),transcribe(2),speak(1),generate_view(3)
  config.py:
    e: load_config,Config
    Config:
    load_config()
  main.py:
    e: main
    main()
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
  server.py:
    e: _websocket_logger,_browser_client_html,_docs_html,TellmServer
    TellmServer: __init__(3),register_function(2),_http_response(3),process_request(2),_call_maybe_async(1),_run_blocking(1),_handle_transcription(3),_handle_test_transcription(4),_audio_payload(1),handle(2),serve_forever(0),run(0)
    _websocket_logger()
    _browser_client_html(host)
    _docs_html(host)
  setup.py:
  tests/test_tellm.py:
    e: test_import,test_sqlite_save_and_get_tasks,test_view_html_escapes_user_content,test_view_html_renders_dynamic_json_structure,test_execute_task_supports_sync_functions,test_analyze_query_reads_llm_json_view_and_processes,test_execute_task_runs_python_process,test_server_starts_inside_running_event_loop,test_server_handles_plain_http_request,test_server_docs_describe_text_and_speech_api,test_server_audio_payload_reads_data_url_suffix,test_server_test_mode_returns_echo_without_llm,test_server_accepts_text_websocket_messages
    test_import()
    test_sqlite_save_and_get_tasks(tmp_path)
    test_view_html_escapes_user_content()
    test_view_html_renders_dynamic_json_structure()
    test_execute_task_supports_sync_functions(tmp_path)
    test_analyze_query_reads_llm_json_view_and_processes(tmp_path;monkeypatch)
    test_execute_task_runs_python_process(tmp_path)
    test_server_starts_inside_running_event_loop(tmp_path)
    test_server_handles_plain_http_request(tmp_path)
    test_server_docs_describe_text_and_speech_api(tmp_path)
    test_server_audio_payload_reads_data_url_suffix(tmp_path)
    test_server_test_mode_returns_echo_without_llm(tmp_path)
    test_server_accepts_text_websocket_messages(tmp_path;monkeypatch)
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('tellm', '0.0.0', 'python').

% ── Project Files ────────────────────────────────────────
project_file('__init__.py', 9, 'python').
project_file('app.doql.less', 23, 'less').
project_file('bot.py', 565, 'python').
project_file('config.py', 12, 'python').
project_file('main.py', 16, 'python').
project_file('project.sh', 59, 'shell').
project_file('scripts/generate_test_audio.py', 110, 'python').
project_file('scripts/protocol_smoke.py', 234, 'python').
project_file('server.py', 1017, 'python').
project_file('setup.py', 18, 'python').
project_file('tests/test_tellm.py', 427, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('__init__.py', 'create_bot', 1, 1, 1).
python_function('__init__.py', 'run_server', 3, 1, 2).
python_function('config.py', 'load_config', 0, 1, 3).
python_function('main.py', 'main', 0, 3, 8).
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
python_function('server.py', '_websocket_logger', 0, 1, 4).
python_function('server.py', '_browser_client_html', 1, 1, 0).
python_function('server.py', '_docs_html', 1, 1, 1).
python_function('tests/test_tellm.py', 'test_import', 0, 3, 1).
python_function('tests/test_tellm.py', 'test_sqlite_save_and_get_tasks', 1, 4, 7).
python_function('tests/test_tellm.py', 'test_view_html_escapes_user_content', 0, 5, 3).
python_function('tests/test_tellm.py', 'test_view_html_renders_dynamic_json_structure', 0, 7, 3).
python_function('tests/test_tellm.py', 'test_execute_task_supports_sync_functions', 1, 2, 6).
python_function('tests/test_tellm.py', 'test_analyze_query_reads_llm_json_view_and_processes', 2, 6, 9).
python_function('tests/test_tellm.py', 'test_execute_task_runs_python_process', 1, 2, 5).
python_function('tests/test_tellm.py', 'test_server_starts_inside_running_event_loop', 1, 1, 7).
python_function('tests/test_tellm.py', 'test_server_handles_plain_http_request', 1, 11, 14).
python_function('tests/test_tellm.py', 'test_server_docs_describe_text_and_speech_api', 1, 11, 14).
python_function('tests/test_tellm.py', 'test_server_audio_payload_reads_data_url_suffix', 1, 3, 5).
python_function('tests/test_tellm.py', 'test_server_test_mode_returns_echo_without_llm', 1, 4, 11).
python_function('tests/test_tellm.py', 'test_server_accepts_text_websocket_messages', 2, 7, 18).

% ── Python Classes ───────────────────────────────────────
python_class('bot.py', 'TaskType').
python_class('bot.py', 'Task').
python_class('bot.py', 'ViewData').
python_method('ViewData', 'to_dict', 0, 1, 0).
python_method('ViewData', '_safe_json', 1, 1, 2).
python_method('ViewData', '_safe_text', 1, 2, 2).
python_method('ViewData', '_render_items', 1, 5, 4).
python_method('ViewData', '_render_table', 1, 11, 5).
python_method('ViewData', '_render_block', 1, 11, 11).
python_method('ViewData', '_render_dynamic', 0, 6, 5).
python_method('ViewData', 'to_html', 0, 5, 5).
python_class('bot.py', 'TellmBot').
python_method('TellmBot', '__init__', 2, 2, 2).
python_method('TellmBot', '_init_db', 0, 1, 5).
python_method('TellmBot', 'save_task', 3, 1, 6).
python_method('TellmBot', 'save_evolution', 2, 1, 5).
python_method('TellmBot', 'save_view', 1, 1, 8).
python_method('TellmBot', 'get_view_html', 1, 2, 5).
python_method('TellmBot', 'get_tasks', 1, 2, 6).
python_method('TellmBot', 'register_function', 2, 1, 0).
python_method('TellmBot', '_completion', 1, 1, 1).
python_method('TellmBot', '_parse_json_response', 1, 9, 7).
python_method('TellmBot', '_normalize_processes', 1, 5, 1).
python_method('TellmBot', '_ensure_function_state', 1, 1, 1).
python_method('TellmBot', '_restricted_import', 5, 2, 3).
python_method('TellmBot', '_process_globals', 0, 1, 1).
python_method('TellmBot', '_execute_registered_function', 2, 2, 1).
python_method('TellmBot', '_execute_python_process', 2, 22, 15).
python_method('TellmBot', 'execute_processes', 1, 7, 5).
python_method('TellmBot', '_get_stt_model', 0, 2, 1).
python_method('TellmBot', '_get_tts', 0, 2, 2).
python_method('TellmBot', 'analyze_query', 1, 12, 9).
python_method('TellmBot', 'evolve_function', 1, 4, 8).
python_method('TellmBot', 'execute_task', 1, 7, 3).
python_method('TellmBot', 'transcribe', 2, 5, 9).
python_method('TellmBot', 'speak', 1, 1, 3).
python_method('TellmBot', 'generate_view', 3, 3, 5).
python_class('config.py', 'Config').
python_class('server.py', 'TellmServer').
python_method('TellmServer', '__init__', 3, 1, 1).
python_method('TellmServer', 'register_function', 2, 1, 1).
python_method('TellmServer', '_http_response', 3, 1, 4).
python_method('TellmServer', 'process_request', 2, 8, 11).
python_method('TellmServer', '_call_maybe_async', 1, 2, 3).
python_method('TellmServer', '_run_blocking', 1, 1, 1).
python_method('TellmServer', '_handle_transcription', 3, 2, 9).
python_method('TellmServer', '_handle_test_transcription', 4, 2, 8).
python_method('TellmServer', '_audio_payload', 1, 5, 8).
python_method('TellmServer', 'handle', 2, 10, 12).
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
```

## Call Graph

*19 nodes · 15 edges · 6 modules · CC̄=3.4*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `_handle_transcription` *(in server.TellmServer)* | 2 | 0 | 15 | **15** |
| `generate_fixture` *(in scripts.generate_test_audio)* | 2 | 1 | 13 | **14** |
| `main` *(in main)* | 3 | 0 | 14 | **14** |
| `send_ws_payload` *(in scripts.protocol_smoke)* | 4 | 2 | 10 | **12** |
| `main` *(in scripts.generate_test_audio)* | 4 | 0 | 9 | **9** |
| `check_http` *(in scripts.protocol_smoke)* | 3 | 2 | 7 | **9** |
| `load_config` *(in config)* | 1 | 3 | 6 | **9** |
| `check_ws_audio` *(in scripts.protocol_smoke)* | 4 | 1 | 8 | **9** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/tellm
# generated in 0.01s
# nodes: 19 | edges: 15 | modules: 6
# CC̄=3.4

HUBS[20]:
  server.TellmServer._handle_transcription
    CC=2  in:0  out:15  total:15
  scripts.generate_test_audio.generate_fixture
    CC=2  in:1  out:13  total:14
  main.main
    CC=3  in:0  out:14  total:14
  scripts.protocol_smoke.send_ws_payload
    CC=4  in:2  out:10  total:12
  scripts.generate_test_audio.main
    CC=4  in:0  out:9  total:9
  scripts.protocol_smoke.check_http
    CC=3  in:2  out:7  total:9
  config.load_config
    CC=1  in:3  out:6  total:9
  scripts.protocol_smoke.check_ws_audio
    CC=4  in:1  out:8  total:9
  scripts.protocol_smoke.check_ws_text
    CC=3  in:1  out:7  total:8
  scripts.protocol_smoke.audio_data_url
    CC=1  in:1  out:4  total:5
  server._websocket_logger
    CC=1  in:1  out:4  total:5
  server.TellmServer.serve_forever
    CC=1  in:0  out:5  total:5
  scripts.protocol_smoke.get_url
    CC=3  in:1  out:4  total:5
  scripts.generate_test_audio.require_tool
    CC=2  in:2  out:2  total:4
  scripts.protocol_smoke.async_main
    CC=7  in:1  out:3  total:4
  scripts.generate_test_audio.run
    CC=1  in:2  out:1  total:3
  scripts.protocol_smoke.ws_ssl_context
    CC=3  in:1  out:2  total:3
  scripts.protocol_smoke.mime_for_audio
    CC=3  in:1  out:1  total:2
  bot.TellmBot.__init__
    CC=2  in:0  out:2  total:2

MODULES:
  bot  [1 funcs]
    __init__  CC=2  out:2
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
  server  [3 funcs]
    _handle_transcription  CC=2  out:15
    serve_forever  CC=1  out:5
    _websocket_logger  CC=1  out:4

EDGES:
  server.TellmServer._handle_transcription → config.load_config
  server.TellmServer.serve_forever → server._websocket_logger
  bot.TellmBot.__init__ → config.load_config
  main.main → config.load_config
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
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Integration (1)

**`Auto-generated from Python Tests`**

## Intent

tellm v4 - STT+TTS+LLM+SQLite+HTML
