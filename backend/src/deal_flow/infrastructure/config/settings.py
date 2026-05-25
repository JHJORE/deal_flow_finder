import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_backend_root() -> Path:
    """Locate the backend dir that contains firms.yaml and data/.

    Local dev keeps source and data files together under backend/, but Vercel
    pip-installs the package into site-packages — separate from the bundled
    firms.yaml and data/ files. A fixed parents[N] climb only works in one of
    those layouts. We try several strategies, anchored on firms.yaml.
    """
    if env := os.environ.get("BACKEND_ROOT"):
        return Path(env)
    cwd = Path.cwd()
    if (cwd / "firms.yaml").exists():
        return cwd
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "firms.yaml").exists():
            return parent
    return Path(__file__).resolve().parents[4]


_BACKEND_ROOT = _find_backend_root()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"

    database_url: str = ""

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
