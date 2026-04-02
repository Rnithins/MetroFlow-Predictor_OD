from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MetroFlow Predictor API"
    api_prefix: str = "/api/v1"
    secret_key: str = "change-this-secret"
    access_token_expire_minutes: int = 180
    mongodb_uri: str = "mongomock://localhost"
    mongodb_database: str = "metroflow_predictor"
    cors_origins: str = "http://localhost:3000"
    model_version: str = "metroflow-baseline-regression-v2"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
