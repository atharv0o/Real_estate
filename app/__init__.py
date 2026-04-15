"""Compatibility package that exposes ``backend/app`` as top-level ``app``."""

from __future__ import annotations

from pathlib import Path

_CURRENT_DIR = Path(__file__).resolve().parent
_BACKEND_APP_DIR = _CURRENT_DIR.parent / "backend" / "app"

__path__ = [str(_CURRENT_DIR)]
if _BACKEND_APP_DIR.is_dir():
    __path__.append(str(_BACKEND_APP_DIR))
