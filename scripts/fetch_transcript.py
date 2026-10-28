"""Compatibility wrapper for ``src.fetch_transcript``."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.fetch_transcript import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
