"""Application Configuration Module.

Uses Pydantic BaseSettings to enforce type safety, provide defaults,
and load environment variables cleanly from .env.
"""

from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project Root Directory: D:\24L31A5485\ML\videomind-ai
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Centralized application configuration settings."""

    # Server Configuration
    app_env: Literal["development", "production", "testing"] = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    log_level: str = "INFO"

    # AI Model Configuration
    whisper_model_size: str = Field(
        default="base",
        description="Whisper model tier: tiny, base, small, medium. Small/base fits 6GB VRAM comfortably.",
    )
    clip_model_name: str = "openai/clip-vit-base-patch32"
    reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    device: Literal["cuda", "cpu"] = "cuda"

    # Paths & Storage
    chroma_persist_dir: Path = PROJECT_ROOT / "data" / "chroma_db"
    audio_cache_dir: Path = PROJECT_ROOT / "data" / "audio_cache"
    keyframe_cache_dir: Path = PROJECT_ROOT / "data" / "keyframes"
    raw_video_dir: Path = PROJECT_ROOT / "data" / "raw_videos"

    # LLM Settings
    gemini_api_key: str = Field(
        default="",
        description="Optional API key for Gemini LLM synthesis.",
    )

    # Configuration for Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Global singleton instance for clean imports throughout the app:
# Usage: from configs.settings import settings
settings = Settings()
