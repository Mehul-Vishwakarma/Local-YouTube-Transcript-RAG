"""Split transcripts into sentence-aware chunks with bounded size."""

from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.paths import get_chunks_dir, get_transcripts_dir
from src.store import (
    read_transcript_metadata,
    sanitize_filename,
    write_chunks_manifest,
)

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?।॥])\s+")


def _split_long_unit(text, max_chars):
    """Hard-wrap an overlong sentence at word (or character) boundaries."""
    pieces = []
    current = []

    for word in text.split():
        if len(word) > max_chars:
            if current:
                pieces.append(" ".join(current))
                current = []
            for start in range(0, len(word), max_chars):
                pieces.append(word[start:start + max_chars])
            continue

        candidate = " ".join(current + [word])
        if len(candidate) <= max_chars:
            current.append(word)
        else:
            if current:
                pieces.append(" ".join(current))
            current = [word]

    if current:
        pieces.append(" ".join(current))
    return pieces


def split_transcript(text, max_chars=1200, overlap_sentences=2):
    """Split text into chunks of at most *max_chars* characters.

    Sentences longer than *max_chars* are hard-wrapped so no chunk can exceed
    the limit. Overlap is applied only when it still leaves room for the next
    sentence.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero")
    if overlap_sentences < 0:
        raise ValueError("overlap_sentences cannot be negative")

    normalised = re.sub(r"\s+", " ", str(text or "")).strip()
    if not normalised:
        return []

    units = []
    for sentence in SENTENCE_SPLIT_RE.split(normalised):
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) <= max_chars:
            units.append(sentence)
        else:
            units.extend(_split_long_unit(sentence, max_chars))

    chunks = []
    current = []

    for unit in units:
        if not current:
            current.append(unit)
            continue

        candidate = " ".join(current + [unit])
        if len(candidate) <= max_chars:
            current.append(unit)
            continue

        chunks.append(" ".join(current))
        overlap = current[-overlap_sentences:] if overlap_sentences else []
        current = overlap + [unit]

        while current and len(" ".join(current)) > max_chars:
            current.pop(0)

        if not current:
            current = [unit]

    if current:
        chunks.append(" ".join(current))

    return chunks


def chunk_file(
    transcript_path,
    chunks_dir=None,
    max_chars=1200,
    overlap_sentences=2,
):
    """Chunk one transcript file and write a complete video index."""
    path = Path(transcript_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Transcript not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a transcript file: {path}")

    text = path.read_text(encoding="utf-8")
    chunks = split_transcript(
        text,
        max_chars=max_chars,
        overlap_sentences=overlap_sentences,
    )

    metadata = read_transcript_metadata(path)
    video_id = str(metadata.get("video_id") or "")
    video_title = str(metadata.get("video_title") or path.stem)

    output_root = Path(get_chunks_dir(chunks_dir))
    output_root.mkdir(parents=True, exist_ok=True)
    video_dir = output_root / sanitize_filename(path.stem, fallback="transcript")
    video_dir.mkdir(parents=True, exist_ok=True)

    for old_file in video_dir.glob("chunk_*.txt"):
        old_file.unlink()
    stale_embeddings = video_dir / "embeddings.json"
    if stale_embeddings.exists():
        stale_embeddings.unlink()

    chunk_records = []
    for index, chunk in enumerate(chunks, start=1):
        chunk_id = f"chunk_{index:03d}"
        (video_dir / f"{chunk_id}.txt").write_text(chunk, encoding="utf-8")
        chunk_records.append(
            {
                "chunk_id": chunk_id,
                "text": chunk,
                "video_id": video_id,
                "video_title": video_title,
                "source": path.name,
            }
        )

    write_chunks_manifest(
        video_dir,
        {
            "video_id": video_id,
            "video_title": video_title,
            "source": path.name,
            "characters": len(text),
            "max_chars": max_chars,
            "overlap_sentences": overlap_sentences,
            "chunk_count": len(chunk_records),
            "chunks": chunk_records,
        },
    )

    return {
        "transcript": path,
        "output_dir": video_dir,
        "characters": len(text),
        "chunks": chunk_records,
        "chunk_count": len(chunk_records),
    }


def chunk_all(transcripts_dir=None, chunks_dir=None, **kwargs):
    """Chunk every ``*.txt`` transcript in a directory."""
    source_dir = Path(get_transcripts_dir(transcripts_dir))
    if not source_dir.exists():
        return {"transcripts": 0, "chunks": 0, "results": [], "errors": []}

    results = []
    errors = []
    for path in sorted(source_dir.glob("*.txt")):
        if not path.is_file():
            continue
        try:
            results.append(chunk_file(path, chunks_dir=chunks_dir, **kwargs))
        except Exception as exc:
            errors.append({"transcript": str(path), "error": str(exc)})

    return {
        "transcripts": len(results) + len(errors),
        "chunks": sum(item["chunk_count"] for item in results),
        "results": results,
        "errors": errors,
    }


def _targets_from_arguments(targets):
    """Expand files, directories, and (Windows-safe) wildcard strings."""
    paths = []
    for target in targets:
        candidate = Path(target).expanduser()
        if candidate.is_dir():
            paths.extend(sorted(candidate.glob("*.txt")))
        elif candidate.is_file():
            paths.append(candidate)
        else:
            matches = sorted(glob.glob(target))
            paths.extend(Path(match) for match in matches if Path(match).is_file())
    return paths


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Chunk transcripts into bounded, overlapping pieces."
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Transcript files, a directory, or a glob. Defaults to transcripts/.",
    )
    parser.add_argument("--max-chars", type=int, default=1200)
    parser.add_argument("--overlap", type=int, default=2)
    args = parser.parse_args(argv)

    if args.targets:
        targets = _targets_from_arguments(args.targets)
    else:
        targets = _targets_from_arguments([str(get_transcripts_dir())])

    if not targets:
        print("No transcript files found.")
        return 1

    failures = 0
    for path in targets:
        try:
            summary = chunk_file(
                path,
                max_chars=args.max_chars,
                overlap_sentences=args.overlap,
            )
        except Exception as exc:
            failures += 1
            print(f"Error chunking {path}: {exc}")
            continue

        print(f"\nTranscript: {summary['transcript'].name}")
        print(f"Characters: {summary['characters']:,}")
        print(f"Chunks created: {summary['chunk_count']}")
        print(f"Output: {summary['output_dir']}")
        if summary["chunks"]:
            print("\nFirst chunk preview:")
            print("-" * 60)
            print(summary["chunks"][0]["text"][:500])
            print("-" * 60)
        else:
            print("No valid chunks were produced (the transcript is empty).")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
