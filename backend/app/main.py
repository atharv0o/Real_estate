from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.postgres import initialize_database
from app.routes import ai, property, rag_query, search, verify
from app.services.search_index import benchmark_search, warm_search_structures


app = FastAPI(title="Real Estate Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REGISTER ROUTES
app.include_router(search.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(verify.router, prefix="/api")
app.include_router(property.router, prefix="/api")
app.include_router(rag_query.router)


@app.on_event("startup")
def _startup_warmup() -> None:
    initialize_database()
    warm_search_structures()
    if os.getenv("ENABLE_SEARCH_BENCHMARK", "0") == "1":
        benchmark_search()


@app.get("/")
def root():
    return {"message": "Backend running successfully"}
