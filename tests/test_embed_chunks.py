import json

from src.embed_chunks import EmbeddingError, embed_all, embed_video, extract_embeddings
from src.ollama_client import OllamaUnavailableError


def deterministic_embedder(model, texts):
    return {"embeddings": [[float(len(text)), 1.0] for text in texts]}


def prepare_index(make_index, chunks_dir, dirname, video_id, title, entries):
    video_dir = make_index(chunks_dir, dirname, video_id, title, entries)
    (video_dir / "embeddings.json").unlink()
    return video_dir


def test_embed_all_processes_every_video_index(tmp_path, make_index):
    chunks_dir = tmp_path / "chunks"
    first = prepare_index(
        make_index,
        chunks_dir,
        "video_a",
        "aaaaaaaaaaa",
        "Video A",
        [("chunk_001", "first text", [1.0, 0.0])],
    )
    second = prepare_index(
        make_index,
        chunks_dir,
        "video_b",
        "bbbbbbbbbbb",
        "Video B",
        [("chunk_001", "second text", [0.0, 1.0])],
    )

    summary = embed_all(chunks_dir=chunks_dir, embedder=deterministic_embedder)

    assert summary["videos"] == 2
    assert summary["embedded"] == 2
    assert summary["errors"] == []
    assert (first / "embeddings.json").exists()
    assert (second / "embeddings.json").exists()

    saved = json.loads((second / "embeddings.json").read_text(encoding="utf-8"))
    assert saved[0]["video_id"] == "bbbbbbbbbbb"
    assert saved[0]["video_title"] == "Video B"
    assert saved[0]["chunk_id"] == "chunk_001"
    assert saved[0]["text"] == "second text"
    assert saved[0]["embedding"] == [11.0, 1.0]


def test_invalid_vectors_are_skipped_without_crashing(tmp_path, make_index):
    chunks_dir = tmp_path / "chunks"
    video_dir = prepare_index(
        make_index,
        chunks_dir,
        "video_a",
        "aaaaaaaaaaa",
        "Video A",
        [
            ("chunk_001", "valid", [1.0, 0.0]),
            ("chunk_002", "invalid", [0.0, 0.0]),
        ],
    )

    def partially_invalid(model, texts):
        return {"embeddings": [[1.0, 0.0], [0.0, 0.0]]}

    summary = embed_all(chunks_dir=chunks_dir, embedder=partially_invalid)

    assert summary["embedded"] == 1
    saved = json.loads((video_dir / "embeddings.json").read_text(encoding="utf-8"))
    assert len(saved) == 1
    assert saved[0]["chunk_id"] == "chunk_001"

    result = embed_video(
        video_dir,
        embedder=lambda model, texts: {"embeddings": [[0.0, 0.0] for _ in texts]},
    )
    assert result["embedded"] == 0


def test_ollama_errors_are_reported_per_video(tmp_path, make_index):
    chunks_dir = tmp_path / "chunks"
    prepare_index(
        make_index,
        chunks_dir,
        "video_a",
        "aaaaaaaaaaa",
        "Video A",
        [("chunk_001", "first text", [1.0, 0.0])],
    )

    def failing_embedder(model, texts):
        raise OllamaUnavailableError("Ollama is not running")

    summary = embed_all(chunks_dir=chunks_dir, embedder=failing_embedder)

    assert summary["results"] == []
    assert summary["embedded"] == 0
    assert len(summary["errors"]) == 1
    assert "Ollama is not running" in summary["errors"][0]["error"]


def test_empty_chunks_directory_is_safe(tmp_path):
    summary = embed_all(chunks_dir=tmp_path / "missing", embedder=deterministic_embedder)
    assert summary == {"videos": 0, "embedded": 0, "results": [], "errors": []}


def test_extract_embeddings_rejects_wrong_count():
    try:
        extract_embeddings({"embeddings": [[1.0]]}, expected_count=2)
    except EmbeddingError as exc:
        assert "1 embeddings for 2 chunks" in str(exc)
    else:
        raise AssertionError("EmbeddingError was expected")
