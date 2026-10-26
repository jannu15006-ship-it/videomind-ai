"""Unit and integration tests for the VideoMind-AI Ingestion Module."""

import os
import subprocess
import wave
from pathlib import Path
import pytest

from configs.settings import settings
from src.ingestion.exceptions import (
    AudioExtractionError,
    InvalidMediaSourceError,
)
from src.ingestion.extractor import AudioExtractor
from src.ingestion.ffmpeg_utils import (
    extract_audio_to_wav,
    get_ffmpeg_binary,
    probe_media_file,
)
from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.schemas import MediaMetadata, MediaSourceType


@pytest.fixture(scope="session")
def sample_video_with_audio(tmp_path_factory) -> Path:
    """Generate a lightweight synthetic 2-second MP4 test video with audio using FFmpeg."""
    temp_dir = tmp_path_factory.mktemp("test_media")
    video_path = temp_dir / "synthetic_test.mp4"

    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [
        ffmpeg_bin,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=2:size=320x240:rate=15",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=1000:duration=2",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-pix_fmt",
        "yuv420p",
        str(video_path),
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0, f"Failed to generate synthetic video: {result.stderr}"
    assert video_path.exists() and video_path.stat().st_size > 0
    return video_path


def test_ffmpeg_binary_discovery():
    """Verify that FFmpeg binary is located and executable."""
    binary_path = get_ffmpeg_binary()
    assert binary_path is not None
    assert os.path.exists(binary_path)


def test_probe_media_file(sample_video_with_audio: Path):
    """Verify that media probing extracts duration, fps, dimensions, and audio stream."""
    info = probe_media_file(sample_video_with_audio)
    assert info["duration"] >= 1.9
    assert info["width"] == 320
    assert info["height"] == 240
    assert info["fps"] == 15.0
    assert info["has_audio"] is True
    assert info["file_size_bytes"] > 0


def test_audio_extraction(sample_video_with_audio: Path, tmp_path: Path):
    """Verify extraction to standard 16kHz mono 16-bit WAV audio."""
    out_wav = tmp_path / "extracted_16k.wav"

    result_path = extract_audio_to_wav(
        video_path=sample_video_with_audio,
        output_wav_path=out_wav,
        sample_rate=16000,
        channels=1,
    )

    assert result_path.exists()
    assert result_path.stat().st_size > 0

    # Inspect WAV header properties using Python's built-in wave module
    with wave.open(str(result_path), "rb") as wf:
        assert wf.getnchannels() == 1  # Mono
        assert wf.getframerate() == 16000  # 16kHz
        assert wf.getsampwidth() == 2  # 16-bit PCM


def test_audio_extractor_caching(sample_video_with_audio: Path, tmp_path: Path):
    """Verify that AudioExtractor reuses cached WAV when overwrite=False."""
    extractor = AudioExtractor(output_dir=tmp_path)
    wav_1 = extractor.extract(sample_video_with_audio, video_id="cache_test")
    mtime_1 = wav_1.stat().st_mtime

    # Second extraction without overwrite should reuse existing cache
    wav_2 = extractor.extract(sample_video_with_audio, video_id="cache_test", overwrite=False)
    mtime_2 = wav_2.stat().st_mtime

    assert wav_1 == wav_2
    assert mtime_1 == mtime_2


def test_ingestion_pipeline_local_file(sample_video_with_audio: Path, tmp_path: Path):
    """Verify end-to-end ingestion of a local video file."""
    downloader_dir = tmp_path / "raw"
    audio_dir = tmp_path / "audio"
    pipeline = IngestionPipeline(
        extractor=AudioExtractor(output_dir=audio_dir),
    )

    metadata: MediaMetadata = pipeline.process(sample_video_with_audio)

    assert metadata.video_id is not None
    assert metadata.source_type == MediaSourceType.LOCAL_FILE
    assert metadata.duration_seconds >= 1.9
    assert metadata.video_path is not None and metadata.video_path.exists()
    assert metadata.audio_path is not None and metadata.audio_path.exists()
    assert metadata.audio_path.suffix == ".wav"


def test_invalid_local_file():
    """Verify that non-existent media raises InvalidMediaSourceError."""
    pipeline = IngestionPipeline()
    with pytest.raises(InvalidMediaSourceError):
        pipeline.process("non_existent_video_path.mp4")


def test_unsupported_file_extension(tmp_path: Path):
    """Verify that unsupported file extensions are rejected."""
    bad_file = tmp_path / "document.pdf"
    bad_file.write_text("dummy text")

    pipeline = IngestionPipeline()
    with pytest.raises(InvalidMediaSourceError):
        pipeline.process(bad_file)


def test_video_downloader_mocked(tmp_path: Path, monkeypatch):
    """Verify VideoDownloader pipeline logic with mocked yt-dlp response."""
    from unittest.mock import MagicMock
    from src.ingestion.downloader import VideoDownloader

    fake_video = tmp_path / "mock_vid.mp4"
    fake_video.write_bytes(b"mock video data")

    downloader = VideoDownloader(output_dir=tmp_path)

    # Mock YoutubeDL context manager
    mock_ydl = MagicMock()
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {
        "id": "mock_vid",
        "title": "Mock Video Title",
        "duration": 42.5,
        "extractor_key": "Youtube",
        "fps": 30,
        "width": 1280,
        "height": 720,
    }

    monkeypatch.setattr("yt_dlp.YoutubeDL", MagicMock(return_value=mock_ydl))

    metadata = downloader.download("https://www.youtube.com/watch?v=mock123")

    assert metadata.video_id == "mock_vid"
    assert metadata.title == "Mock Video Title"
    assert metadata.duration_seconds == 42.5
    assert metadata.source_type == MediaSourceType.YOUTUBE
    assert metadata.video_path == fake_video

