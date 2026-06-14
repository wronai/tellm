import copy
import inspect
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional
from urllib.parse import urlparse


JSON_SCHEMA_DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
TRM_VERSION = "1.0.0"
TSR_VERSION = "1.0.0"

RESOURCE_KINDS = {
    "function",
    "data",
    "variable",
    "env",
    "setting",
    "schema",
    "service",
    "process",
    "view",
    "task",
    "file",
    "model",
    "prompt",
    "tool",
    "event",
    "stream",
    "policy",
    "report",
    "patch",
}

EXECUTABLE_KINDS = {"function", "service", "process", "tool"}

DEFAULT_PERMISSIONS = {
    "llm_discover": True,
    "llm_read": False,
    "llm_write": False,
    "llm_execute": False,
    "requires_confirmation": False,
    "network": False,
    "filesystem_read": False,
    "filesystem_write": False,
    "shell": False,
    "env_read": False,
    "env_write": False,
    "danger_level": "read_only",
}


class RegistryError(Exception):
    pass


class RegistryPermissionError(RegistryError):
    pass


class RegistryValidationError(RegistryError):
    pass


def validate_tellm_uri(uri: str, expected_kind: Optional[str] = None) -> None:
    parsed = urlparse(uri)
    if parsed.scheme != "tellm":
        raise RegistryValidationError("URI must use tellm:// scheme: %s" % uri)
    if not parsed.netloc:
        raise RegistryValidationError("URI must include resource kind authority: %s" % uri)
    if parsed.netloc not in RESOURCE_KINDS:
        raise RegistryValidationError("Unsupported URI kind: %s" % parsed.netloc)
    if expected_kind and parsed.netloc != expected_kind:
        raise RegistryValidationError(
            "URI kind %s does not match entry kind %s" % (parsed.netloc, expected_kind)
        )
    path_parts = [part for part in parsed.path.split("/") if part]
    if not path_parts:
        raise RegistryValidationError("URI must include a resource path: %s" % uri)


def normalize_schema(schema: Optional[Dict[str, Any]], schema_id: str = "") -> Optional[Dict[str, Any]]:
    if not isinstance(schema, dict):
        return schema
    result = copy.deepcopy(schema)
    result.setdefault("$schema", JSON_SCHEMA_DRAFT_2020_12)
    if schema_id and "$id" not in result:
        result["$id"] = schema_id
    return result


def _schema_types(schema_type: Any) -> List[str]:
    if isinstance(schema_type, list):
        return [str(item) for item in schema_type]
    if schema_type is None:
        return []
    return [str(schema_type)]


def _matches_type(value: Any, schema_type: str) -> bool:
    if schema_type == "object":
        return isinstance(value, dict)
    if schema_type == "array":
        return isinstance(value, list)
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "null":
        return value is None
    return True


def validate_schema(schema: Optional[Dict[str, Any]], value: Any, path: str = "$") -> None:
    """Small JSON-schema subset validator used to avoid a hard dependency."""
    if not schema:
        return

    schema_types = _schema_types(schema.get("type"))
    if schema_types and not any(_matches_type(value, item) for item in schema_types):
        raise RegistryValidationError(
            "%s expected %s, got %s" % (path, "/".join(schema_types), type(value).__name__)
        )

    if "enum" in schema and value not in schema["enum"]:
        raise RegistryValidationError("%s must be one of %s" % (path, schema["enum"]))

    if isinstance(value, str) and schema.get("pattern"):
        if not re.match(str(schema["pattern"]), value):
            raise RegistryValidationError("%s does not match pattern" % path)

    if isinstance(value, dict):
        required = schema.get("required") or []
        for key in required:
            if key not in value:
                raise RegistryValidationError("%s.%s is required" % (path, key))

        properties = schema.get("properties") or {}
        for key, child_schema in properties.items():
            if key in value:
                validate_schema(child_schema, value[key], "%s.%s" % (path, key))

        if schema.get("additionalProperties") is False:
            allowed = set(properties)
            for key in value:
                if key not in allowed:
                    raise RegistryValidationError("%s.%s is not allowed" % (path, key))

    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        item_schema = schema["items"]
        for index, item in enumerate(value):
            validate_schema(item_schema, item, "%s[%d]" % (path, index))


