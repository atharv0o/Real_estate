from __future__ import annotations

from typing import Any


def success_response(data: Any, status: str = "ok") -> dict[str, Any]:
    return {"success": True, "status": status, "data": data, "error": None}


def error_response(message: str, data: Any = None, status: str = "error") -> dict[str, Any]:
    return {"success": False, "status": status, "data": data, "error": message}
