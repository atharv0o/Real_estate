from fastapi import FastAPI
from pydantic import BaseModel
from pipeline.rag_pipeline import run_rag

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/rag-query")
def rag_query(req: QueryRequest):
    result = run_rag(req.query)
    return {"answer": result}