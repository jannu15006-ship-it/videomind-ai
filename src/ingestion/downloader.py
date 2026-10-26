"""Video stream downloader using yt-dlp for YouTube and web video ingestion."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yt_dlp

from configs.settings import settings
from src.ingestion.exceptions import MediaDownloadError
from src.ingestion.ffmpeg_utils import get_ffmpeg_binary
from src.ingestion.schemas import MediaMetadata, MediaSourceType

logger = logging.getLogger(__name__)


class VideoDownloader:
    """Production downloader for YouTube streams and web video URLs using yt-dlp."""

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        max_height: int = 1080,
    ) -> None:
        """Initialize the video downloader.

        Args:
            output_dir: Target directory to save raw downloaded videos.
            max_height: Maximum vertical resolution to download (caps at 1080p to prevent bloat).
        """
        self.output_dir = Path(output_dir or settings.raw_video_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_height = max_height

    def extract_info(self, url: str) -> Dict[str, Any]:
        """Fetch video metadata without downloading the media payload.

        Args:
            url: Web video or YouTube URL.

        Returns:
            dict: Raw metadata dictionary from yt-dlp.

        Raises:
            MediaDownloadError: If extraction fails or URL is invalid.
        """
        ydl_opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise MediaDownloadError(f"No metadata returned for URL: {url}")
                return info
        except Exception as exc:
            logger.error("Failed to extract info from URL %s: %s", url, exc)
            raise MediaDownloadError(f"Failed to fetch metadata for URL: {url}", details=str(exc))

    def download(self, url: str, custom_video_id: Optional[str] = None) -> MediaMetadata:
        """Download video stream and return structured MediaMetadata.

        Args:
            url: YouTube video URL or supported web stream URL.
            custom_video_id: Optional identifier; defaults to yt-dlp's native video id.

        Returns:
            MediaMetadata: Validated media model with video file path and stream specs.

        Raises:
            MediaDownloadError: If download fails or file is corrupt.
        """
        ffmpeg_bin = get_ffmpeg_binary()

        # yt-dlp format selection:
        # Prioritizes mp4 with audio merged, capped at max_height
        format_spec = (
            f"bestvideo[height<={self.max_height}][ext=mp4]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={self.max_height}]+bestaudio/"
            f"best[height<={self.max_height}]/best"
        )

        template_filename = (
            f"{custom_video_id}.%(ext)s" if custom_video_id else "%(id)s.%(ext)s"
        )
        outtmpl = str(self.output_dir / template_filename)

        ydl_opts: Dict[str, Any] = {
            "format": format_spec,
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "ffmpeg_location": ffmpeg_bin,
            "quiet": False,
            "no_warnings": False,
            "overwrites": True,
        }

        logger.info("Starting stream download for URL: %s", url)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise MediaDownloadError(f"Failed to download video from: {url}")

                video_id = custom_video_id or str(info.get("id", "video"))
                title = info.get("title", f"Video {video_id}")
                duration = float(info.get("duration") or 0.0)

                # Determine downloaded video path
                expected_mp4 = self.output_dir / f"{video_id}.mp4"
                if expected_mp4.is_file():
                    actual_path = expected_mp4
                else:
                    # Search matching prefix in output_dir
                    matching = list(self.output_dir.glob(f"{video_id}.*"))
                    if not matching:
                        raise MediaDownloadError(
                            f"Downloaded file for video '{video_id}' could not be located in {self.output_dir}"
                        )
                    actual_path = matching[0]

                # Identify source type
                extractor_key = str(info.get("extractor_key", "")).lower()
                source_type = (
                    MediaSourceType.YOUTUBE
                    if "youtube" in extractor_key or "youtu" in url
                    else MediaSourceType.WEB_STREAM
                )

                file_size = actual_path.stat().st_size if actual_path.exists() else None

                metadata = MediaMetadata(
                    video_id=video_id,
                    title=title,
                    duration_seconds=duration,
                    source_type=source_type,
                    source_uri=url,
                    video_path=actual_path,
                    audio_path=None,  # Populated downstream by AudioExtractor
                    fps=info.get("fps"),
                    width=info.get("width"),
                    height=info.get("height"),
                    file_size_bytes=file_size,
                )

                logger.info(
                    "Download complete: '%s' (%s, %.1fs, %s bytes)",
                    metadata.title,
                    metadata.video_id,
                    metadata.duration_seconds,
                    metadata.file_size_bytes,
                )
                return metadata

        except Exception as exc:
            if isinstance(exc, MediaDownloadError):
                raise
            logger.error("Download failed for URL %s: %s", url, exc)
            raise MediaDownloadError(
                f"Error downloading stream from {url}", details=str(exc)
            ) from exc
