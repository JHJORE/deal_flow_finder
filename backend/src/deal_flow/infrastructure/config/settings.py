from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"

    firecrawl_api_key: str = ""
    firecrawl_cache_dir: Path = _BACKEND_ROOT / ".firecrawl"
    firecrawl_cache_refresh: bool = False

    sec_user_agent: str = ""
    sec_cache_dir: Path = _BACKEND_ROOT / ".edgar"
    sec_cache_refresh: bool = False

    twitterapi_key: str = ""
    twitterapi_cache_dir: Path = _BACKEND_ROOT / ".twitter"
    twitterapi_cache_refresh: bool = False

    output_dir: Path = _BACKEND_ROOT / ".outputs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
