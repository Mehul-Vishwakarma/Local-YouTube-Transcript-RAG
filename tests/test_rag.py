from src.ollama_client import OllamaUnavailableError
from src.rag import INSUFFICIENT_ANSWER, answer_question, format_rag_result


def embed_query(vector):
    def _embedder(model, texts):
        return {"embeddings": [vector]}

    return _embedder


def test_no_evidence_returns_explicit_message_without_calling_llm(
    tmp_path, make_index
):
    chunks_dir = tmp_path / "chunks"
    make_index(
        chunks_dir,
        "video_a",
        "aaaaaaaaaaa",
        "Video A",
        [("chunk_001", "alpha beta gamma", [0.0, 1.0, 0.0])],
    )

    def chat_fn(model, messages):
        raise AssertionError("LLM must not be called when evidence is insufficient")

    result = answer_question(
        "zzz",
        chunks_dir=chunks_dir,
        min_relevance=0.3,
        embedder=embed_query([1.0, 0.0, 0.0]),
        chat_fn=chat_fn,
    )

    assert result["sufficient"] is False
    assert result["answer"] == INSUFFICIENT_ANSWER
    assert "do not contain enough relevant information" in result["answer"]
    assert result["sources"] == []


def test_no_indexes_returns_insufficient_answer(tmp_path):
    result = answer_question(
        "anything",
        chunks_dir=tmp_path / "missing",
        min_relevance=0.1,
    )

    assert result["sufficient"] is False
    assert result["answer"] == INSUFFICIENT_ANSWER


def test_answer_includes_source_title_chunk_id_and_prompt_context(
    tmp_path, make_index
):
    chunks_dir = tmp_path / "chunks"
    make_index(
        chunks_dir,
        "video_a",
        "abcdefghijk",
        "Real Video Title",
        [("chunk_007", "alpha beta gamma", [1.0, 0.0])],
    )

    captured = {}

    def chat_fn(model, messages):
        captured["model"] = model
        captured["messages"] = messages
        return {"message": {"content": "Alpha is discussed in the transcript."}}

    result = answer_question(
        "zzz",
        chunks_dir=chunks_dir,
        min_relevance=0.3,
        embedder=embed_query([1.0, 0.0]),
        chat_fn=chat_fn,
    )

    assert result["sufficient"] is True
    assert result["answer"] == "Alpha is discussed in the transcript."
    assert len(result["sources"]) == 1
    assert result["sources"][0]["video_title"] == "Real Video Title"
    assert result["sources"][0]["chunk_id"] == "chunk_007"

    user_prompt = captured["messages"][1]["content"]
    assert "[Source:" in user_prompt
    assert "Real Video Title" in user_prompt
    assert "chunk_007" in user_prompt
    assert "alpha beta gamma" in user_prompt

    formatted = format_rag_result(result)
    assert "ANSWER" in formatted
    assert "Real Video Title" in formatted
    assert "chunk_007" in formatted
    assert "SOURCES" in formatted


def test_empty_question_is_insufficient(tmp_path):
    result = answer_question("   ", chunks_dir=tmp_path)
    assert result["sufficient"] is False
    assert result["answer"] == INSUFFICIENT_ANSWER


def test_llm_failure_is_reported_gracefully(tmp_path, make_index):
    chunks_dir = tmp_path / "chunks"
    make_index(
        chunks_dir,
        "video_a",
        "aaaaaaaaaaa",
        "Video A",
        [("chunk_001", "alpha", [1.0, 0.0])],
    )

    def failing_chat(model, messages):
        raise OllamaUnavailableError("Ollama is not running")

    result = answer_question(
        "zzz",
        chunks_dir=chunks_dir,
        min_relevance=0.3,
        embedder=embed_query([1.0, 0.0]),
        chat_fn=failing_chat,
    )

    assert result["sufficient"] is False
    assert "Unable to generate an answer" in result["answer"]
    assert "Ollama is not running" in result["answer"]
    assert result["sources"]
