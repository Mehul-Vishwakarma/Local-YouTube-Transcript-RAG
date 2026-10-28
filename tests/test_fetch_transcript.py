import pytest

from src.fetch_transcript import (
    fetch_transcript_text,
    fetch_video_transcript,
    get_video_title,
)
from src.store import read_transcript_metadata


class FakeTranscript:
    def __init__(self, snippets):
        self.snippets = snippets

    def fetch(self):
        return self.snippets


class FakeTranscriptList:
    def __init__(self, snippets):
        self.transcript = FakeTranscript(snippets)

    def find_transcript(self, languages):
        return self.transcript

    def __iter__(self):
        return iter([self.transcript])


class FakeApi:
    def __init__(self, snippets):
        self.snippets = snippets

    def list(self, video_id):
        return FakeTranscriptList(self.snippets)


def test_fetch_transcript_text_joins_snippets():
    api = FakeApi([{"text": "Hello"}, {"text": "world"}])
    assert fetch_transcript_text("abcdefghijk", api=api) == "Hello world"


def test_fetch_transcript_text_rejects_empty_transcript():
    api = FakeApi([{"text": "   "}])
    with pytest.raises(RuntimeError, match="empty"):
        fetch_transcript_text("abcdefghijk", api=api)


def test_fetch_video_transcript_uses_project_directory_and_video_id(tmp_path):
    api = FakeApi([{"text": "Course content."}])

    path = fetch_video_transcript(
        "abcdefghijk",
        transcripts_dir=tmp_path,
        api=api,
        title_lookup=lambda video_id: "A Long Video Title",
    )

    assert path == tmp_path / "abcdefghijk.txt"
    assert path.read_text(encoding="utf-8") == "Course content."

    metadata = read_transcript_metadata(path)
    assert metadata["video_id"] == "abcdefghijk"
    assert metadata["video_title"] == "A Long Video Title"


def test_get_video_title_falls_back_on_network_error(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("network down")

    monkeypatch.setattr("urllib.request.urlopen", fail)
    assert get_video_title("abcdefghijk") == "abcdefghijk"


def test_fetch_video_transcript_requires_video_id(tmp_path):
    with pytest.raises(ValueError):
        fetch_video_transcript("", transcripts_dir=tmp_path)
