"""Unified Ingestion Pipeline orchestrating video downloading and audio extraction."""

import hashlib
import logging
import re
import shutil
from pathlib import Path
from typing import Optional, Union

from configs.settings import settings
from src.ingestion.downloader import VideoDownloader
from src.ingestion.exceptions import (
    IngestionError,
    InvalidMediaSourceError,
)
from src.ingestion.extractor import AudioExtractor
from src.ingestion.ffmpeg_utils import probe_media_file
from src.ingestion.schemas import MediaMetadata, MediaSourceType

logger = logging.getLogger(__name__)

SUPPORTED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".webm",
    ".flv",
    ".wmv",
    ".m4v",
}


def _is_url(source: str) -> bool:
    """Check if the provided source string is a network URL."""
    return bool(re.match(r"^https?://", source.strip(), re.IGNORECASE))


def _compute_file_hash(file_path: Path, chunk_size: int = 65536) -> str:
    """Compute short SHA-256 fingerprint of a local media file for deduplication."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Hash first 4MB to keep hash calculation fast for multi-GB videos
        bytes_read = 0
        while bytes_read < 4 * 1024 * 1024:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
            bytes_read += len(chunk)
    return hasher.hexdigest()[:12]


class IngestionPipeline:
    """Enterprise ingestion orchestrator.

    Accepts online URLs (YouTube/web streams) or local media paths,
    downloads/caches video streams, probes metadata, and generates
    normalized 16kHz mono audio files ready for Whisper transcription.
    """

    def __init__(
        self,
        downloader: Optional[VideoDownloader] = None,
        extractor: Optional[AudioExtractor] = None,
    ) -> None:
        """Initialize the unified ingestion pipeline."""
        self.downloader = downloader or VideoDownloader()
        self.extractor = extractor or AudioExtractor()

    def process(
        self,
        source: Union[str, Path],
        custom_id: Optional[str] = None,
        overwrite: bool = False,
    ) -> MediaMetadata:
        """Process a media source into normalized video and audio assets.

        Args:
            source: YouTube/web URL or local video file path.
            custom_id: Optional custom identifier for the media.
            overwrite: Force re-download and re-extraction if cached.

        Returns:
            MediaMetadata: Complete metadata with paths to both video and 16kHz WAV audio.

        Raises:
            IngestionError: If download, validation, or extraction fails.
        """
        source_str = str(source).strip()

        if _is_url(source_str):
            return self._process_url(
                url=source_str, custom_id=custom_id, overwrite=overwrite
            )
        return self._process_local_file(
            file_path=Path(source_str), custom_id=custom_id, overwrite=overwrite
        )

    def _process_url(
        self,
        url: str,
        custom_id: Optional[str] = None,
        overwrite: bool = False,
    ) -> MediaMetadata:
        """Ingest a web or YouTube video stream."""
        logger.info("Processing remote stream URL: %s", url)

        # 1. Download video
        metadata = self.downloader.download(url, custom_video_id=custom_id)

        # 2. Extract 16kHz mono audio
        if metadata.video_path:
            audio_path = self.extractor.extract(
                video_path=metadata.video_path,
                video_id=metadata.video_id,
                overwrite=overwrite,
            )
            metadata.audio_path = audio_path

        return metadata

    def _process_local_file(
        self,
        file_path: Path,
        custom_id: Optional[str] = None,
        overwrite: bool = False,
    ) -> MediaMetadata:
        """Ingest a local video file, store in raw_videos cache, and extract audio."""
        resolved_path = file_path.resolve()
        if not resolved_path.is_file():
            raise InvalidMediaSourceError(
                f"Local media file does not exist: {resolved_path}"
            )

        if resolved_path.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
            raise InvalidMediaSourceError(
                f"Unsupported media extension '{resolved_path.suffix}'. "
                f"Supported: {sorted(SUPPORTED_VIDEO_EXTENSIONS)}"
            )

        # Generate deterministic video_id
        if custom_id:
            video_id = custom_id
        else:
            file_hash = _compute_file_hash(resolved_path)
            clean_stem = re.sub(r"[^\w\-]", "_", resolved_path.stem)[:24]
            video_id = f"{clean_stem}_{file_hash}"

        # Copy/store in raw_video_dir if not already there
        target_video_path = settings.raw_video_dir / f"{video_id}{resolved_path.suffix.lower()}"
        if not target_video_path.exists() or overwrite:
            if resolved_path != target_video_path:
                logger.info("Caching local video to: %s", target_video_path)
                shutil.copy2(resolved_path, target_video_path)
        actual_video_path = target_video_path if target_video_path.exists() else resolved_path

        # Probe metadata (duration, width, height, fps)
        probe_info = probe_media_file(actual_video_path)

        # Extract 16kHz mono audio
        audio_path = self.extractor.extract(
            video_path=actual_video_path,
            video_id=video_id,
            overwrite=overwrite,
        )

        metadata = MediaMetadata(
            video_id=video_id,
            title=resolved_path.stem.replace("_", " ").title(),
            duration_seconds=probe_info["duration"],
            source_type=MediaSourceType.LOCAL_FILE,
            source_uri=str(resolved_path),
            video_path=actual_video_path,
            audio_path=audio_path,
            fps=probe_info.get("fps"),
            width=probe_info.get("width"),
            height=probe_info.get("height"),
            file_size_bytes=probe_info.get("file_size_bytes"),
        )

        logger.info(
            "Local video successfully ingested: %s (Duration: %.2fs)",
            metadata.video_id,
            metadata.duration_seconds,
        )
        return metadata
