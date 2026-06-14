from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"

    database_url: str = "postgresql+asyncpg://exposureflow:exposureflow@localhost:5432/exposureflow"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me"
    encryption_key: str = "change-me-32-byte-key-in-production"

    serper_api_key: str | None = None
    serpapi_api_key: str | None = None


settings = Settings()
