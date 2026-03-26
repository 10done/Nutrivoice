from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "NutriVoice API"
    database_url: str = "sqlite:///./nutrivoice.db"

    @field_validator("database_url", mode="before")
    @classmethod
    def postgres_driver_for_sqlalchemy(cls, v: object) -> object:
        """Railway/Render often set postgresql://… without a driver; SQLAlchemy needs +psycopg."""
        if not isinstance(v, str) or v.startswith("sqlite"):
            return v
        scheme = v.split("://", 1)[0]
        if "psycopg" in scheme:
            return v
        if scheme in ("postgres", "postgresql"):
            return "postgresql+psycopg://" + v.split("://", 1)[1]
        return v
    jwt_secret: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    #: Groq LLM for turning transcript → structured meal JSON (when MOCK_AI is false).
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    #: Google Web Speech API via SpeechRecognition (requires network). For WebM/MP4, ffmpeg must be installed for pydub.
    speech_recognition_language: str = "en-US"

    #: Skip real STT and return mock_whisper_text (tests / no mic pipeline).
    mock_whisper: bool = False
    #: Rule-based meal parser instead of Groq.
    mock_ai: bool = False
    mock_whisper_text: str = "I had two boiled eggs and a cup of black coffee for breakfast."


def get_settings() -> Settings:
    return Settings()
