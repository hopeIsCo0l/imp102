from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EAA Recruit API"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 60 * 12
    database_url: str = "sqlite:///./eaa_recruit.db"
    redis_url: str = "redis://redis:6379/0"
    upload_dir: str = "uploads"
    export_dir: str = "exports"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
