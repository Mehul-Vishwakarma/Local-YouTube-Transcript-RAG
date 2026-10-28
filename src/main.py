"""Main entry point for the local YouTube transcript RAG pipeline.

Pipeline functions take explicit arguments and never read ``sys.argv``
themselves, so they can be called safely from tests or other code.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chunker import chunk_all, chunk_file
from src.embed_chunks import embed_all
from src.fetch_transcript import fetch_video_transcript
from src.ollama_client import OllamaUnavailableError
from src.rag import answer_question, format_rag_result
from src.search import (
    DEFAULT_MIN_RELEVANCE,
    DEFAULT_TOP_K,
    print_results,
    search,
)


def run_full_pipeline(
    video_id=None,
    transcript_path=None,
    question=None,
    transcripts_dir=None,
    chunks_dir=None,
    top_k=DEFAULT_TOP_K,
    min_relevance=DEFAULT_MIN_RELEVANCE,
    embedder=None,
    chat_fn=None,
):
    """Fetch (optional), chunk, embed, and optionally answer a question."""
    print("=" * 60)
    print("YOUTUBE AI PROJECT - FULL PIPELINE")
    print("=" * 60)

    transcript_file = None

    if video_id:
        print(f"\n[1/4] Fetching transcript for video ID: {video_id}")
        transcript_file = fetch_video_transcript(video_id, transcripts_dir=transcripts_dir)
        print(f"Saved transcript: {transcript_file}")
    elif transcript_path:
        transcript_file = Path(transcript_path).expanduser().resolve()
        if not transcript_file.exists():
            raise FileNotFoundError(f"Transcript not found: {transcript_file}")
        print(f"\n[1/4] Using existing transcript: {transcript_file}")
    else:
        print("\n[1/4] No video ID or transcript path supplied; chunking all transcripts.")

    print("\n[2/4] Chunking transcript(s)...")
    if transcript_file:
        chunk_summary = chunk_file(transcript_file, chunks_dir=chunks_dir)
        chunk_count = chunk_summary["chunk_count"]
        print(f"Chunks created: {chunk_count}")
    else:
        chunk_summary = chunk_all(transcripts_dir=transcripts_dir, chunks_dir=chunks_dir)
        chunk_count = chunk_summary["chunks"]
        print(
            f"Transcripts processed: {len(chunk_summary['results'])} "
            f"| chunks created: {chunk_count}"
        )
        for error in chunk_summary["errors"]:
            print(f"  Error: {error['transcript']}: {error['error']}")

    print("\n[3/4] Generating embeddings...")
    embed_summary = embed_all(
        chunks_dir=chunks_dir,
        embedder=embedder,
    )
    print(
        f"Videos indexed: {len(embed_summary['results'])} "
        f"| embeddings written: {embed_summary['embedded']}"
    )
    for error in embed_summary["errors"]:
        print(f"  Error: {error['video_dir']}: {error['error']}")

    rag_result = None
    if question:
        print("\n[4/4] Searching and answering...")
        results = search(
            question,
            chunks_dir=chunks_dir,
            top_k=top_k,
            min_relevance=min_relevance,
            embedder=embedder,
        )
        print_results(results)
        rag_result = answer_question(
            question,
            chunks_dir=chunks_dir,
            top_k=top_k,
            min_relevance=min_relevance,
            embedder=embedder,
            chat_fn=chat_fn,
            retrieved=results,
        )
        print()
        print(format_rag_result(rag_result))
    else:
        print("\n[4/4] No question supplied; skipping search and RAG.")

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    return {
        "transcript": transcript_file,
        "chunk_count": chunk_count,
        "chunk_summary": chunk_summary,
        "embed_summary": embed_summary,
        "rag": rag_result,
    }


def quick_search(
    question,
    chunks_dir=None,
    top_k=DEFAULT_TOP_K,
    min_relevance=DEFAULT_MIN_RELEVANCE,
    embedder=None,
    chat_fn=None,
):
    """Search existing indexes and answer *question* from the best chunks."""
    print("\n" + "=" * 60)
    print("YOUTUBE AI - QUICK SEARCH & RAG")
    print("=" * 60)

    results = search(
        question,
        chunks_dir=chunks_dir,
        top_k=top_k,
        min_relevance=min_relevance,
        embedder=embedder,
    )
    print_results(results)

    rag_result = answer_question(
        question,
        chunks_dir=chunks_dir,
        top_k=top_k,
        min_relevance=min_relevance,
        embedder=embedder,
        chat_fn=chat_fn,
        retrieved=results,
    )
    print()
    print(format_rag_result(rag_result))

    return results, rag_result


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Local YouTube transcript RAG pipeline."
    )
    subparsers = parser.add_subparsers(dest="command")

    pipeline = subparsers.add_parser("pipeline", help="Fetch, chunk, embed, and ask")
    pipeline.add_argument("video_id", nargs="?", help="YouTube video ID")
    pipeline.add_argument("--transcript", help="Use an existing transcript file")
    pipeline.add_argument("--question", help="Question to answer after indexing")
    pipeline.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    pipeline.add_argument("--min-score", type=float, default=DEFAULT_MIN_RELEVANCE)

    search_parser = subparsers.add_parser("search", help="Search indexed chunks")
    search_parser.add_argument("question", nargs="+")
    search_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    search_parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_RELEVANCE)

    rag_parser = subparsers.add_parser("rag", help="Answer from indexed chunks")
    rag_parser.add_argument("question", nargs="+")
    rag_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    rag_parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_RELEVANCE)

    return parser


def cli(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("\nYouTube AI Project - Interactive Mode")
        print("=" * 50)
        question = input("\nAsk a question about the transcripts: ").strip()
        if not question:
            print("No question entered.")
            return 1
        try:
            results, rag_result = quick_search(question)
        except OllamaUnavailableError as exc:
            print(f"Error: {exc}")
            return 1
        return 0 if rag_result["sufficient"] else 1

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "pipeline":
            run_full_pipeline(
                video_id=args.video_id,
                transcript_path=args.transcript,
                question=args.question,
                top_k=args.top_k,
                min_relevance=args.min_score,
            )
            return 0

        if args.command == "search":
            question = " ".join(args.question).strip()
            results = search(
                question,
                top_k=args.top_k,
                min_relevance=args.min_score,
            )
            print_results(results)
            return 0 if results else 1

        if args.command == "rag":
            question = " ".join(args.question).strip()
            result = answer_question(
                question,
                top_k=args.top_k,
                min_relevance=args.min_score,
            )
            if result.get("chunks"):
                print("\nRetrieved chunks:")
                for chunk in result["chunks"]:
                    print(
                        f"  {chunk.get('video_title', 'Unknown video')} "
                        f"| chunk_id={chunk.get('chunk_id', '')} "
                        f"| score={chunk['score']:.4f}"
                    )
            print()
            print(format_rag_result(result))
            return 0 if result["sufficient"] else 1
    except (OllamaUnavailableError, FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}")
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(cli())
