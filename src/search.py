"""Hybrid semantic + keyword search across every indexed video."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ollama_client import OllamaUnavailableError, embed_texts
from src.paths import get_chunks_dir
from src.scoring import (
    HINDI_STOPWORDS,
    cosine_similarity,
    hybrid_score,
    is_valid_vector,
    keyword_similarity,
    min_max_normalize,
    normalize_text,
    tokenize,
)
from src.store import load_all_embeddings, source_label

# Backwards-compatible names used by the original implementation.
min_max_norm = min_max_normalize
normalize = normalize_text


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


EMBED_MODEL = os.environ.get("YOUTUBE_RAG_EMBED_MODEL", "nomic-embed-text")
DEFAULT_TOP_K = _env_int("YOUTUBE_RAG_TOP_K", 3)
DEFAULT_MIN_RELEVANCE = _env_float("YOUTUBE_RAG_MIN_RELEVANCE", 0.25)
SEMANTIC_WEIGHT = _env_float("YOUTUBE_RAG_SEMANTIC_WEIGHT", 0.6)
KEYWORD_WEIGHT = _env_float("YOUTUBE_RAG_KEYWORD_WEIGHT", 0.4)


def extract_query_embedding(response):
    """Pull the first valid embedding out of an Ollama-style response."""
    if isinstance(response, dict):
        embeddings = response.get("embeddings")
    elif isinstance(response, (list, tuple)):
        embeddings = response
    else:
        embeddings = getattr(response, "embeddings", None)

    if isinstance(embeddings, (list, tuple)) and embeddings:
        candidate = embeddings[0]
    elif is_valid_vector(response):
        candidate = response
    else:
        return None

    return candidate if is_valid_vector(candidate) else None


def rank_records(
    question,
    records,
    query_embedding,
    top_k=DEFAULT_TOP_K,
    min_relevance=DEFAULT_MIN_RELEVANCE,
    semantic_weight=SEMANTIC_WEIGHT,
    keyword_weight=KEYWORD_WEIGHT,
):
    """Score in-memory chunk records against one query embedding.

    Semantic similarity uses the absolute cosine score. Keyword scores are
    min-max normalized per query; when every keyword score is zero the
    normalized values stay zero instead of becoming perfect matches.
    """
    query_terms = tokenize(question)
    results = []

    for item in records or []:
        semantic = cosine_similarity(query_embedding, item.get("embedding"))
        keyword = keyword_similarity(query_terms, item.get("text", ""))
        results.append(
            {
                "chunk_id": item.get("chunk_id", ""),
                "text": item.get("text", ""),
                "video_id": item.get("video_id", ""),
                "video_title": item.get("video_title", ""),
                "source": item.get("source", ""),
                "semantic": semantic,
                "keyword": keyword,
            }
        )

    keyword_normalized = min_max_normalize([item["keyword"] for item in results])
    semantic_normalized = min_max_normalize([item["semantic"] for item in results])

    for item, keyword_norm, semantic_norm in zip(
        results, keyword_normalized, semantic_normalized
    ):
        item["kw_norm"] = keyword_norm
        item["sem_norm"] = semantic_norm
        item["score"] = hybrid_score(
            item["semantic"],
            keyword_norm,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
        )
        item["final_score"] = item["score"]

    results.sort(
        key=lambda item: (item["score"], item["semantic"], item["chunk_id"]),
        reverse=True,
    )

    if min_relevance is not None:
        results = [item for item in results if item["score"] >= min_relevance]

    if top_k is None:
        return results
    return results[: max(0, int(top_k))]


def search(
    question,
    chunks_dir=None,
    top_k=DEFAULT_TOP_K,
    min_relevance=DEFAULT_MIN_RELEVANCE,
    embedder=None,
    model=EMBED_MODEL,
    semantic_weight=SEMANTIC_WEIGHT,
    keyword_weight=KEYWORD_WEIGHT,
):
    """Return the best chunks across all video indexes."""
    question = str(question or "").strip()
    if not question:
        return []

    records = load_all_embeddings(chunks_dir)
    if not records:
        return []

    embedder = embedder or embed_texts
    response = embedder(model=model, texts=question)
    query_embedding = extract_query_embedding(response)
    if query_embedding is None:
        return []

    return rank_records(
        question,
        records,
        query_embedding,
        top_k=top_k,
        min_relevance=min_relevance,
        semantic_weight=semantic_weight,
        keyword_weight=keyword_weight,
    )


def print_results(results, query_terms=None):
    if query_terms is not None:
        print(f"Query terms (after stopword filter): {query_terms}")

    if not results:
        print("\nNo relevant chunks were found at the configured threshold.")
        return

    print("\n" + "=" * 70)
    print("SEARCH RESULTS")
    print("=" * 70)

    for index, result in enumerate(results, start=1):
        print(f"\n[{index}] {source_label(result)}")
        print(
            f"    final: {result['score']:.4f} "
            f"| semantic: {result['semantic']:.4f} "
            f"| keyword: {result['keyword']:.2f} "
            f"(norm {result['kw_norm']:.2f})"
        )
        print("-" * 70)
        print(result["text"])
        print("-" * 70)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Search indexed transcripts with hybrid scoring."
    )
    parser.add_argument("question", nargs="*", help="Question to search for")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument(
        "--min-score",
        type=float,
        default=DEFAULT_MIN_RELEVANCE,
        help="Minimum hybrid relevance score (0 disables the threshold)",
    )
    parser.add_argument("--chunks-dir", default=None)
    parser.add_argument("--model", default=EMBED_MODEL)
    args = parser.parse_args(argv)

    question = " ".join(args.question).strip()
    if not question:
        question = input("Ask a question: ").strip()
    if not question:
        print("No question entered.")
        return 1

    try:
        results = search(
            question,
            chunks_dir=args.chunks_dir,
            top_k=args.top_k,
            min_relevance=args.min_score,
            model=args.model,
        )
    except OllamaUnavailableError as exc:
        print(f"Error: {exc}")
        return 1

    print_results(results, query_terms=tokenize(question))
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
