# tellm v4 - STT+TTS+LLM+SQLite+HTML

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `tellm`
- **version**: `0.0.0`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: requirements.txt, testql(1), app.doql.less, goal.yaml, .env.example, project/(5 analysis files)

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

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

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

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 13f 2494L | python:8,shell:2,yaml:1,txt:1,json:1 | 2026-06-14
# generated in 0.00s
# CC̅=3.4 | critical:1/67 | dups:0 | cycles:0

HEALTH[2]:
  🔴 GOD   bot.py = 553L, 4 classes, 32m, max CC=22
  🟡 CC    _execute_python_process CC=22 (limit:15)

REFACTOR[2]:
  1. split bot.py  (god module)
  2. split 1 high-CC methods  (CC>15)

PIPELINES[47]:
  [1] Src [__init__]: __init__
      PURITY: 100% pure
  [2] Src [register_function]: register_function
      PURITY: 100% pure
  [3] Src [_http_response]: _http_response
      PURITY: 100% pure
  [4] Src [process_request]: process_request → _docs_html
      PURITY: 100% pure
  [5] Src [_call_maybe_async]: _call_maybe_async
      PURITY: 100% pure
  [6] Src [_run_blocking]: _run_blocking
      PURITY: 100% pure
  [7] Src [_handle_transcription]: _handle_transcription → load_config
      PURITY: 100% pure
  [8] Src [_handle_test_transcription]: _handle_test_transcription
      PURITY: 100% pure
  [9] Src [_audio_payload]: _audio_payload
      PURITY: 100% pure
  [10] Src [handle]: handle
      PURITY: 100% pure
  [11] Src [serve_forever]: serve_forever → _websocket_logger
      PURITY: 100% pure
  [12] Src [run]: run
      PURITY: 100% pure
  [13] Src [create_bot]: create_bot
      PURITY: 100% pure
  [14] Src [run_server]: run_server
      PURITY: 100% pure
  [15] Src [_safe_json]: _safe_json
      PURITY: 100% pure
  [16] Src [_safe_text]: _safe_text
      PURITY: 100% pure
  [17] Src [_render_items]: _render_items
      PURITY: 100% pure
  [18] Src [_render_table]: _render_table
      PURITY: 100% pure
  [19] Src [_render_block]: _render_block
      PURITY: 100% pure
  [20] Src [_render_dynamic]: _render_dynamic
      PURITY: 100% pure
  [21] Src [to_html]: to_html
      PURITY: 100% pure
  [22] Src [__init__]: __init__ → load_config
      PURITY: 100% pure
  [23] Src [_init_db]: _init_db
      PURITY: 100% pure
  [24] Src [save_task]: save_task
      PURITY: 100% pure
  [25] Src [save_evolution]: save_evolution
      PURITY: 100% pure
  [26] Src [save_view]: save_view
      PURITY: 100% pure
  [27] Src [get_tasks]: get_tasks
      PURITY: 100% pure
  [28] Src [_completion]: _completion
      PURITY: 100% pure
  [29] Src [_parse_json_response]: _parse_json_response
      PURITY: 100% pure
  [30] Src [_normalize_processes]: _normalize_processes
      PURITY: 100% pure
  [31] Src [_ensure_function_state]: _ensure_function_state
      PURITY: 100% pure
  [32] Src [_restricted_import]: _restricted_import
      PURITY: 100% pure
  [33] Src [_process_globals]: _process_globals
      PURITY: 100% pure
  [34] Src [_execute_registered_function]: _execute_registered_function
      PURITY: 100% pure
  [35] Src [_execute_python_process]: _execute_python_process
      PURITY: 100% pure
  [36] Src [execute_processes]: execute_processes
      PURITY: 100% pure
  [37] Src [_get_stt_model]: _get_stt_model
      PURITY: 100% pure
  [38] Src [_get_tts]: _get_tts
      PURITY: 100% pure
  [39] Src [analyze_query]: analyze_query
      PURITY: 100% pure
  [40] Src [evolve_function]: evolve_function
      PURITY: 100% pure
  [41] Src [execute_task]: execute_task
      PURITY: 100% pure
  [42] Src [transcribe]: transcribe
      PURITY: 100% pure
  [43] Src [speak]: speak
      PURITY: 100% pure
  [44] Src [generate_view]: generate_view
      PURITY: 100% pure
  [45] Src [main]: main → load_config
      PURITY: 100% pure
  [46] Src [main]: main → generate_fixture → run
      PURITY: 100% pure
  [47] Src [main]: main → check_http → get_url
      PURITY: 100% pure

LAYERS:
  ./                              CC̄=3.5    ←in:0  →out:0
  │ !! server                     910L  1C   15m  CC=10     ←0
  │ !! bot                        553L  4C   32m  CC=22     ←0
  │ !! goal.yaml                  511L  0C    0m  CC=0.0    ←0
  │ project.sh                  59L  0C    0m  CC=0.0    ←0
  │ setup                       17L  0C    0m  CC=0.0    ←0
  │ main                        16L  0C    1m  CC=3      ←0
  │ config                      12L  1C    1m  CC=1      ←3
  │ __init__                     8L  0C    2m  CC=1      ←0
  │ requirements.txt             5L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=3.0    ←in:0  →out:0
  │ protocol_smoke             233L  0C   12m  CC=7      ←0
  │ generate_test_audio        109L  0C    4m  CC=4      ←0
  │
  output/                         CC̄=0.0    ←in:0  →out:0
  │ manifest.json               60L  0C    0m  CC=0.0    ←0
  │

COUPLING:
          config     bot    main  server
  config      ──      ←1      ←1      ←1
     bot       1      ──                
    main       1              ──        
  server       1                      ──
  CYCLES: none

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 0 groups | 7f 1749L | 2026-06-13

SUMMARY:
  files_scanned: 7
  total_lines:   1749
  dup_groups:    0
  dup_fragments: 0
  saved_lines:   0
  scan_ms:       2666
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 51 func | 5f | 2026-06-14
# generated in 0.00s

NEXT[4] (ranked by impact):
  [1] !! SPLIT           bot.py
      WHY: 553L, 4 classes, max CC=22
      EFFORT: ~4h  IMPACT: 12166

  [2] !! SPLIT           server.py
      WHY: 910L, 1 classes, max CC=10
      EFFORT: ~4h  IMPACT: 9100

  [3] !  SPLIT-FUNC      TellmBot._execute_python_process  CC=22  fan=16
      WHY: CC=22 exceeds 15
      EFFORT: ~1h  IMPACT: 352

  [4] !! SPLIT           goal.yaml
      WHY: 511L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting server.py may break 15 import paths
  ⚠ Splitting bot.py may break 32 import paths
  ⚠ Splitting goal.yaml may break 0 import paths

METRICS-TARGET:
  CC̄:          3.5 → ≤2.4
  max-CC:      22 → ≤11
  god-modules: 3 → 0
  high-CC(≥15): 1 → ≤0
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
  (first run — no previous data)
```

## Intent

tellm v4 - STT+TTS+LLM+SQLite+HTML
