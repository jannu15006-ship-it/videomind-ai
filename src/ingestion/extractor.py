"""Audio extraction module: converts video streams to normalized 16kHz mono WAV audio."""

import logging
from pathlib import Path
from typing import Optional

from configs.settings import settings
from src.ingestion.exceptions import AudioExtractionError
from src.ingestion.ffmpeg_utils import extract_audio_to_wav

logger = logging.getLogger(__name__)


class AudioExtractor:
    """Production audio extractor tailored for speech-to-text engines (OpenAI Whisper).

    Extracts and resamples audio streams to standard 16,000 Hz, 1-channel (mono),
    16-bit PCM WAV. Pre-normalizing to this standard ensures Whisper runs at maximum
    speed with zero downstream resampling overhead.
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> None:
        """Initialize the audio extractor.

        Args:
            output_dir: Target cache directory for extracted .wav files.
            sample_rate: Audio sampling frequency in Hz (default: 16000).
            channels: Channel count (1 = mono, 2 = stereo). Default: 1.
        """
        self.output_dir = Path(output_dir or settings.audio_cache_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sample_rate = sample_rate
        self.channels = channels

    def extract(
        self,
        video_path: Path | str,
        video_id: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        """Extract and normalize audio from a given video file.

        Args:
            video_path: Path to the source video file (MP4, MKV, MOV, etc.).
            video_id: Unique identifier for naming the cached audio file.
                      If not provided, uses the video file stem.
            overwrite: If True, re-extracts audio even if cache exists.

        Returns:
            Path: Resolved path to the normalized 16kHz mono .wav file.

        Raises:
            AudioExtractionError: If file not found or extraction fails.
        """
        v_path = Path(video_path).resolve()
        if not v_path.is_file():
            raise AudioExtractionError(f"Video file not found: {v_path}")

        file_id = video_id or v_path.stem
        target_wav = self.output_dir / f"{file_id}.wav"

        # Check cache
        if target_wav.exists() and not overwrite and target_wav.stat().st_size > 0:
            logger.info("Found cached 16kHz WAV audio at: %s", target_wav)
            return target_wav

        logger.info(
            "Extracting audio from '%s' to normalized 16kHz WAV: %s",
            v_path.name,
            target_wav,
        )

        return extract_audio_to_wav(
            video_path=v_path,
            output_wav_path=target_wav,
            sample_rate=self.sample_rate,
            channels=self.channels,
            overwrite=overwrite,
        )
