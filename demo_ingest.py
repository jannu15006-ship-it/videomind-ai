"""Interactive CLI demonstration script for VideoMind-AI stream & video ingestion.

Usage:
    python demo_ingest.py                          # Ingests a synthetic sample video
    python demo_ingest.py --source "https://..."   # Ingests a web/YouTube video
    python demo_ingest.py --source "path/to.mp4"   # Ingests a local file
"""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from configs.settings import settings
from src.ingestion.ffmpeg_utils import get_ffmpeg_binary
from src.ingestion.pipeline import IngestionPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("demo_ingest")


def generate_sample_clip() -> Path:
    """Create a 3-second sample test video with audio for instant local testing."""
    sample_path = settings.raw_video_dir / "sample_clip.mp4"
    if sample_path.exists():
        return sample_path

    logger.info("Generating synthetic 3-second test clip at: %s", sample_path)
    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [
        ffmpeg_bin,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=3:size=640x360:rate=24",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:duration=3",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-pix_fmt",
        "yuv420p",
        str(sample_path),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return sample_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="VideoMind-AI: Video & Audio Stream Ingestion Demo"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="YouTube URL, Web stream URL, or local video path. If omitted, generates a sample clip.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Force re-downloading and re-extracting audio.",
    )
    args = parser.parse_args()

    source = args.source
    if not source:
        logger.info("No source provided; creating a sample test video...")
        source = str(generate_sample_clip())

    print("\n" + "=" * 60)
    print("🎥 VideoMind-AI: Day 2 Ingestion Pipeline Demo")
    print("=" * 60)
    print(f"Target Source: {source}\n")

    pipeline = IngestionPipeline()
    metadata = pipeline.process(source, overwrite=args.overwrite)

    print("\n" + "=" * 60)
    print("✅ Ingestion Successful! Extracted Media Metadata:")
    print("=" * 60)
    summary = {
        "video_id": metadata.video_id,
        "title": metadata.title,
        "duration_seconds": f"{metadata.duration_seconds}s",
        "source_type": metadata.source_type.value,
        "source_uri": metadata.source_uri,
        "video_path": str(metadata.video_path),
        "audio_path": str(metadata.audio_path),
        "resolution": f"{metadata.width}x{metadata.height}" if metadata.width else "N/A",
        "fps": metadata.fps,
        "file_size_kb": f"{(metadata.file_size_bytes or 0) / 1024:.1f} KB",
    }
    print(json.dumps(summary, indent=2))
    print("\n🎧 Audio is normalized to 16kHz Mono WAV, ready for Whisper Speech-to-Text (Day 3)!\n")


if __name__ == "__main__":
    main()
