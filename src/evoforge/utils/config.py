import os
from pathlib import Path

import yaml
from pydantic import BaseModel


class GlobalConfig(BaseModel):
    max_daily_api_cost_usd: float = 5.00
    max_prs_per_day: int = 10
    max_retries_per_task: int = 3
    require_tests_pass: bool = True
    require_security_scan: bool = True
    never_auto_merge: bool = True
    never_auto_deploy: bool = True

class DatabaseConfig(BaseModel):
    sqlite_path: str = "data/evoforge.db"

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"

class LearningConfig(BaseModel):
    enabled: bool = True
    research_budget_usd: float = 1.00
    max_research_per_day: int = 5
    auto_deploy_threshold: float = 0.05  # 5% improvement
    auto_deploy_confidence: float = 0.85
    high_volatility_interval_days: int = 7
    medium_volatility_interval_days: int = 14
    low_volatility_interval_days: int = 30
    sandbox_path: str = "data/sandbox"

class OllamaConfig(BaseModel):
    enabled: bool = True
    endpoint: str = "http://localhost:11434"
    default_model: str = "qwen2.5-coder:7b-instruct-q4_K_M"
    timeout_seconds: float = 60.0

class GeminiConfig(BaseModel):
    enabled: bool = True
    default_model: str = "gemini/gemini-2.5-flash"
    timeout_seconds: float = 60.0

class NvidiaConfig(BaseModel):
    enabled: bool = True
    endpoint: str = "https://integrate.api.nvidia.com/v1"
    default_model: str = "deepseek-ai/deepseek-coder-33b-instruct"
    timeout_seconds: float = 60.0

class AntigravityConfig(BaseModel):
    enabled: bool = False
    endpoint: str | None = None
    timeout_seconds: float = 120.0

class ProvidersConfig(BaseModel):
    ollama: OllamaConfig = OllamaConfig()
    gemini: GeminiConfig = GeminiConfig()
    nvidia: NvidiaConfig = NvidiaConfig()
    antigravity: AntigravityConfig = AntigravityConfig()

class AppConfig(BaseModel):
    global_settings: GlobalConfig = GlobalConfig()
    database: DatabaseConfig = DatabaseConfig()
    logging: LoggingConfig = LoggingConfig()
    learning: LearningConfig = LearningConfig()
    providers: ProvidersConfig = ProvidersConfig()

def load_config(config_path: str = "config/default.yaml") -> AppConfig:
    """Loads configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        return AppConfig() # Default config if not found
    
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    
    if not data:
        return AppConfig()
    
    global_cfg = GlobalConfig(**data.get("global", {}))
    db_cfg = DatabaseConfig(**data.get("database", {}))
    log_cfg = LoggingConfig(**data.get("logging", {}))
    learning_cfg = LearningConfig(**data.get("learning", {}))
    
    prov_data = data.get("providers", {})
    providers_cfg = ProvidersConfig(
        ollama=OllamaConfig(**prov_data.get("ollama", {})),
        gemini=GeminiConfig(**prov_data.get("gemini", {})),
        nvidia=NvidiaConfig(**prov_data.get("nvidia", {})),
        antigravity=AntigravityConfig(**prov_data.get("antigravity", {})),
    )
    
    # Allow environment variables to override DB path for testing
    if "EVOFORGE_DATA_DIR" in os.environ:
        db_cfg.sqlite_path = os.path.join(os.environ["EVOFORGE_DATA_DIR"], "evoforge.db")
        
    return AppConfig(
        global_settings=global_cfg,
        database=db_cfg,
        logging=log_cfg,
        learning=learning_cfg,
        providers=providers_cfg,
    )