def _issue_code_from_text(detail: str, default_code: str) -> str:
    lowered = detail.lower()
    if "network" in lowered and (
        "not allowed" in lowered
        or "denied" in lowered
        or "cannot access" in lowered
        or "requires network" in lowered
    ):
        return "NETWORK_ACCESS_NOT_ALLOWED"
    if "file" in lowered and (
        "not allowed" in lowered
        or "denied" in lowered
        or "cannot access" in lowered
    ):
        return "FILESYSTEM_ACCESS_NOT_ALLOWED"
    return default_code


def normalize_issue_list(
    issues: Optional[List[Any]],
    default_source: str = "",
    default_code: str = "SERVICE_ERROR",
    recoverable: bool = True,
) -> List[Dict[str, Any]]:
    normalized = []
    for issue in issues or []:
        if isinstance(issue, dict):
            item = copy.deepcopy(issue)
            detail = str(
                item.get("detail")
                or item.get("message")
                or item.get("error")
                or item.get("summary")
                or ""
            )
            item["code"] = str(
                item.get("code") or _issue_code_from_text(detail, default_code)
            )
            item["source"] = str(item.get("source") or default_source)
            item["detail"] = detail or json_like(item)
            item["recoverable"] = bool(item.get("recoverable", recoverable))
            normalized.append(item)
        else:
            detail = str(issue)
            normalized.append(
                {
                    "code": _issue_code_from_text(detail, default_code),
                    "source": default_source,
                    "detail": detail,
                    "recoverable": bool(recoverable),
                }
            )
    return normalized


def json_like(value: Any) -> str:
    try:
        import json

        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return str(value)


def service_result(
    ok: bool,
    result_type: str,
    data: Any,
    title: str,
    summary: str,
    details: str = "",
    errors: Optional[List[Dict[str, Any]]] = None,
    view: Optional[Dict[str, Any]] = None,
    uri: str = "",
    warnings: Optional[List[Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
    render: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    render_data = render or view or {"renderer": "auto"}
    source = None
    if isinstance(data, dict):
        source = data.get("source")
    payload = {
        "ok": bool(ok),
        "uri": uri,
        "type": result_type,
        "data": data,
        "message": {
            "title": title,
            "summary": summary,
            "details": details,
        },
        "errors": normalize_issue_list(errors, uri, "SERVICE_ERROR", True),
        "warnings": normalize_issue_list(warnings, uri, "SERVICE_WARNING", True),
        "meta": {
            "source": source,
            "fetched_at": data.get("fetched_at") if isinstance(data, dict) else None,
            "duration_ms": None,
            **(meta or {}),
        },
        "render": render_data,
        "view": render_data,
        "envelope_version": TSR_VERSION,
    }
    return payload


def service_result_schema() -> Dict[str, Any]:
    return {
        "$schema": JSON_SCHEMA_DRAFT_2020_12,
        "$id": "tellm://schema/tellm/service-result",
        "title": "Tellm Service Result",
        "type": "object",
        "required": ["ok", "uri", "type", "data", "message", "errors", "warnings", "meta", "render"],
        "properties": {
            "ok": {"type": "boolean"},
            "uri": {"type": "string", "pattern": r"^tellm://[A-Za-z0-9_.-]+/.+"},
            "type": {"type": "string"},
            "data": {},
            "message": {
                "type": "object",
                "required": ["title", "summary"],
                "properties": {
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "details": {"type": "string"},
                },
                "additionalProperties": True,
            },
            "errors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["code", "source", "detail", "recoverable"],
                    "properties": {
                        "code": {"type": "string"},
                        "source": {"type": "string"},
                        "detail": {"type": "string"},
                        "recoverable": {"type": "boolean"},
                    },
                    "additionalProperties": True,
                },
            },
            "warnings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["code", "source", "detail", "recoverable"],
                    "properties": {
                        "code": {"type": "string"},
                        "source": {"type": "string"},
                        "detail": {"type": "string"},
                        "recoverable": {"type": "boolean"},
                    },
                    "additionalProperties": True,
                },
            },
            "meta": {"type": "object"},
            "render": {"type": "object"},
        },
        "additionalProperties": True,
    }


