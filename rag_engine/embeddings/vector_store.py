from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover
    faiss = None  # type: ignore


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if hasattr(value, "item") and callable(value.item):
        try:
            scalar = value.item()
        except Exception:
            return str(value)
        return _json_safe(scalar)
    return value


class VectorStore:
    def __init__(self, dim: int = 384, index_path: str | Path | None = None, metadata_path: str | Path | None = None):
        self.dim = dim
        self.index_path = Path(index_path) if index_path else None
        self.metadata_path = Path(metadata_path) if metadata_path else None
        self.ids: list[str] = []
        self.texts: list[str] = []
        self.metadata: list[dict[str, Any]] = []
        self._embeddings = np.empty((0, dim), dtype="float32")
        self.index = self._new_index()
        if self.index_path and self.metadata_path:
            self.load()

    def _new_index(self):
        if faiss is not None:
            return faiss.IndexFlatL2(self.dim)
        return None

    def _rebuild_index(self) -> None:
        if faiss is not None:
            self.index = faiss.IndexFlatL2(self.dim)
            if len(self._embeddings):
                self.index.add(self._embeddings.astype("float32"))

    def add(self, embeddings, texts):
        generated_ids = [f"doc-{len(self.ids) + index}" for index in range(len(texts))]
        self.upsert(generated_ids, embeddings, texts)

    def upsert(self, ids, embeddings, texts, metadata=None):
        metadata = metadata or [{} for _ in texts]
        vector_rows = np.array(embeddings, dtype="float32")
        if len(vector_rows.shape) == 1:
            vector_rows = np.expand_dims(vector_rows, axis=0)

        by_id = {
            current_id: (self._embeddings[index], self.texts[index], self.metadata[index])
            for index, current_id in enumerate(self.ids)
        }
        for row_id, embedding, text, meta in zip(ids, vector_rows, texts, metadata):
            by_id[str(row_id)] = (np.array(embedding, dtype="float32"), text, meta)

        ordered_ids = list(by_id.keys())
        self.ids = ordered_ids
        self._embeddings = np.array([by_id[row_id][0] for row_id in ordered_ids], dtype="float32")
        self.texts = [by_id[row_id][1] for row_id in ordered_ids]
        self.metadata = [by_id[row_id][2] for row_id in ordered_ids]
        self._rebuild_index()
        self.save()

    def search(self, query_embedding, k: int = 5):
        if not self.texts:
            return []

        query_vector = np.array([query_embedding], dtype="float32")
        if faiss is not None and self.index is not None:
            distances, indices = self.index.search(query_vector, min(k, len(self.texts)))
            return [self.texts[i] for i in indices[0] if 0 <= i < len(self.texts)]

        distances = np.linalg.norm(self._embeddings - query_vector[0], axis=1)
        top_indices = np.argsort(distances)[: min(k, len(self.texts))]
        return [self.texts[index] for index in top_indices]

    def load(self) -> None:
        if not self.metadata_path or not self.metadata_path.exists():
            return

        payload = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        self.ids = payload.get("ids", [])
        self.texts = payload.get("texts", [])
        self.metadata = payload.get("metadata", [])
        embeddings = payload.get("embeddings", [])
        self._embeddings = np.array(embeddings, dtype="float32") if embeddings else np.empty((0, self.dim), dtype="float32")

        if faiss is not None and self.index_path and self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        else:
            self._rebuild_index()

    def save(self) -> None:
        if not self.metadata_path:
            return

        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ids": self.ids,
            "texts": self.texts,
            "metadata": self.metadata,
            "embeddings": self._embeddings.tolist(),
        }
        self.metadata_path.write_text(json.dumps(_json_safe(payload), indent=2), encoding="utf-8")

        if faiss is not None and self.index_path and self.index is not None:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(self.index_path))
