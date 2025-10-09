from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    user_name: str = Field(alias="USER_NAME")
    user_password: str = Field(alias="USER_PASSWORD")

    mongo_uri: str = Field(alias="mongo_uri")
    mongo_db_name: str = Field(alias="MONGO_DB_NAME")
    request_timeout: int = Field(alias="REQUEST_TIMEOUT")

    ana_api_url: str = Field(alias="ANA_API_URL")
    ana_api_inventario_url: str = Field(alias="ANA_API_INVENTARIO_URL")
    ana_identificador: str = Field(alias="ANA_IDENTIFICADOR")
    ana_senha: str = Field(alias="ANA_SENHA")

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()