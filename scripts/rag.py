"""Compatibility wrapper for ``src.rag``."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
