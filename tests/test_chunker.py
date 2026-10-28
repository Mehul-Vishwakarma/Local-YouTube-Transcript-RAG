import json

from src.chunker import chunk_all, chunk_file, split_transcript
from src.store import write_transcript_metadata


def test_split_transcript_normal_text():
    text = "First sentence. Second sentence. Third sentence. Fourth sentence."

    chunks = split_transcript(text, max_chars=45, overlap_sentences=1)

    assert chunks
    assert all(len(chunk) <= 45 for chunk in chunks)
    assert "First sentence." in chunks[0]
    assert "Fourth sentence." in chunks[-1]


def test_split_transcript_empty_returns_empty_list():
    assert split_transcript("") == []
    assert split_transcript("   \n\t  ") == []


def test_split_transcript_overlong_sentence_without_spaces():
    text = "a" * 250

    chunks = split_transcript(text, max_chars=100, overlap_sentences=2)

    assert chunks
    assert all(len(chunk) <= 100 for chunk in chunks)
    assert "".join(chunks) == text


def test_split_transcript_overlong_sentence_with_words():
    text = " ".join(["word"] * 200)

    chunks = split_transcript(text, max_chars=80, overlap_sentences=2)

    assert chunks
    assert all(len(chunk) <= 80 for chunk in chunks)
    assert all(chunk.strip() for chunk in chunks)


def test_chunk_overlap_is_present_but_bounded():
    text = "One is here. Two is here. Three is here. Four is here."

    chunks = split_transcript(text, max_chars=30, overlap_sentences=1)

    assert all(len(chunk) <= 30 for chunk in chunks)
    assert len(chunks) > 1
    # The overlapping sentence should appear in consecutive chunks.
    assert any(
        chunks[index].split(".")[-2].strip() in chunks[index + 1]
        for index in range(len(chunks) - 1)
        if "." in chunks[index]
    )


def test_overlap_never_makes_chunk_too_long():
    text = "A" * 60 + ". " + "B" * 60 + ". " + "C" * 60 + "."

    chunks = split_transcript(text, max_chars=65, overlap_sentences=2)

    assert all(len(chunk) <= 65 for chunk in chunks)


def test_chunk_file_with_empty_transcript(tmp_path):
    transcript = tmp_path / "abcdefghijk.txt"
    transcript.write_text("   ", encoding="utf-8")
    write_transcript_metadata(
        transcript,
        {"video_id": "abcdefghijk", "video_title": "Empty video"},
    )

    summary = chunk_file(transcript, chunks_dir=tmp_path / "chunks")

    assert summary["chunk_count"] == 0
    manifest = json.loads(
        (summary["output_dir"] / "chunks.json").read_text(encoding="utf-8")
    )
    assert manifest["chunks"] == []
    assert not list(summary["output_dir"].glob("chunk_*.txt"))


def test_chunk_file_preserves_source_metadata(tmp_path):
    transcript = tmp_path / "abcdefghijk.txt"
    transcript.write_text("Hello world. This is a test.", encoding="utf-8")
    write_transcript_metadata(
        transcript,
        {"video_id": "abcdefghijk", "video_title": "Video title"},
    )

    summary = chunk_file(
        transcript,
        chunks_dir=tmp_path / "chunks",
        max_chars=20,
        overlap_sentences=0,
    )

    manifest = json.loads(
        (summary["output_dir"] / "chunks.json").read_text(encoding="utf-8")
    )
    assert summary["chunk_count"] > 0
    for chunk in manifest["chunks"]:
        assert chunk["video_id"] == "abcdefghijk"
        assert chunk["video_title"] == "Video title"
        assert chunk["chunk_id"].startswith("chunk_")
        assert chunk["text"].strip()


def test_chunk_all_processes_directory(tmp_path):
    transcripts = tmp_path / "transcripts"
    transcripts.mkdir()
    (transcripts / "abcdefghijk.txt").write_text("One. Two.", encoding="utf-8")
    (transcripts / "zyxwvutsrqp.txt").write_text("Three. Four.", encoding="utf-8")

    summary = chunk_all(
        transcripts_dir=transcripts,
        chunks_dir=tmp_path / "chunks",
        max_chars=50,
    )

    assert summary["transcripts"] == 2
    assert summary["errors"] == []
    assert summary["chunks"] >= 2


def test_chunk_all_missing_directory_is_safe(tmp_path):
    summary = chunk_all(
        transcripts_dir=tmp_path / "does-not-exist",
        chunks_dir=tmp_path / "chunks",
    )

    assert summary["transcripts"] == 0
    assert summary["chunks"] == 0
