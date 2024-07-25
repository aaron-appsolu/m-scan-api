from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


@lru_cache
def get_settings():
    return Settings()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    PROD: bool
    SECRET: str
    MONGODB: str
    NEO4J: str
    GRAPHAUTH: str
    MEMGRAPH: str

