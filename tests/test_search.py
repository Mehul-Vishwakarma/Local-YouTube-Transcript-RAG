from src.search import search
from src.store import load_all_embeddings


def embed_query(vector):
    def _embedder(model, texts):
        return {"embeddings": [vector]}

    return _embedder


def test_search_loads_multiple_video_indexes(tmp_path, make_index):
    chunks_dir = tmp_path / "chunks"
    make_index(
        chunks_dir,
        "video_a",
        "aaaaaaaaaaa",
        "Video A",
        [("chunk_001", "alpha beta gamma", [1.0, 0.0, 0.0])],
    )
    make_index(
        chunks_dir,
        "video_b",
        "bbbbbbbbbbb",
        "Video B",
        [("chunk_001", "delta epsilon", [0.0, 1.0, 0.0])],
    )

    results = search(
        "zzz",
        chunks_dir=chunks_dir,
        top_k=10,
        min_relevance=None,
        embedder=embed_query([1.0, 0.0, 0.0]),
    )

    assert len(results) == 2
    assert results[0]["video_title"] == "Video A"
    assert results[0]["video_id"] == "aaaaaaaaaaa"
    assert results[0]["chunk_id"] == "chunk_001"
    assert results[1]["video_title"] == "Video B"


def test_keyword_scores_all_zero_do_not_become_perfect_matches(tmp_path, make_index):
    chunks_dir = tmp_path / "chunks"
    make_index(
        chunks_dir,
        "video_a",
        "aaaaaaaaaaa",
        "Video A",
        [("chunk_001", "alpha beta gamma", [1.0, 0.0, 0.0])],
    )
    make_index(
        chunks_dir,
        "video_b",
        "bbbbbbbbbbb",
        "Video B",
        [("chunk_001", "delta epsilon", [0.0, 1.0, 0.0])],
    )

    results = search(
        "zzz",
        chunks_dir=chunks_dir,
        top_k=10,
        min_relevance=None,
        embedder=embed_query([1.0, 0.0, 0.0]),
    )

    assert results[0]["keyword"] == 0.0
    assert results[0]["kw_norm"] == 0.0
    assert abs(results[0]["score"] - 0.6) < 1e-9
    assert results[1]["score"] == 0.0


def test_search_filters_by_minimum_relevance(tmp_path, make_index):
    chunks_dir = tmp_path / "chunks"
    make_index(
        chunks_dir,
        "video_a",
        "aaaaaaaaaaa",
        "Video A",
        [("chunk_001", "alpha", [1.0, 0.0, 0.0])],
    )
    make_index(
        chunks_dir,
        "video_b",
        "bbbbbbbbbbb",
        "Video B",
        [("chunk_001", "unrelated", [0.0, 1.0, 0.0])],
    )

    results = search(
        "zzz",
        chunks_dir=chunks_dir,
        top_k=10,
        min_relevance=0.5,
        embedder=embed_query([1.0, 0.0, 0.0]),
    )

    assert len(results) == 1
    assert results[0]["video_title"] == "Video A"


def test_invalid_and_zero_vectors_are_skipped(tmp_path, make_index):
    chunks_dir = tmp_path / "chunks"
    make_index(
        chunks_dir,
        "video_a",
        "aaaaaaaaaaa",
        "Video A",
        [
            ("chunk_001", "valid text", [1.0, 0.0]),
            ("chunk_002", "zero vector", [0.0, 0.0]),
            ("chunk_003", "empty vector", []),
        ],
    )

    records = load_all_embeddings(chunks_dir)
    assert len(records) == 1
    assert records[0]["chunk_id"] == "chunk_001"

    results = search(
        "zzz",
        chunks_dir=chunks_dir,
        top_k=10,
        min_relevance=None,
        embedder=embed_query([1.0, 0.0]),
    )
    assert len(results) == 1


def test_malformed_embeddings_file_is_ignored(tmp_path):
    chunks_dir = tmp_path / "chunks"
    video_dir = chunks_dir / "broken"
    video_dir.mkdir(parents=True)
    (video_dir / "embeddings.json").write_text("{not-json", encoding="utf-8")

    called = {"value": False}

    def embedder(model, texts):
        called["value"] = True
        return {"embeddings": [[1.0]]}

    assert search("question", chunks_dir=chunks_dir, embedder=embedder) == []
    assert called["value"] is False


def test_missing_index_directory_is_safe(tmp_path):
    assert search("anything", chunks_dir=tmp_path / "missing") == []


def test_empty_question_returns_no_results(tmp_path, make_index):
    chunks_dir = tmp_path / "chunks"
    make_index(
        chunks_dir,
        "video_a",
        "aaaaaaaaaaa",
        "Video A",
        [("chunk_001", "alpha", [1.0, 0.0])],
    )

    assert search("   ", chunks_dir=chunks_dir, embedder=embed_query([1.0, 0.0])) == []


def test_search_response_with_invalid_query_embedding_returns_empty(
    tmp_path, make_index
):
    chunks_dir = tmp_path / "chunks"
    make_index(
        chunks_dir,
        "video_a",
        "aaaaaaaaaaa",
        "Video A",
        [("chunk_001", "alpha", [1.0, 0.0])],
    )

    results = search(
        "question",
        chunks_dir=chunks_dir,
        embedder=embed_query([0.0, 0.0]),
    )
    assert results == []


def test_manifest_metadata_is_used_for_attribution(tmp_path, make_index):
    chunks_dir = tmp_path / "chunks"
    make_index(
        chunks_dir,
        "video_dir_name",
        "abcdefghijk",
        "Real Video Title",
        [("chunk_007", "alpha text", [1.0, 0.0])],
    )

    results = search(
        "zzz",
        chunks_dir=chunks_dir,
        top_k=1,
        min_relevance=None,
        embedder=embed_query([1.0, 0.0]),
    )

    assert results[0]["video_title"] == "Real Video Title"
    assert results[0]["video_id"] == "abcdefghijk"
    assert results[0]["chunk_id"] == "chunk_007"
    assert results[0]["text"] == "alpha text"
