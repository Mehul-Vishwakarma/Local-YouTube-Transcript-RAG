"""Reading and writing transcript, chunk, and embedding artefacts."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.paths import get_chunks_dir
from src.scoring import is_valid_vector

INVALID_FILENAME_RE = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_PREFIXED_VIDEO_ID_RE = re.compile(r"^([A-Za-z0-9_-]{11})__(.+)$")


def sanitize_filename(value, fallback="transcript", max_length=120):
    """Turn arbitrary text into a safe single filename component."""
    cleaned = INVALID_FILENAME_RE.sub("_", str(value or ""))
    cleaned = re.sub(r"\s+", "_", cleaned).strip(" ._")
    cleaned = cleaned[:max_length].strip(" ._")
    return cleaned or fallback


def transcript_filename(video_id, title=None):
    """Return a collision-resistant transcript filename based on video ID."""
    safe_id = sanitize_filename(video_id, fallback="video")
    return f"{safe_id}.txt"


def metadata_path_for(transcript_path):
    path = Path(transcript_path)
    return path.with_name(f"{path.stem}.meta.json")


def infer_metadata_from_name(value):
    """Infer ``video_id`` and ``video_title`` from a file or directory name."""
    stem = Path(value).stem
    match = _PREFIXED_VIDEO_ID_RE.match(stem)
    if match:
        return {"video_id": match.group(1), "video_title": match.group(2)}
    if VIDEO_ID_RE.match(stem):
        return {"video_id": stem, "video_title": stem}
    return {"video_id": "", "video_title": stem}


def write_transcript_metadata(transcript_path, metadata):
    path = metadata_path_for(transcript_path)
    payload = dict(metadata or {})
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def read_transcript_metadata(transcript_path):
    """Read sidecar metadata, falling back to filename-based inference."""
    path = Path(transcript_path)
    inferred = infer_metadata_from_name(path)
    sidecar = metadata_path_for(path)
    if not sidecar.exists():
        return inferred

    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return inferred
    if not isinstance(payload, dict):
        return inferred

    metadata = dict(inferred)
    metadata.update(
        {
            "video_id": str(payload.get("video_id") or inferred["video_id"]),
            "video_title": str(payload.get("video_title") or inferred["video_title"]),
        }
    )
    for key, value in payload.items():
        metadata.setdefault(key, value)
    return metadata


def write_chunks_manifest(video_dir, manifest):
    video_dir = Path(video_dir)
    video_dir.mkdir(parents=True, exist_ok=True)
    path = video_dir / "chunks.json"
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def iter_video_dirs(chunks_dir=None):
    directory = Path(get_chunks_dir(chunks_dir))
    if not directory.exists():
        return []
    return sorted(path for path in directory.iterdir() if path.is_dir())


def _normalise_record(item, defaults, fallback_id):
    if not isinstance(item, dict):
        return None

    text = item.get("text")
    if not isinstance(text, str) or not text.strip():
        return None

    video_id = item.get("video_id")
    if video_id is None:
        video_id = defaults.get("video_id", "")
    video_title = item.get("video_title")
    if not video_title:
        video_title = defaults.get("video_title") or fallback_id

    return {
        "chunk_id": str(item.get("chunk_id") or "chunk"),
        "text": text,
        "video_id": str(video_id or ""),
        "video_title": str(video_title or fallback_id),
        "source": str(item.get("source") or defaults.get("source") or ""),
    }


def load_chunk_records(video_dir):
    """Load chunks for one video directory.

    Prefers ``chunks.json`` (which carries metadata) and falls back to legacy
    ``chunk_*.txt`` files.
    """
    video_dir = Path(video_dir)
    inferred = infer_metadata_from_name(video_dir)
    defaults = {
        "video_id": inferred["video_id"],
        "video_title": inferred["video_title"],
        "source": "",
    }

    manifest_path = video_dir / "chunks.json"
    records = []
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = {}
        if isinstance(manifest, dict):
            defaults["video_id"] = str(manifest.get("video_id") or defaults["video_id"])
            defaults["video_title"] = str(
                manifest.get("video_title") or defaults["video_title"]
            )
            defaults["source"] = str(manifest.get("source") or "")
            raw_chunks = manifest.get("chunks", [])
        elif isinstance(manifest, list):
            raw_chunks = manifest
        else:
            raw_chunks = []

        for item in raw_chunks or []:
            record = _normalise_record(item, defaults, video_dir.name)
            if record:
                records.append(record)

    if records:
        return records

    for path in sorted(video_dir.glob("chunk_*.txt")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        record = _normalise_record(
            {"chunk_id": path.stem, "text": text},
            defaults,
            video_dir.name,
        )
        if record:
            records.append(record)

    return records


def load_all_embeddings(chunks_dir=None):
    """Load every valid embedded chunk from every video index."""
    records = []
    for video_dir in iter_video_dirs(chunks_dir):
        embedding_path = video_dir / "embeddings.json"
        if not embedding_path.exists():
            continue
        try:
            payload = json.loads(embedding_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue

        if isinstance(payload, dict):
            payload = payload.get("chunks", [])
        if not isinstance(payload, list):
            continue

        inferred = infer_metadata_from_name(video_dir)
        defaults = {
            "video_id": inferred["video_id"],
            "video_title": inferred["video_title"],
            "source": "",
        }

        for item in payload:
            if not isinstance(item, dict):
                continue
            embedding = item.get("embedding")
            if not is_valid_vector(embedding):
                continue
            record = _normalise_record(item, defaults, video_dir.name)
            if record:
                record["embedding"] = list(embedding)
                records.append(record)

    return records


def source_label(record):
    """Human-readable source attribution for a chunk."""
    title = record.get("video_title") or "Unknown video"
    video_id = record.get("video_id") or "unknown"
    chunk_id = record.get("chunk_id") or "unknown"
    return f"{title} (video_id={video_id}, chunk_id={chunk_id})"
