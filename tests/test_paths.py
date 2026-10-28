from pathlib import Path

from src import paths
from src.store import (
    infer_metadata_from_name,
    read_transcript_metadata,
    transcript_filename,
    write_transcript_metadata,
)


def test_default_paths_are_anchored_to_project_root(tmp_path, monkeypatch):
    project_root = Path(__file__).resolve().parent.parent

    monkeypatch.chdir(tmp_path)

    assert paths.get_transcripts_dir() == project_root / "transcripts"
    assert paths.get_chunks_dir() == project_root / "chunks"
    assert paths.PROJECT_ROOT == project_root


def test_explicit_paths_are_honoured(tmp_path):
    transcripts = tmp_path / "custom-transcripts"
    chunks = tmp_path / "custom-chunks"

    assert paths.get_transcripts_dir(transcripts) == transcripts.resolve()
    assert paths.get_chunks_dir(chunks) == chunks.resolve()


def test_environment_override(tmp_path, monkeypatch):
    monkeypatch.setenv("YOUTUBE_RAG_TRANSCRIPTS_DIR", str(tmp_path / "t"))
    monkeypatch.setenv("YOUTUBE_RAG_CHUNKS_DIR", str(tmp_path / "c"))

    assert paths.get_transcripts_dir() == (tmp_path / "t").resolve()
    assert paths.get_chunks_dir() == (tmp_path / "c").resolve()


def test_transcript_filename_uses_video_id():
    first = transcript_filename("abcdefghijk", "First title")
    second = transcript_filename("abcdefghijk", "Completely different title")
    other_video = transcript_filename("zyxwvutsrqp", "First title")

    assert first == "abcdefghijk.txt"
    assert second == first
    assert other_video != first


def test_metadata_sidecar_round_trip(tmp_path):
    transcript = tmp_path / "abcdefghijk.txt"
    transcript.write_text("hello", encoding="utf-8")

    write_transcript_metadata(
        transcript,
        {"video_id": "abcdefghijk", "video_title": "Real title"},
    )

    metadata = read_transcript_metadata(transcript)
    assert metadata["video_id"] == "abcdefghijk"
    assert metadata["video_title"] == "Real title"


def test_metadata_inference_for_legacy_and_new_names():
    assert infer_metadata_from_name("abcdefghijk.txt") == {
        "video_id": "abcdefghijk",
        "video_title": "abcdefghijk",
    }
    assert infer_metadata_from_name("abcdefghijk__My_Title.txt") == {
        "video_id": "abcdefghijk",
        "video_title": "My_Title",
    }
    legacy = infer_metadata_from_name("ep01_Intro_Setup.txt")
    assert legacy["video_id"] == ""
    assert legacy["video_title"] == "ep01_Intro_Setup"
