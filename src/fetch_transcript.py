"""Fetch a YouTube transcript and save it under the project transcripts dir."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.paths import TRANSCRIPTS_DIR, ensure_directory, get_transcripts_dir
from src.store import transcript_filename, write_transcript_metadata


def get_video_title(video_id, timeout=10):
    """Look up the video title. Network failures fall back to the video ID."""
    url = (
        "https://www.youtube.com/oembed"
        f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
    )
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.load(response)
        title = data.get("title")
        return str(title).strip() if title else video_id
    except Exception:
        return video_id


def _snippet_text(snippet):
    if isinstance(snippet, dict):
        return snippet.get("text", "")
    return getattr(snippet, "text", "")


def fetch_transcript_text(video_id, api=None):
    """Return the transcript text for *video_id* (Hindi preferred, then English)."""
    if api is None:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "youtube-transcript-api is not installed. "
                "Run: pip install -r requirements.txt"
            ) from exc
        api = YouTubeTranscriptApi()

    transcript_list = api.list(video_id)

    try:
        transcript = transcript_list.find_transcript(["hi", "en"])
    except Exception:
        try:
            transcript = transcript_list.find_transcript(["en", "hi"])
        except Exception:
            available = list(transcript_list)
            if not available:
                raise RuntimeError(f"No transcript is available for video {video_id}")
            transcript = available[0]

    fetched = transcript.fetch()
    text = " ".join(
        part.strip() for part in (_snippet_text(item) for item in fetched) if part
    )
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise RuntimeError(f"The transcript for video {video_id} is empty")
    return text


def fetch_video_transcript(
    video_id,
    transcripts_dir=None,
    api=None,
    title_lookup=None,
):
    """Fetch and persist one transcript. Returns the saved path."""
    video_id = str(video_id or "").strip()
    if not video_id:
        raise ValueError("A YouTube video ID is required")

    directory = ensure_directory(get_transcripts_dir(transcripts_dir))
    lookup = title_lookup or get_video_title
    title = lookup(video_id) or video_id

    text = fetch_transcript_text(video_id, api=api)

    path = directory / transcript_filename(video_id, title)
    path.write_text(text, encoding="utf-8")
    write_transcript_metadata(
        path,
        {
            "video_id": video_id,
            "video_title": title,
            "transcript_file": path.name,
            "characters": len(text),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return path


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Fetch a YouTube transcript.")
    parser.add_argument("video_id", help="YouTube video ID (the part after v=)")
    args = parser.parse_args(argv)

    print(f"Fetching transcript for {args.video_id}...")
    try:
        path = fetch_video_transcript(args.video_id)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Saved transcript to: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
