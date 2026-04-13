from __future__ import annotations

import sys
from pathlib import Path


def ensure_project_root() -> Path:
    root = Path(__file__).resolve().parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


def main() -> None:
    ensure_project_root()
    from data_pipeline.scheduler import main as scheduler_main

    scheduler_main()


if __name__ == "__main__":
    main()