def registry_manifest_schema() -> Dict[str, Any]:
    return {
        "$schema": JSON_SCHEMA_DRAFT_2020_12,
        "$id": "tellm://schema/tellm/resource-manifest",
        "title": "Tellm Resource Manifest",
        "type": "object",
        "required": [
            "manifest_version",
            "uri",
            "kind",
            "name",
            "version",
            "schema_version",
            "permissions",
        ],
        "properties": {
            "manifest_version": {"type": "string"},
            "uri": {"type": "string", "pattern": r"^tellm://[A-Za-z0-9_.-]+/.+"},
            "kind": {"type": "string", "enum": sorted(RESOURCE_KINDS)},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "version": {"type": "string"},
            "schema_version": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "transport": {"type": "object"},
            "input_schema": {"type": ["object", "null"]},
            "output_schema": {"type": ["object", "null"]},
            "value_schema": {"type": ["object", "null"]},
            "permissions": {"type": "object"},
            "data_policy": {"type": "object"},
            "render": {"type": "object"},
            "compatibility": {"type": "object"},
        },
        "additionalProperties": True,
    }


@dataclass
class RegistryEntry:
    uri: str
    kind: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    schema_version: str = "2020-12"
    transport: Any = "local"
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    value_schema: Optional[Dict[str, Any]] = None
    metadata_schema: Optional[Dict[str, Any]] = None
    callable_ref: Optional[Callable[..., Any]] = None
    value_ref: Any = None
    permissions: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)
    data_policy: Dict[str, Any] = field(default_factory=dict)
    render: Dict[str, Any] = field(default_factory=dict)
    compatibility: Dict[str, Any] = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)
    masked: bool = False

    def __post_init__(self) -> None:
        if self.kind not in RESOURCE_KINDS:
            raise RegistryValidationError("Unsupported resource kind: %s" % self.kind)
        validate_tellm_uri(self.uri, self.kind)
        merged = dict(DEFAULT_PERMISSIONS)
        merged.update(self.permissions or {})
        self.permissions = merged
        self.input_schema = normalize_schema(
            self.input_schema,
            "tellm://schema/" + self.kind + "/" + self.name + "/input",
        )
        self.output_schema = normalize_schema(
            self.output_schema,
            "tellm://schema/" + self.kind + "/" + self.name + "/output",
        )
        self.value_schema = normalize_schema(
            self.value_schema,
            "tellm://schema/" + self.kind + "/" + self.name + "/value",
        )
        self.metadata_schema = normalize_schema(
            self.metadata_schema,
            "tellm://schema/" + self.kind + "/" + self.name + "/metadata",
        )
        if not self.data_policy:
            policy_keys = {
                "requires_real_world_data",
                "allowed_sources",
                "disallowed_sources",
            }
            self.data_policy = {
                key: self.metadata[key]
                for key in policy_keys
                if key in self.metadata
            }
        self.compatibility = {
            "breaking_change": False,
            "deprecated": False,
            **(self.compatibility or {}),
        }

    def _transport_manifest(self) -> Dict[str, Any]:
        if isinstance(self.transport, dict):
            return self.transport
        data = {"type": str(self.transport or "local")}
        if self.callable_ref:
            data["entrypoint"] = getattr(self.callable_ref, "__qualname__", self.name)
        return data

    def to_dict(self, include_private: bool = False) -> Dict[str, Any]:
        data = {
            "manifest_version": TRM_VERSION,
            "uri": self.uri,
            "kind": self.kind,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "schema_version": self.schema_version,
            "compatibility": self.compatibility,
            "transport": self._transport_manifest(),
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "value_schema": self.value_schema,
            "metadata_schema": self.metadata_schema,
            "permissions": self.permissions,
            "data_policy": self.data_policy,
            "render": self.render or {"renderer": "auto"},
            "tags": self.tags,
            "status": self.status,
            "metadata": self.metadata,
            "aliases": self.aliases,
            "masked": self.masked,
        }
        if include_private:
            data["has_callable"] = self.callable_ref is not None
            data["has_value"] = self.value_ref is not None
        return data


