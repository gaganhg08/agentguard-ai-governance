import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "AgentGuard – AI Agent Security & Governance Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_PATH: Path = BASE_DIR / "agentguard.db"
    DATABASE_URL: str = f"sqlite:///{DATABASE_PATH}"
    
    # Sensitive Thresholds
    PAYMENT_APPROVAL_THRESHOLD: float = 500.0
    REFUND_APPROVAL_THRESHOLD: float = 100.0
    
    # Sensitive tools that always require human approval
    SENSITIVE_TOOLS: set[str] = {
        "modify_firewall",
        "restart_service",
        "reset_password",
        "update_ledger",
        "execute_terminal_command",
        "delete_user_data",
        "grant_admin_privileges"
    }

    # Prompt injection patterns
    INJECTION_KEYWORDS: list[str] = [
        "ignore previous instructions",
        "disregard all previous",
        "override system",
        "you are now bypass_mode",
        "jailbreak",
        "drop table",
        "exec(",
        "eval(",
        "__import__",
        "rm -rf",
        ";--",
        "system:override"
    ]

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
