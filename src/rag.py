"""Retrieval-augmented answers with explicit source attribution."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ollama_client import OllamaUnavailableError, chat, embed_texts
from src.scoring import (
    HINDI_STOPWORDS,
    cosine_similarity,
    keyword_similarity,
    min_max_normalize,
    normalize_text,
)
from src.search import (
    DEFAULT_MIN_RELEVANCE,
    DEFAULT_TOP_K,
    EMBED_MODEL,
    extract_query_embedding,
    rank_records,
    search,
)
from src.store import source_label

# Backwards-compatible names used by the original implementation.
min_max_norm = min_max_normalize
normalize = normalize_text

LLM_MODEL = os.environ.get("YOUTUBE_RAG_LLM_MODEL", "phi3:mini")

INSUFFICIENT_ANSWER = (
    "The indexed transcripts do not contain enough relevant information to "
    "answer this question."
)

SYSTEM_PROMPT = """You are a transcript question-answering assistant.

Your ONLY source of information is the transcript context provided
by the user. Every context block includes a source video title, video ID,
and chunk ID.

Rules:

1. Answer only from the supplied transcript context.
2. Do not use outside knowledge.
3. Do not invent facts.
4. If the context does not contain enough information to answer,
   clearly say that the provided transcript context does not contain
   enough information.
5. Preserve the meaning of the transcript.
6. You may explain the retrieved information clearly.
7. Do not claim something was taught if it is not present in the
   supplied context.
8. Cite supporting evidence with the source title and chunk ID.
"""


def retrieve(
    question,
    data,
    model=EMBED_MODEL,
    top_k=DEFAULT_TOP_K,
    min_relevance=None,
    embedder=None,
):
    """Backwards-compatible ranking over an already-loaded embedding list."""
    question = str(question or "").strip()
    if not question or not data:
        return []

    embedder = embedder or embed_texts
    response = embedder(model=model, texts=question)
    query_embedding = extract_query_embedding(response)
    if query_embedding is None:
        return []

    return rank_records(
        question,
        data,
        query_embedding,
        top_k=top_k,
        min_relevance=min_relevance,
    )


def _response_content(response):
    if isinstance(response, dict):
        message = response.get("message")
        if isinstance(message, dict) and message.get("content"):
            return message["content"]
        if response.get("response"):
            return response["response"]
    content = getattr(response, "message", None)
    if content is not None:
        content = getattr(content, "content", content)
        if content:
            return content
    return ""


def generate_answer(question, chunks, chat_fn=None, model=LLM_MODEL):
    """Ask the local LLM to answer using only the retrieved chunks."""
    context = "\n\n---\n\n".join(
        f"[Source: {source_label(chunk)}]\n{chunk['text']}" for chunk in chunks
    )
    user_prompt = f"""
Transcript context:

{context}

Question:

{question}

Answer the question using ONLY the transcript context. Cite the source
video title and chunk ID for every claim.
"""

    chat_fn = chat_fn or chat
    response = chat_fn(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    answer = _response_content(response).strip()
    if not answer:
        raise RuntimeError("Ollama returned an empty answer")
    return answer


def _sources_from_chunks(chunks):
    return [
        {
            "video_id": chunk.get("video_id", ""),
            "video_title": chunk.get("video_title", ""),
            "chunk_id": chunk.get("chunk_id", ""),
            "source": chunk.get("source", ""),
            "text": chunk.get("text", ""),
            "score": chunk.get("score", 0.0),
        }
        for chunk in chunks
    ]


def answer_question(
    question,
    chunks_dir=None,
    top_k=DEFAULT_TOP_K,
    min_relevance=DEFAULT_MIN_RELEVANCE,
    embedder=None,
    chat_fn=None,
    model=EMBED_MODEL,
    llm_model=LLM_MODEL,
    retrieved=None,
):
    """Retrieve evidence and return ``{answer, sources, sufficient}``.

    When no chunk meets the relevance threshold, no LLM call is made and the
    caller receives an explicit insufficient-evidence answer.
    """
    question = str(question or "").strip()
    if not question:
        return {
            "answer": INSUFFICIENT_ANSWER,
            "sources": [],
            "chunks": [],
            "sufficient": False,
        }

    if retrieved is None:
        retrieved = search(
            question,
            chunks_dir=chunks_dir,
            top_k=top_k,
            min_relevance=min_relevance,
            embedder=embedder,
            model=model,
        )

    if not retrieved:
        return {
            "answer": INSUFFICIENT_ANSWER,
            "sources": [],
            "chunks": [],
            "sufficient": False,
        }

    if min_relevance is not None and retrieved[0]["score"] < min_relevance:
        return {
            "answer": INSUFFICIENT_ANSWER,
            "sources": [],
            "chunks": [],
            "sufficient": False,
        }

    sources = _sources_from_chunks(retrieved)
    try:
        answer = generate_answer(
            question,
            retrieved,
            chat_fn=chat_fn,
            model=llm_model,
        )
    except (OllamaUnavailableError, RuntimeError) as exc:
        return {
            "answer": (
                "Unable to generate an answer because the local language "
                f"model failed: {exc}"
            ),
            "sources": sources,
            "chunks": retrieved,
            "sufficient": False,
            "error": str(exc),
        }

    return {
        "answer": answer,
        "sources": sources,
        "chunks": retrieved,
        "sufficient": True,
    }


def format_rag_result(result):
    lines = ["=" * 70, "ANSWER", "=" * 70, result["answer"], "=" * 70]

    sources = result.get("sources") or []
    if sources:
        lines.extend(["", "SOURCES (supporting evidence):"])
        for source in sources:
            title = source.get("video_title") or "Unknown video"
            video_id = source.get("video_id") or "unknown"
            chunk_id = source.get("chunk_id") or "unknown"
            lines.append(
                f"  - {title} | video_id={video_id} | chunk_id={chunk_id} "
                f"| score={source.get('score', 0.0):.4f}"
            )

    return "\n".join(lines)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Answer a question from the indexed transcripts."
    )
    parser.add_argument("question", nargs="*", help="Question to answer")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_RELEVANCE)
    parser.add_argument("--chunks-dir", default=None)
    parser.add_argument("--model", default=EMBED_MODEL)
    parser.add_argument("--llm-model", default=LLM_MODEL)
    args = parser.parse_args(argv)

    question = " ".join(args.question).strip()
    if not question:
        question = input("Ask a question: ").strip()
    if not question:
        print("No question provided.")
        return 1

    try:
        result = answer_question(
            question,
            chunks_dir=args.chunks_dir,
            top_k=args.top_k,
            min_relevance=args.min_score,
            model=args.model,
            llm_model=args.llm_model,
        )
    except OllamaUnavailableError as exc:
        print(f"Error: {exc}")
        return 1

    if result.get("chunks"):
        print("\nRetrieved chunks:")
        for chunk in result["chunks"]:
            print(f"  {source_label(chunk)} (score={chunk['score']:.4f})")
    else:
        print("\nNo sufficiently relevant chunks were retrieved.")

    print()
    print(format_rag_result(result))
    return 0 if result["sufficient"] else 1


if __name__ == "__main__":
    sys.exit(main())
