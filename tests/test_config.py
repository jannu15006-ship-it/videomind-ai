"""Sanity test to verify application settings and directory resolution."""

from configs.settings import settings


def test_settings_load():
    """Verify that settings load with correct defaults."""
    assert settings.app_env in ["development", "production", "testing"]
    assert settings.api_port == 8000
    assert settings.whisper_model_size in ["tiny", "base", "small", "medium"]
    assert settings.device in ["cuda", "cpu"]


def test_paths_exist():
    """Verify that core data directories are resolved properly."""
    assert settings.chroma_persist_dir.name == "chroma_db"
    assert settings.audio_cache_dir.name == "audio_cache"
    assert settings.keyframe_cache_dir.name == "keyframes"
    assert settings.raw_video_dir.name == "raw_videos"


if __name__ == "__main__":
    test_settings_load()
    test_paths_exist()
    print("✅ All Day 1 configuration sanity tests passed successfully!")
