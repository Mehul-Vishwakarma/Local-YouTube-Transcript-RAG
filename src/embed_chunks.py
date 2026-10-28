"""Generate embeddings for every video index under ``chunks/``."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ollama_client import OllamaUnavailableError, embed_texts
from src.paths import CHUNKS_DIR, get_chunks_dir
from src.scoring import is_valid_vector
from src.store import iter_video_dirs, load_chunk_records

MODEL = os.environ.get("YOUTUBE_RAG_EMBED_MODEL", "nomic-embed-text")
BATCH_SIZE = 16


class EmbeddingError(RuntimeError):
    """Raised when an embedding response is malformed."""


def extract_embeddings(response, expected_count):
    if isinstance(response, dict):
        embeddings = response.get("embeddings")
    else:
        embeddings = getattr(response, "embeddings", None)

    if not isinstance(embeddings, (list, tuple)):
        raise EmbeddingError("Ollama returned no embeddings list")
    if len(embeddings) != expected_count:
        raise EmbeddingError(
            "Ollama returned "
            f"{len(embeddings)} embeddings for {expected_count} chunks"
        )
    return list(embeddings)


def embed_video(
    video_dir,
    model=MODEL,
    embedder=None,
    batch_size=BATCH_SIZE,
):
    """Embed all chunks in one video directory and write ``embeddings.json``."""
    video_dir = Path(video_dir)
    records = load_chunk_records(video_dir)
    if not records:
        return {
            "video_dir": video_dir,
            "chunks": 0,
            "embedded": 0,
            "skipped": 0,
        }

    embedder = embedder or embed_texts
    batch_size = max(1, int(batch_size))
    payload = []
    skipped = 0

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        texts = [record["text"] for record in batch]
        response = embedder(model=model, texts=texts)
        vectors = extract_embeddings(response, len(texts))

        for record, vector in zip(batch, vectors):
            if not is_valid_vector(vector):
                skipped += 1
                continue
            payload.append(
                {
                    "chunk_id": record["chunk_id"],
                    "text": record["text"],
                    "video_id": record["video_id"],
                    "video_title": record["video_title"],
                    "source": record["source"],
                    "embedding": list(vector),
                }
            )

    if not payload:
        return {
            "video_dir": video_dir,
            "chunks": len(records),
            "embedded": 0,
            "skipped": skipped,
        }

    output_file = video_dir / "embeddings.json"
    output_file.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "video_dir": video_dir,
        "chunks": len(records),
        "embedded": len(payload),
        "skipped": skipped,
        "output_file": output_file,
        "dimensions": len(payload[0]["embedding"]),
    }


def embed_all(chunks_dir=None, model=MODEL, embedder=None, batch_size=BATCH_SIZE):
    """Embed every video index. Missing or empty indexes are skipped."""
    directory = Path(get_chunks_dir(chunks_dir))
    if not directory.exists():
        return {"videos": 0, "embedded": 0, "results": [], "errors": []}

    results = []
    errors = []
    for video_dir in iter_video_dirs(directory):
        if not (video_dir / "chunks.json").exists() and not list(
            video_dir.glob("chunk_*.txt")
        ):
            continue
        try:
            results.append(
                embed_video(
                    video_dir,
                    model=model,
                    embedder=embedder,
                    batch_size=batch_size,
                )
            )
        except (EmbeddingError, OllamaUnavailableError) as exc:
            errors.append({"video_dir": str(video_dir), "error": str(exc)})
        except Exception as exc:
            errors.append({"video_dir": str(video_dir), "error": str(exc)})

    return {
        "videos": len(results) + len(errors),
        "embedded": sum(item["embedded"] for item in results),
        "results": results,
        "errors": errors,
    }


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Generate embeddings for all chunked videos."
    )
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--chunks-dir", default=None)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args(argv)

    summary = embed_all(
        chunks_dir=args.chunks_dir,
        model=args.model,
        batch_size=args.batch_size,
    )

    if summary["videos"] == 0:
        print("No chunk directories with chunks were found.")
        print("Run the chunker first: python src/chunker.py transcripts")
        return 1

    for item in summary["results"]:
        print(f"\nVideo: {item['video_dir'].name}")
        print(f"Chunks: {item['chunks']}")
        print(f"Embeddings written: {item['embedded']}")
        if item["skipped"]:
            print(f"Invalid embeddings skipped: {item['skipped']}")
        if item.get("output_file"):
            print(f"Saved to: {item['output_file']}")
            print(f"Vector dimensions: {item['dimensions']}")
        else:
            print("No valid embeddings were produced for this video.")

    for error in summary["errors"]:
        print(f"\nError for {error['video_dir']}: {error['error']}")

    if summary["errors"]:
        print("\nSome videos could not be embedded. See errors above.")
        return 1

    print(f"\nDone. Embedded {summary['embedded']} chunks across {summary['videos']} videos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
