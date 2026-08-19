from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================
    # Database
    # =========================
    database_url: str

    # =========================
    # Brevo Email Configuration
    # =========================
    brevo_api_key: str
    brevo_sender_email: str
    brevo_sender_name: str

    # =========================
    # Frontend
    # =========================
    frontend_url: str = "http://localhost:3000"

    # =========================
    # JWT Configuration
    # =========================
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    jwt_access_token_expire_minutes: int = 15

    jwt_refresh_token_expire_days: int = 7

    jwt_issuer: str = "legal-ai-api"

    jwt_audience: str = "legal-ai-client"

    # =========================
    # Account Lockout
    # =========================
    max_failed_login_attempts: int = 5

    account_lockout_minutes: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()