from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
from os import getenv

if getenv("PROD") is None:
    load_dotenv()


@lru_cache
def get_settings():
    return Settings()


class Settings(BaseSettings):
    # model_config = SettingsConfigDict(env_file=".env")

    PROD: bool
    SECRET: str
    MONGODB: str
    NEO4J: str
    GRAPHAUTH: str
    MEMGRAPH: str
