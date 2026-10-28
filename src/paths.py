"""Project path helpers.

All default data locations are anchored to the project root, so commands work
no matter which directory the terminal was started from.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS_DIR = PROJECT_ROOT / "transcripts"
CHUNKS_DIR = PROJECT_ROOT / "chunks"


def ensure_directory(path):
    """Create *path* (including parents) and return it as a ``Path``."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_transcripts_dir(path=None):
    """Return the transcript directory.

    An explicit *path* wins. Otherwise ``YOUTUBE_RAG_TRANSCRIPTS_DIR`` may
    override the project default, which is ``<project-root>/transcripts``.
    """
    if path is not None:
        return Path(path).expanduser().resolve()
    override = os.environ.get("YOUTUBE_RAG_TRANSCRIPTS_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return TRANSCRIPTS_DIR


def get_chunks_dir(path=None):
    """Return the chunks directory.

    An explicit *path* wins. Otherwise ``YOUTUBE_RAG_CHUNKS_DIR`` may override
    the project default, which is ``<project-root>/chunks``.
    """
    if path is not None:
        return Path(path).expanduser().resolve()
    override = os.environ.get("YOUTUBE_RAG_CHUNKS_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return CHUNKS_DIR
