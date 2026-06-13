import os
from dotenv import load_dotenv
from dataclasses import dataclass
load_dotenv()
@dataclass
class Config:
    openrouter_api_key: str
    llm_model: str
    host: str
    port: int
def load_config() -> Config:
    return Config(openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""), llm_model=os.getenv("LLM_MODEL", "openrouter/qwen/qwen3-coder-next"), host=os.getenv("HOST", "localhost"), port=int(os.getenv("PORT", "8000")))