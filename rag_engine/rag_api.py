from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from rag_engine.pipeline.rag_pipeline import refresh_vector_store, run_rag

app = FastAPI()


class QueryRequest(BaseModel):
    query: str
    location: str | None = None
    property_context: dict | str | None = None


@app.post("/rag-query")
def rag_query(req: QueryRequest):
    result = run_rag(req.query, location=req.location, property_context=req.property_context)
    return {"answer": result}


@app.post("/refresh-index")
def refresh_index():
    store = refresh_vector_store(force=True)
    return {"status": "refreshed", "documents": len(store.texts)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
