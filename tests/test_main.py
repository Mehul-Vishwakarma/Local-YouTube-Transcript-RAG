import sys

import src.main as main_module


def test_run_full_pipeline_passes_explicit_arguments(tmp_path, monkeypatch):
    transcript = tmp_path / "abcdefghijk.txt"
    transcript.write_text("Hello world.", encoding="utf-8")
    chunks_dir = tmp_path / "chunks"

    calls = {}

    def fake_fetch(video_id, transcripts_dir=None):
        calls["fetch"] = {"video_id": video_id, "transcripts_dir": transcripts_dir}
        return transcript

    def fake_chunk_file(path, chunks_dir=None):
        calls["chunk_file"] = {"path": path, "chunks_dir": chunks_dir}
        return {"chunk_count": 2, "chunks": []}

    def fake_embed_all(chunks_dir=None, embedder=None):
        calls["embed_all"] = {"chunks_dir": chunks_dir, "embedder": embedder}
        return {"results": [], "errors": [], "embedded": 0}

    results = [{"score": 0.8, "chunk_id": "chunk_001"}]

    def fake_search(question, chunks_dir=None, top_k=None, min_relevance=None, embedder=None):
        calls["search"] = {
            "question": question,
            "chunks_dir": chunks_dir,
            "top_k": top_k,
            "min_relevance": min_relevance,
            "embedder": embedder,
        }
        return results

    def fake_answer(
        question,
        chunks_dir=None,
        top_k=None,
        min_relevance=None,
        embedder=None,
        chat_fn=None,
        retrieved=None,
    ):
        calls["answer"] = {
            "question": question,
            "chunks_dir": chunks_dir,
            "retrieved": retrieved,
        }
        return {"answer": "ok", "sources": [], "sufficient": True, "chunks": results}

    monkeypatch.setattr(main_module, "fetch_video_transcript", fake_fetch)
    monkeypatch.setattr(main_module, "chunk_file", fake_chunk_file)
    monkeypatch.setattr(main_module, "embed_all", fake_embed_all)
    monkeypatch.setattr(main_module, "search", fake_search)
    monkeypatch.setattr(main_module, "answer_question", fake_answer)
    monkeypatch.setattr(main_module, "print_results", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_module, "format_rag_result", lambda result: "formatted")

    # These unrelated argv values must not be used by the pipeline functions.
    monkeypatch.setattr(sys, "argv", ["prog", "search", "WRONG QUESTION"])

    summary = main_module.run_full_pipeline(
        video_id="abcdefghijk",
        question="What is this about?",
        chunks_dir=chunks_dir,
    )

    assert calls["fetch"]["video_id"] == "abcdefghijk"
    assert calls["chunk_file"]["path"] == transcript
    assert calls["chunk_file"]["chunks_dir"] == chunks_dir
    assert calls["embed_all"]["chunks_dir"] == chunks_dir
    assert calls["search"]["question"] == "What is this about?"
    assert calls["answer"]["question"] == "What is this about?"
    assert calls["answer"]["retrieved"] is results
    assert summary["chunk_count"] == 2


def test_run_full_pipeline_without_video_chunks_all_transcripts(tmp_path, monkeypatch):
    calls = {}

    def fake_chunk_all(transcripts_dir=None, chunks_dir=None):
        calls["chunk_all"] = {
            "transcripts_dir": transcripts_dir,
            "chunks_dir": chunks_dir,
        }
        return {"results": [], "errors": [], "chunks": 0, "transcripts": 0}

    def fail_chunk_file(*args, **kwargs):
        raise AssertionError("chunk_file should not be used in batch mode")

    def fake_embed_all(chunks_dir=None, embedder=None):
        calls["embed_all"] = chunks_dir
        return {"results": [], "errors": [], "embedded": 0}

    monkeypatch.setattr(main_module, "chunk_all", fake_chunk_all)
    monkeypatch.setattr(main_module, "chunk_file", fail_chunk_file)
    monkeypatch.setattr(main_module, "embed_all", fake_embed_all)
    monkeypatch.setattr(
        main_module,
        "search",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("search should not run without a question")
        ),
    )

    summary = main_module.run_full_pipeline(
        transcripts_dir=tmp_path / "transcripts",
        chunks_dir=tmp_path / "chunks",
    )

    assert calls["chunk_all"]["chunks_dir"] == tmp_path / "chunks"
    assert summary["rag"] is None


def test_quick_search_uses_explicit_question(tmp_path, monkeypatch):
    calls = {}
    results = [{"score": 0.8, "chunk_id": "chunk_001"}]

    def fake_search(question, chunks_dir=None, top_k=None, min_relevance=None, embedder=None):
        calls["search"] = {"question": question, "chunks_dir": chunks_dir}
        return results

    def fake_answer(
        question,
        chunks_dir=None,
        top_k=None,
        min_relevance=None,
        embedder=None,
        chat_fn=None,
        retrieved=None,
    ):
        calls["answer"] = {"question": question, "retrieved": retrieved}
        return {"answer": "ok", "sources": [], "sufficient": True, "chunks": results}

    monkeypatch.setattr(main_module, "search", fake_search)
    monkeypatch.setattr(main_module, "answer_question", fake_answer)
    monkeypatch.setattr(main_module, "print_results", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_module, "format_rag_result", lambda result: "formatted")
    monkeypatch.setattr(sys, "argv", ["prog", "pipeline", "ignored"])

    search_results, rag_result = main_module.quick_search(
        "real question",
        chunks_dir=tmp_path / "chunks",
    )

    assert calls["search"]["question"] == "real question"
    assert calls["search"]["chunks_dir"] == tmp_path / "chunks"
    assert calls["answer"]["question"] == "real question"
    assert calls["answer"]["retrieved"] is results
    assert search_results is results
    assert rag_result["sufficient"] is True
