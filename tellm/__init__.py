from .bot import TellmBot, Task, TaskType, ViewData
from .server import TellmServer
from .config import load_config
from .improvement import AutoimprovementRunner, ExecutionHistoryStore
from .registry import (
    JSON_SCHEMA_DRAFT_2020_12,
    RegistryEntry,
    ResourceRegistry,
    TRM_VERSION,
    TSR_VERSION,
    registry_manifest_schema,
    service_result,
    service_result_schema,
    validate_tellm_uri,
)
__version__ = "4.0.6"
def create_bot(db_path="tellm.db"): return TellmBot(db_path=db_path)
def run_server(host="localhost", port=8000, db_path="tellm.db"):
    server = TellmServer(host, port, db_path)
    server.run()
