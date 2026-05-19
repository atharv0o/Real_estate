from fastapi import FastAPI
from services.verifier import verify_property
from scripts.verify_data import fetch_verification_history, fetch_verification_record, verify_hashes
import uvicorn

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok", "service": "blockchain"}

@app.post("/verify")
def verify(data: dict):
    return verify_property(data)


@app.get("/proof")
def proof(app_id: int | None = None):
    return {"verified": True, "record": fetch_verification_record(app_id)}


@app.get("/history")
def history(app_id: int | None = None, limit: int = 10):
    return fetch_verification_history(app_id, limit)


@app.post("/verify-hashes")
def verify_stored_hashes(data: dict):
    return verify_hashes(
        expected_property_hash=str(data.get("propertyHash") or data.get("property_hash") or ""),
        expected_document_hash=str(data.get("documentHash") or data.get("document_hash") or ""),
        app_id=data.get("appId") or data.get("app_id"),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
