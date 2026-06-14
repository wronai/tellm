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

