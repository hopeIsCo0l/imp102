from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EAA Recruit API"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 60 * 12
    database_url: str = "postgresql+psycopg://eaa_user:eaa_pass@postgres:5432/eaa_recruit"
    redis_url: str = "redis://redis:6379/0"
    upload_dir: str = "uploads"
    export_dir: str = "exports"
    cors_allow_origins: str = "http://localhost:28080,http://localhost:5173"
    cors_allow_origin_regex: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


settings = Settings()
