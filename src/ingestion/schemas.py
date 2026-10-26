"""Pydantic v2 Schemas for Media Ingestion and Metadata Tracking."""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MediaSourceType(str, Enum):
    """Categorization of media ingestion sources."""

    YOUTUBE = "youtube"
    LOCAL_FILE = "local_file"
    WEB_STREAM = "web_stream"


class MediaMetadata(BaseModel):
    """Normalized metadata representing an ingested audio/video entity."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    video_id: str = Field(
        ...,
        description="Unique identifier for the video (e.g. YouTube ID or local file hash).",
    )
    title: str = Field(
        ...,
        description="Human-readable title or file name.",
    )
    duration_seconds: float = Field(
        ...,
        ge=0.0,
        description="Total duration of the media file in seconds.",
    )
    source_type: MediaSourceType = Field(
        ...,
        description="Source of the media: YouTube, local file, or direct web stream.",
    )
    source_uri: str = Field(
        ...,
        description="Original URL or source file path.",
    )
    video_path: Optional[Path] = Field(
        default=None,
        description="Local filesystem path to the saved/cached video file.",
    )
    audio_path: Optional[Path] = Field(
        default=None,
        description="Local filesystem path to the extracted 16kHz mono WAV audio file.",
    )
    fps: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Frames per second of the video stream.",
    )
    width: Optional[int] = Field(
        default=None,
        gt=0,
        description="Width in pixels.",
    )
    height: Optional[int] = Field(
        default=None,
        gt=0,
        description="Height in pixels.",
    )
    file_size_bytes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Raw video file size in bytes.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of media ingestion.",
    )
