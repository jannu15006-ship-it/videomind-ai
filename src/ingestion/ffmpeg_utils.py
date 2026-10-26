"""Utility functions for FFmpeg binary location, media probing, and audio extraction."""

import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from src.ingestion.exceptions import AudioExtractionError, FFmpegNotFoundError

logger = logging.getLogger(__name__)


def get_ffmpeg_binary() -> str:
    """Locate the FFmpeg binary on the system.

    Prioritizes system PATH, falling back to the bundled imageio-ffmpeg binary.

    Returns:
        str: Absolute path or executable name for FFmpeg.

    Raises:
        FFmpegNotFoundError: If FFmpeg cannot be located.
    """
    # 1. Check system PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # 2. Check bundled imageio_ffmpeg
    try:
        import imageio_ffmpeg

        bundled_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled_ffmpeg and os.path.isfile(bundled_ffmpeg):
            return str(bundled_ffmpeg)
    except (ImportError, Exception) as exc:
        logger.debug("imageio_ffmpeg lookup failed: %s", exc)

    raise FFmpegNotFoundError(
        "FFmpeg binary not found on system PATH or in imageio-ffmpeg package. "
        "Please install FFmpeg or run: pip install imageio-ffmpeg"
    )


def probe_media_file(media_path: Path | str) -> Dict[str, Any]:
    """Probe media properties (duration, fps, resolution, audio presence) using FFmpeg.

    Runs `ffmpeg -i <file>` which outputs comprehensive container and stream
    metadata to standard error.

    Args:
        media_path: Path to the media file to probe.

    Returns:
        dict: Extracted properties including duration, width, height, fps, has_audio.
    """
    path = Path(media_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Media file not found: {path}")

    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [ffmpeg_bin, "-hide_banner", "-i", str(path)]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    info: Dict[str, Any] = {
        "duration": 0.0,
        "width": None,
        "height": None,
        "fps": None,
        "has_audio": False,
        "file_size_bytes": path.stat().st_size,
    }

    stderr_output = result.stderr

    # Duration parsing: "Duration: 00:01:23.45"
    duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", stderr_output)
    if duration_match:
        hours, minutes, seconds = duration_match.groups()
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        info["duration"] = round(total_seconds, 3)

    # Video stream parsing: e.g. "Stream #0:0: Video: ... 1920x1080 ... 30 fps"
    video_match = re.search(r"Stream #\d+:\d+.*?: Video:.*", stderr_output)
    if video_match:
        video_line = video_match.group(0)
        # Dimensions: 1920x1080
        dim_match = re.search(r"\b(\d{3,5})x(\d{3,5})\b", video_line)
        if dim_match:
            info["width"] = int(dim_match.group(1))
            info["height"] = int(dim_match.group(2))

        # FPS: "29.97 fps" or "30 fps"
        fps_match = re.search(r"(\d+(?:\.\d+)?)\s*fps", video_line)
        if fps_match:
            info["fps"] = float(fps_match.group(1))

    # Audio stream check: e.g. "Stream #0:1: Audio:"
    if re.search(r"Stream #\d+:\d+.*?: Audio:", stderr_output):
        info["has_audio"] = True

    return info


def extract_audio_to_wav(
    video_path: Path | str,
    output_wav_path: Path | str,
    sample_rate: int = 16000,
    channels: int = 1,
    overwrite: bool = True,
) -> Path:
    """Extract audio from a video file into a normalized 16kHz mono WAV format.

    This format matches OpenAI Whisper's native expected audio rate, eliminating
    downstream resampling overhead during transcription.

    Args:
        video_path: Source video file path.
        output_wav_path: Target path for the output .wav file.
        sample_rate: Audio sampling frequency in Hz (default: 16000).
        channels: Number of audio channels (1 = mono, 2 = stereo).
        overwrite: Overwrite destination file if it already exists.

    Returns:
        Path: Resolved path to the generated WAV file.

    Raises:
        AudioExtractionError: If FFmpeg fails or the file has no extractable audio.
    """
    v_path = Path(video_path).resolve()
    out_path = Path(output_wav_path).resolve()

    if not v_path.is_file():
        raise AudioExtractionError(f"Input video file not found: {v_path}")

    # Ensure parent output directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and not overwrite and out_path.stat().st_size > 0:
        logger.info("Using cached audio file: %s", out_path)
        return out_path

    ffmpeg_bin = get_ffmpeg_binary()

    # ffmpeg arguments:
    # -y: overwrite output
    # -i: input file
    # -vn: disable video recording (extract audio only)
    # -acodec pcm_s16le: 16-bit uncompressed PCM WAV
    # -ar: audio sampling rate (16000 Hz)
    # -ac: audio channels (1 = mono)
    cmd = [
        ffmpeg_bin,
        "-y" if overwrite else "-n",
        "-i",
        str(v_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
        str(out_path),
    ]

    logger.debug("Executing FFmpeg command: %s", " ".join(cmd))

    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if process.returncode != 0:
        error_msg = process.stderr.strip()
        logger.error("FFmpeg audio extraction failed: %s", error_msg)
        raise AudioExtractionError(
            f"Failed to extract audio from '{v_path.name}'.", details=error_msg
        )

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise AudioExtractionError(
            f"FFmpeg exited successfully but output audio file is empty or missing: {out_path}"
        )

    logger.info(
        "Successfully extracted 16kHz mono WAV audio (%d bytes) to %s",
        out_path.stat().st_size,
        out_path,
    )
    return out_path
