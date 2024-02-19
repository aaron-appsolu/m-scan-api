from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


@lru_cache
def get_settings():
    return Settings()


class Settings(BaseSettings):
    PROD: bool
    SECRET: str
    MONGODB: str
    NEO4J: str
    NEO4JAUTH: str
    MEMGRAPH: str
    MEMGRAPHAUTH: str

    model_config = SettingsConfigDict(env_file=".env")
