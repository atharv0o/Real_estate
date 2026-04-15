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
    import json
    import os

    if os.getenv("PIPELINE_IMPORT_CSV", "").strip().lower() in {"1", "true", "yes", "on"}:
        from data_pipeline.import_csv_listings import run_import

        skip_db = os.getenv("PIPELINE_IMPORT_CSV_NO_DB", "").strip().lower() in {"1", "true", "yes", "on"}
        skip_json = os.getenv("PIPELINE_IMPORT_CSV_NO_JSON", "").strip().lower() in {"1", "true", "yes", "on"}
        print(json.dumps(run_import(limit=None, json_out=not skip_json, db_load=not skip_db), indent=2))
        return

    from data_pipeline.scheduler import main as scheduler_main

    scheduler_main()


if __name__ == "__main__":
    main()
