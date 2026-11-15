from typing import ClassVar

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", extra="ignore"
    )

    api_key: SecretStr
    public_base_url: str = "http://localhost:8000"
    max_file_size_bytes: int = 10 * 1024 * 1024
    issuer: str = "in-memory-issuer"
