"""VideoMind-AI Ingestion Module.

Provides stream downloading (yt-dlp), audio extraction (FFmpeg 16kHz mono WAV),
and metadata schemas for end-to-end multimodal ingestion.
"""

from src.ingestion.downloader import VideoDownloader
from src.ingestion.exceptions import (
    AudioExtractionError,
    FFmpegNotFoundError,
    IngestionError,
    InvalidMediaSourceError,
    MediaDownloadError,
)
from src.ingestion.extractor import AudioExtractor
from src.ingestion.ffmpeg_utils import (
    extract_audio_to_wav,
    get_ffmpeg_binary,
    probe_media_file,
)
from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.schemas import MediaMetadata, MediaSourceType

__all__ = [
    "VideoDownloader",
    "AudioExtractor",
    "IngestionPipeline",
    "MediaMetadata",
    "MediaSourceType",
    "get_ffmpeg_binary",
    "extract_audio_to_wav",
    "probe_media_file",
    "IngestionError",
    "MediaDownloadError",
    "AudioExtractionError",
    "InvalidMediaSourceError",
    "FFmpegNotFoundError",
]
