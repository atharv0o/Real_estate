from fastapi import FastAPI
from services.verifier import verify_property
import uvicorn

app = FastAPI()

@app.post("/verify")
def verify(data: dict):
    return verify_property(data)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
