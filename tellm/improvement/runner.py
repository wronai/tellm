from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tellm.registry import ResourceRegistry, service_result, validate_schema

from .history import ExecutionHistoryStore


class AutoimprovementRunner:
    def __init__(self, registry: ResourceRegistry, history: ExecutionHistoryStore):
        self.registry = registry
        self.history = history

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _finding(
        severity: str,
        finding_type: str,
        problem: str,
        recommendation: str,
        uri: str = "",
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "severity": severity,
            "type": finding_type,
            "uri": uri,
            "problem": problem,
            "recommendation": recommendation,
            "evidence": evidence or {},
        }

    @staticmethod
    def _collect_source_values(value: Any) -> List[str]:
        sources: List[str] = []
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower() == "source":
                    sources.append(str(item))
                sources.extend(AutoimprovementRunner._collect_source_values(item))
        elif isinstance(value, list):
            for item in value:
                sources.extend(AutoimprovementRunner._collect_source_values(item))
        return sources

    @staticmethod
    def _collect_error_objects(value: Any) -> List[Dict[str, Any]]:
        errors: List[Dict[str, Any]] = []
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower() == "errors" and isinstance(item, list):
                    for error in item:
                        if isinstance(error, dict):
                            errors.append(error)
                        else:
                            errors.append({"detail": str(error), "code": ""})
                else:
                    errors.extend(AutoimprovementRunner._collect_error_objects(item))
        elif isinstance(value, list):
            for item in value:
                errors.extend(AutoimprovementRunner._collect_error_objects(item))
        return errors

    @staticmethod
    def _looks_like_weather_identifier(uri: str, query: str) -> bool:
        text = (uri + " " + query).lower()
        return any(keyword in text for keyword in ["weather", "pogoda", "temperatura"])

    @staticmethod
    def _looks_like_ad_hoc_weather_function(uri: str, query: str) -> bool:
        if uri.startswith("tellm://service/weather/current"):
            return False
        if uri.startswith("tellm://"):
            return False
        return AutoimprovementRunner._looks_like_weather_identifier(uri, query)

    def _schema_health(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        invalid = 0
        missing = 0
        entries = self.registry.list()
        for entry in entries:
            if not entry.description:
                findings.append(
                    self._finding(
                        "info",
                        "missing_description",
                        "Resource has no description.",
                        "Add a short operational description so LLM discovery is auditable.",
                        entry.uri,
                    )
                )
            if not entry.tags:
                findings.append(
                    self._finding(
                        "info",
                        "missing_tags",
                        "Resource has no tags.",
                        "Add tags for filtering in registry UI and autoimprovement reports.",
                        entry.uri,
                    )
                )

            if entry.kind in {"function", "service", "process", "tool"}:
                if not entry.input_schema:
                    missing += 1
                    findings.append(
                        self._finding(
                            "warning",
                            "missing_input_schema",
                            "Executable resource has no input_schema.",
                            "Add input_schema before exposing this resource to LLM execution.",
                            entry.uri,
                        )
                    )
                if not entry.output_schema:
                    missing += 1
                    findings.append(
                        self._finding(
                            "warning",
                            "missing_output_schema",
                            "Executable resource has no output_schema.",
                            "Add output_schema so service results can be validated.",
                            entry.uri,
                        )
                    )
                try:
                    validate_schema({"type": "object"}, entry.input_schema or {})
                    validate_schema({"type": "object"}, entry.output_schema or {})
                except Exception as exc:
                    invalid += 1
                    findings.append(
                        self._finding(
                            "error",
                            "invalid_schema",
                            "Resource schema is not a JSON object.",
                            "Replace the schema with a valid JSON-schema object.",
                            entry.uri,
                            {"error": str(exc)},
                        )
                    )

            danger = str(entry.permissions.get("danger_level", "read_only"))
            if danger in {"dangerous", "secret"} and entry.permissions.get("llm_execute"):
                findings.append(
                    self._finding(
                        "error",
                        "unsafe_permission",
                        "High-risk resource is executable by LLM.",
                        "Disable llm_execute or require explicit confirmation and policy review.",
                        entry.uri,
                        {"danger_level": danger},
                    )
                )
            if danger in {"network", "execute_local", "write_local", "dangerous"}:
                if entry.permissions.get("llm_execute") and not entry.output_schema:
                    findings.append(
                        self._finding(
                            "warning",
                            "executable_without_output_schema",
                            "Executable non-safe resource lacks output validation.",
                            "Define output_schema before relying on this resource in automated workflows.",
                            entry.uri,
                            {"danger_level": danger},
                        )
                    )
        return {"invalid_schemas": invalid, "missing_schemas": missing}

    def _history_health(
        self,
        findings: List[Dict[str, Any]],
        recent: List[Dict[str, Any]],
        repeated_failure_threshold: int,
    ) -> Dict[str, int]:
        failures_by_uri = defaultdict(list)
        renderer_errors = 0
        repair_loop_errors = 0
        direct_answer_violations = 0
        failed_validations = 0
        simulated_data_warnings = 0
        missing_real_data_provider = 0
        provider_location_resolution_failed = 0
        ad_hoc_function_generated = 0
        disallowed_sources = {"local_simulation", "mock", "test", "llm_generated", "generated"}

        for item in recent:
            uri = item.get("uri") or ""
            result = item.get("result")
            metadata = item.get("metadata") or {}
            query = str(metadata.get("query") or "")
            if not item.get("ok") or (
                isinstance(result, dict) and result.get("ok") is False
            ):
                failures_by_uri[uri].append(item)
            errors = self._collect_error_objects(result)
            error_codes = {
                str(error.get("code") or "").upper()
                for error in errors
                if error.get("code")
            }
            if (
                "NETWORK_ACCESS_NOT_ALLOWED" in error_codes
                and self._looks_like_weather_identifier(uri, query)
            ):
                missing_real_data_provider += 1
                findings.append(
                    self._finding(
                        "warning",
                        "missing_real_data_provider",
                        "Zapytanie wymaga aktualnych danych pogodowych, ale system nie ma skonfigurowanej lokalnej usługi z dostępnym providerem.",
                        "Dodać weather.current jako stałą usługę registry z providerem Open-Meteo/IMGW i kontrolowanym uprawnieniem network=true.",
                        "tellm://service/weather/current",
                        {
                            "execution_id": item.get("id"),
                            "uri": uri,
                            "error_codes": sorted(error_codes),
                        },
                    )
                )
            if (
                "LOCATION_NOT_FOUND" in error_codes
                and self._looks_like_weather_identifier(uri, query)
            ):
                provider_location_resolution_failed += 1
                findings.append(
                    self._finding(
                        "warning",
                        "provider_location_resolution_failed",
                        "Usługa weather.current użyła realnego providera, ale geocoding nie znalazł lokalizacji mimo że zapytanie wygląda na poprawne.",
                        "Dodać normalizację country do ISO-3166 alpha-2, fallback geocoding bez kraju oraz cache znanych lokalizacji.",
                        "tellm://service/weather/current",
                        {
                            "execution_id": item.get("id"),
                            "uri": uri,
                            "error_codes": sorted(error_codes),
                            "errors": errors,
                        },
                    )
                )
            if self._looks_like_ad_hoc_weather_function(uri, query):
                ad_hoc_function_generated += 1
                findings.append(
                    self._finding(
                        "info",
                        "ad_hoc_function_generated",
                        "LLM wygenerował funkcję pogodową ad hoc zamiast użyć generycznej usługi tellm://service/weather/current.",
                        "Dodać routing intent weather.current do registry i zablokować tworzenie funkcji per lokalizacja.",
                        uri,
                        {"execution_id": item.get("id"), "query": query},
                    )
                )
            for finding in metadata.get("data_quality_findings", []) or []:
                if finding.get("type") == "simulated_data_used_for_real_world_query":
                    simulated_data_warnings += 1
                    findings.append(
                        self._finding(
                            "warning",
                            "simulated_data_used_for_real_world_query",
                            finding.get(
                                "problem",
                                "Workflow used simulated data for a real-world query.",
                            ),
                            finding.get(
                                "recommendation",
                                "Route the query through a typed registry service with an allowed real provider.",
                            ),
                            uri,
                            {"execution_id": item.get("id"), "source": finding.get("source", "")},
                        )
                    )
            sources = [
                source.strip().lower()
                for source in self._collect_source_values(result)
            ]
            for source in sources:
                if source in disallowed_sources:
                    simulated_data_warnings += 1
                    findings.append(
                        self._finding(
                            "warning",
                            "simulated_data_used_for_real_world_query",
                            "Execution result used source=%s." % source,
                            "Use a typed registry service with an explicit real provider, or mark the result as simulation/test in UI.",
                            uri,
                            {"execution_id": item.get("id"), "source": source},
                        )
                    )
            if metadata.get("llm_direct_answer_violation"):
                direct_answer_violations += 1
                findings.append(
                    self._finding(
                        "error",
                        "llm_direct_answer_violation",
                        "Workflow appears to have answered an executable task without a local service.",
                        "Route this task through a tellm://service/... registry resource.",
                        uri,
                        {"execution_id": item.get("id"), "query": metadata.get("query", "")},
                    )
                )
            for log in item.get("logs") or []:
                if log.get("stage") == "renderer" and log.get("status") == "error":
                    renderer_errors += 1
                if log.get("stage") == "llm_validation" and log.get("status") == "error":
                    failed_validations += 1
                if log.get("stage") == "llm_validation" and log.get("status") == "repair":
                    repair_loop_errors += 1
                if log.get("stage") == "data_source" and log.get("status") == "warning":
                    simulated_data_warnings += 1

        for uri, failures in failures_by_uri.items():
            if len(failures) >= repeated_failure_threshold:
                findings.append(
                    self._finding(
                        "warning",
                        "repeated_service_failure",
                        "Resource failed %d times in recent execution history." % len(failures),
                        "Inspect service errors and add fallback/retry policy or stricter validation.",
                        uri,
                        {"failure_count": len(failures), "latest_error": failures[0].get("error", "")},
                    )
                )

        if renderer_errors:
            findings.append(
                self._finding(
                    "warning",
                    "renderer_errors",
                    "Renderer produced %d recent error log(s)." % renderer_errors,
                    "Inspect render_data shape and add renderer tests for failing block types.",
                    evidence={"count": renderer_errors},
                )
            )
        if failed_validations:
            findings.append(
                self._finding(
                    "error",
                    "failed_validations",
                    "LLM validation reached an error %d time(s)." % failed_validations,
                    "Review validation prompts and cap repair attempts with structured errors.",
                    evidence={"count": failed_validations},
                )
            )
        if repair_loop_errors:
            findings.append(
                self._finding(
                    "info",
                    "renderer_template_repair",
                    "Renderer required %d LLM repair cycle(s)." % repair_loop_errors,
                    "Normalize render_data so renderer can map process results into view blocks without LLM repair.",
                    evidence={"count": repair_loop_errors},
                )
            )

        return {
            "failed_services": sum(len(value) for value in failures_by_uri.values()),
            "renderer_errors": renderer_errors,
            "repair_loops": repair_loop_errors,
            "direct_answer_violations": direct_answer_violations,
            "failed_validations": failed_validations,
            "simulated_data_warnings": simulated_data_warnings,
            "missing_real_data_provider": missing_real_data_provider,
            "provider_location_resolution_failed": provider_location_resolution_failed,
            "ad_hoc_function_generated": ad_hoc_function_generated,
        }

    @staticmethod
    def _patches_from_findings(findings: List[Dict[str, Any]], allow_code_generation: bool) -> List[Dict[str, Any]]:
        patches = []
        for index, finding in enumerate(findings, start=1):
            severity = finding.get("severity")
            if severity not in {"warning", "error"}:
                continue
            risk = "medium" if severity == "warning" else "high"
            if finding.get("type") in {"missing_output_schema", "missing_input_schema", "missing_description", "missing_tags"}:
                risk = "low"
            patches.append(
                {
                    "id": "patch-%03d-%s" % (index, finding.get("type", "finding")),
                    "status": "pending_review",
                    "risk": risk,
                    "uri": finding.get("uri", ""),
                    "description": finding.get("recommendation", ""),
                    "code_generated": False,
                    "allowed_to_generate_code": bool(allow_code_generation and risk == "low"),
                }
            )
        return patches

    @staticmethod
    def _suggested_actions(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "severity": finding.get("severity", "info"),
                "uri": finding.get("uri", ""),
                "action": finding.get("recommendation", ""),
                "source_finding": finding.get("type", ""),
            }
            for finding in findings
        ]

    def registry_health(self) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []
        schema = self._schema_health(findings)
        return {
            "ok": not any(item.get("severity") == "error" for item in findings),
            "checked_at": self.now(),
            "registry_entries": len(self.registry.list()),
            "invalid_schemas": schema["invalid_schemas"],
            "missing_schemas": schema["missing_schemas"],
            "findings": findings,
        }

    def run(self, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        options = options or {}
        dry_run = bool(options.get("dry_run", True))
        allow_auto_apply = bool(options.get("allow_auto_apply", False))
        allow_code_generation = bool(options.get("allow_code_generation", True))
        max_cycles = int(options.get("max_cycles", 10) or 10)
        repeated_failure_threshold = int(options.get("repeated_failure_threshold", 3) or 3)
        recent_limit = max(10, max_cycles * 10)

        findings: List[Dict[str, Any]] = []
        schema = self._schema_health(findings)
        recent = self.history.recent(limit=recent_limit)
        history = self._history_health(findings, recent, repeated_failure_threshold)
        patches = self._patches_from_findings(findings, allow_code_generation)
        suggested_actions = self._suggested_actions(findings)
        auto_applied = 0

        checked = {
            "registry_entries": len(self.registry.list()),
            "schemas": len(self.registry.list()),
            "services": len([entry for entry in self.registry.list() if entry.kind == "service"]),
            "views": len([entry for entry in self.registry.list() if entry.kind == "view"]),
            "execution_history": len(recent),
        }
        summary = {
            "checked_resources": checked["registry_entries"],
            "invalid_schemas": schema["invalid_schemas"],
            "missing_schemas": schema["missing_schemas"],
            "failed_services": history["failed_services"],
            "renderer_errors": history["renderer_errors"],
            "repair_loops": history["repair_loops"],
            "direct_answer_violations": history["direct_answer_violations"],
            "failed_validations": history["failed_validations"],
            "simulated_data_warnings": history["simulated_data_warnings"],
            "missing_real_data_provider": history["missing_real_data_provider"],
            "provider_location_resolution_failed": history[
                "provider_location_resolution_failed"
            ],
            "ad_hoc_function_generated": history["ad_hoc_function_generated"],
            "suggested_patches": len(patches),
            "auto_applied": auto_applied,
        }
        tests = {
            "py_compile": "not_run",
            "pytest": "not_run",
            "smoke": "not_run",
            "reason": "Autoimprovement runs in audit mode and does not execute tests unless a patch is accepted.",
        }
        data = {
            "generated_at": self.now(),
            "mode": str(options.get("mode", "manual")),
            "scope": str(options.get("scope", "registry")),
            "dry_run": dry_run,
            "allow_auto_apply": allow_auto_apply,
            "allow_code_generation": allow_code_generation,
            "checked": checked,
            "summary": summary,
            "findings": findings,
            "suggested_actions": suggested_actions,
            "patches": patches,
            "tests": tests,
        }
        ok = not any(item.get("severity") == "error" for item in findings)
        return service_result(
            ok=ok,
            result_type="system.autoimprovement.report",
            uri="tellm://service/system/autoimprove",
            data=data,
            title="Autoimprovement report",
            summary="Audit completed with %d finding(s) and %d pending patch proposal(s)." % (
                len(findings),
                len(patches),
            ),
            details="Autoimprovement is audit-only by default. Code changes are not auto-applied.",
            errors=[] if ok else [
                {
                    "code": "AUTOIMPROVEMENT_FINDINGS",
                    "source": "system.autoimprove",
                    "detail": "Report contains error-severity findings.",
                }
            ],
            view={"renderer": "auto", "template": "autoimprovement_report", "severity": "info" if ok else "warning"},
        )
