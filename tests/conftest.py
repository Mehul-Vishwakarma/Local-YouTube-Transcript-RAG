import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def make_index():
    """Create a chunk manifest and embeddings file for one fake video."""

    def _make(chunks_dir, dirname, video_id, video_title, entries):
        video_dir = Path(chunks_dir) / dirname
        video_dir.mkdir(parents=True, exist_ok=True)

        manifest_chunks = []
        embedding_rows = []
        for chunk_id, text, embedding in entries:
            manifest_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": text,
                    "video_id": video_id,
                    "video_title": video_title,
                    "source": f"{video_id}.txt",
                }
            )
            embedding_rows.append(
                {
                    "chunk_id": chunk_id,
                    "text": text,
                    "video_id": video_id,
                    "video_title": video_title,
                    "source": f"{video_id}.txt",
                    "embedding": embedding,
                }
            )

        (video_dir / "chunks.json").write_text(
            json.dumps(
                {
                    "video_id": video_id,
                    "video_title": video_title,
                    "source": f"{video_id}.txt",
                    "chunks": manifest_chunks,
                }
            ),
            encoding="utf-8",
        )
        (video_dir / "embeddings.json").write_text(
            json.dumps(embedding_rows),
            encoding="utf-8",
        )
        return video_dir

    return _make
