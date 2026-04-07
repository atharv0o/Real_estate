from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

from rag.vectorstore import load_index
from rag.chain import query_properties
from blockchain.algorand import verify

app = FastAPI(title="PropSight AI Service")

app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup():
    load_index()
    print("FAISS index loaded.")

class QueryRequest(BaseModel):
    query: str
    city: str = ""

@app.post("/query")
async def query(req: QueryRequest):
    q = f"{req.city} {req.query}".strip()
    return query_properties(q)

@app.get("/verify/{txn_id}")
async def verify_txn(txn_id: str):
    return verify(txn_id)

@app.get("/health")
async def health():
    return {"status": "ok"}