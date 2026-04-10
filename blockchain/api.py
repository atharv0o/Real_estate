from fastapi import FastAPI
from services.verifier import verify_property

app = FastAPI()

@app.post("/verify")
def verify(data: dict):
    return verify_property(data)