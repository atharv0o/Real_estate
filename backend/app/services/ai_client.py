from __future__ import annotations

import os

import requests


RAG_API = os.getenv("RAG_API", "http://127.0.0.1:8001").rstrip("/")
RAG_URL = os.getenv("RAG_QUERY_URL", f"{RAG_API}/rag-query")


def ask_ai(query: str) -> dict:
    try:
        response = requests.post(RAG_URL, json={"query": query}, timeout=5)
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"answer": str(payload)}
    except Exception as exc:
        return {"error": str(exc)}
