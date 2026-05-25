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

    twitterapi_io_key: str = ""
    twitterapi_cache_dir: Path = _BACKEND_ROOT / ".twitter"
    twitterapi_cache_refresh: bool = False

    apify_api_token: str = ""
    apify_cache_dir: Path = _BACKEND_ROOT / ".apify"
    apify_cache_refresh: bool = False
    apify_linkedin_actor_id: str = "harvestapi~linkedin-profile-posts"

    gemini_api_key: str = ""
    gemini_cache_dir: Path = _BACKEND_ROOT / ".gemini"
    gemini_cache_refresh: bool = False

    partner_data_dir: Path = _BACKEND_ROOT / "data"

    output_dir: Path = _BACKEND_ROOT / ".outputs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
