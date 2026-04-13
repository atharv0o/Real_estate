from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import ai, property, search, verify

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


@app.get("/")
def root():
    return {"message": "Backend running successfully"}
