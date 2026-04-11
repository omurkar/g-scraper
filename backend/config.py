"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend directory
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


class Settings:
    """Application settings."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./leadscout.db")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MAX_RESULTS: int = int(os.getenv("MAX_RESULTS_PER_SEARCH", "30"))
    SCRAPE_DELAY_MIN: float = float(os.getenv("SCRAPE_DELAY_MIN", "2.0"))
    SCRAPE_DELAY_MAX: float = float(os.getenv("SCRAPE_DELAY_MAX", "4.0"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL


settings = Settings()
