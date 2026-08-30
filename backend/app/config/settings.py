from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Gemini LLM Settings
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"

    # STT & TTS Settings
    DEEPGRAM_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""

    # Weather Settings
    OPENWEATHER_API_KEY: str = ""

    # SQLite Async Database URL
    DATABASE_URL: str = "sqlite+aiosqlite:///./aura.db"

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None, env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