class ResourceRegistry:
    def __init__(self) -> None:
        self._entries: Dict[str, RegistryEntry] = {}
        self._aliases: Dict[str, str] = {}

    def register(self, entry: RegistryEntry) -> RegistryEntry:
        self._entries[entry.uri] = entry
        for alias in entry.aliases:
            self._aliases[alias] = entry.uri
        return entry

    def register_value(
        self,
        uri: str,
        kind: str,
        name: str,
        value: Any,
        description: str = "",
        value_schema: Optional[Dict[str, Any]] = None,
        permissions: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        masked: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0",
        data_policy: Optional[Dict[str, Any]] = None,
        render: Optional[Dict[str, Any]] = None,
    ) -> RegistryEntry:
        entry = RegistryEntry(
            uri=uri,
            kind=kind,
            name=name,
            description=description,
            value_ref=value,
            value_schema=value_schema,
            permissions=permissions or {},
            tags=tags or [],
            masked=masked,
            metadata=metadata or {},
            version=version,
            data_policy=data_policy or {},
            render=render or {},
        )
        return self.register(entry)

    def register_callable(
        self,
        uri: str,
        kind: str,
        name: str,
        func: Callable[..., Any],
        description: str = "",
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        permissions: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0",
        data_policy: Optional[Dict[str, Any]] = None,
        render: Optional[Dict[str, Any]] = None,
    ) -> RegistryEntry:
        entry = RegistryEntry(
            uri=uri,
            kind=kind,
            name=name,
            description=description,
            callable_ref=func,
            input_schema=input_schema,
            output_schema=output_schema,
            permissions=permissions or {},
            tags=tags or [],
            aliases=aliases or [],
            metadata=metadata or {},
            version=version,
            data_policy=data_policy or {},
            render=render or {},
        )
        return self.register(entry)

    def get(self, uri: str) -> Optional[RegistryEntry]:
        canonical = self._aliases.get(uri, uri)
        return self._entries.get(canonical)

    def require(self, uri: str) -> RegistryEntry:
        entry = self.get(uri)
        if entry is None:
            raise RegistryError("Unknown registry URI: %s" % uri)
        return entry

    def list(self, kinds: Optional[Iterable[str]] = None) -> List[RegistryEntry]:
        if kinds is None:
            return list(self._entries.values())
        allowed = set(kinds)
        return [entry for entry in self._entries.values() if entry.kind in allowed]

    def discover_for_llm(self) -> List[Dict[str, Any]]:
        return [
            entry.to_dict()
            for entry in self.list()
            if bool(entry.permissions.get("llm_discover"))
        ]

    def manifest(self) -> Dict[str, Any]:
        return {
            "manifest_version": TRM_VERSION,
            "schema_version": "2020-12",
            "schemas": {
                "resource_manifest": registry_manifest_schema(),
                "service_result": service_result_schema(),
            },
            "resources": [entry.to_dict() for entry in self.list()],
        }

    def check_permission(self, entry: RegistryEntry, action: str, confirmed: bool = False) -> None:
        key = {
            "discover": "llm_discover",
            "read": "llm_read",
            "write": "llm_write",
            "execute": "llm_execute",
        }.get(action)
        if not key:
            raise RegistryPermissionError("Unknown registry action: %s" % action)
        if not bool(entry.permissions.get(key)):
            raise RegistryPermissionError("Permission denied for %s on %s" % (action, entry.uri))
        if action == "execute" and entry.permissions.get("requires_confirmation") and not confirmed:
            raise RegistryPermissionError("Execution requires confirmation for %s" % entry.uri)

    def resolve(self, uri: str) -> Dict[str, Any]:
        entry = self.require(uri)
        return entry.to_dict(include_private=True)

    def read(self, uri: str) -> Any:
        entry = self.require(uri)
        self.check_permission(entry, "read")
        value = entry.value_ref() if callable(entry.value_ref) else entry.value_ref
        validate_schema(entry.value_schema, value)
        if entry.masked:
            return {"exists": value is not None, "masked": True}
        return value

    def execute(self, uri: str, payload: Optional[Dict[str, Any]] = None, confirmed: bool = False) -> Any:
        entry = self.require(uri)
        if entry.kind not in EXECUTABLE_KINDS:
            raise RegistryError("URI is not executable: %s" % uri)
        if entry.callable_ref is None:
            raise RegistryError("URI has no callable: %s" % uri)
        self.check_permission(entry, "execute", confirmed=confirmed)

        data = payload or {}
        if not isinstance(data, dict):
            raise RegistryValidationError("Execution input must be an object")
        validate_schema(entry.input_schema, data)

        result = self._call(entry.callable_ref, data)
        validate_schema(entry.output_schema, result)
        return result

    @staticmethod
    def _call(func: Callable[..., Any], payload: Dict[str, Any]) -> Any:
        try:
            signature = inspect.signature(func)
            params = list(signature.parameters.values())
            if len(params) == 0:
                return func()
            if len(params) == 1:
                return func(payload)
        except (TypeError, ValueError):
            pass
        return func(**payload)
