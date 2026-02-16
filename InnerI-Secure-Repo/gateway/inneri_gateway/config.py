from pydantic import BaseModel
import os

class Settings(BaseModel):
    db_dsn: str = os.getenv("INNERI_DB_DSN", "postgresql+psycopg://inneri:inneri@localhost:5432/inneri")
    opa_url: str = os.getenv("INNERI_OPA_URL", "http://localhost:8181")
    receipt_signing_key: str = os.getenv("INNERI_RECEIPT_SIGNING_KEY", "dev_only_change_me")
    jwt_signing_key: str = os.getenv("INNERI_JWT_SIGNING_KEY", "dev_jwt_change_me")
    vault_addr: str = os.getenv("INNERI_VAULT_ADDR", "http://localhost:8200")
    vault_token: str = os.getenv("INNERI_VAULT_TOKEN", "")
    fail_open: bool = os.getenv("INNERI_FAIL_OPEN", "false").lower() == "true"
    log_level: str = os.getenv("INNERI_LOG_LEVEL", "info")

settings = Settings()
