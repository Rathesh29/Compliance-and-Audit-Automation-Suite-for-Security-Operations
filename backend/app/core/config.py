import json
import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Compliance and Audit Automation Suite for Security Operations"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/security_compliance"
    DATABASE_URL_SQLITE_FALLBACK: bool = True
    SQLITE_FALLBACK_URL: str = "sqlite:///./security_compliance.db"

    # Security & Auth
    JWT_SECRET_KEY: str = "compliance_and_audit_super_secret_jwt_key_2026_operations_suite!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]

    # Notifications
    NOTIFICATION_PROVIDER: str = "console"  # 'console', 'log', 'smtp_mock'

    # Scheduler
    MISSED_SHIFT_CHECK_INTERVAL_SECONDS: int = 30

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
