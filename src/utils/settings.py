from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DB_CONNECTION: str = "sqlite:///./findnseekh.db"
    SECRET_KEY: str = "findnseekh-secret-key-development-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440


settings = Settings()
