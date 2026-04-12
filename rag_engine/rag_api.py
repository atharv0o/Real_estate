from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_engine.pipeline.rag_pipeline import refresh_vector_store, run_rag

app = FastAPI()


class QueryRequest(BaseModel):
    query: str


@app.post("/rag-query")
def rag_query(req: QueryRequest):
    result = run_rag(req.query)
    return {"answer": result}


@app.post("/refresh-index")
def refresh_index():
    store = refresh_vector_store(force=True)
    return {"status": "refreshed", "documents": len(store.texts)}
