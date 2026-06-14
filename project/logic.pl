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
project_file('server.py', 1028, 'python').
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
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').

