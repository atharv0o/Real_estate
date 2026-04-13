from __future__ import annotations

import os

import requests


RAG_API = os.getenv("RAG_API", "http://localhost:8001").rstrip("/")
RAG_QUERY_URL = os.getenv("RAG_QUERY_URL", f"{RAG_API}/rag-query")
RAG_REFRESH_URL = os.getenv("RAG_REFRESH_URL", f"{RAG_API}/refresh-index")


def call_rag(query: str) -> dict:
    response = requests.post(RAG_QUERY_URL, json={"query": query}, timeout=20)
    response.raise_for_status()
    return response.json()


def refresh_rag_index() -> dict:
    response = requests.post(RAG_REFRESH_URL, timeout=10)
    response.raise_for_status()
    return response.json()
