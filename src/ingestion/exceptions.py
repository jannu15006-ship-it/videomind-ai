"""Custom Exception Classes for the VideoMind-AI Ingestion Module.

Ensures clear error classification across network, decoding, and I/O failures.
"""


class IngestionError(Exception):
    """Base exception for all ingestion-related failures."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class MediaDownloadError(IngestionError):
    """Raised when video stream downloading fails via yt-dlp."""

    pass


class AudioExtractionError(IngestionError):
    """Raised when FFmpeg fails to extract or re-sample audio."""

    pass


class InvalidMediaSourceError(IngestionError):
    """Raised when the specified media URL or file path is invalid or unreadable."""

    pass


class FFmpegNotFoundError(IngestionError):
    """Raised when no compatible FFmpeg binary is discovered on the system."""

    pass
