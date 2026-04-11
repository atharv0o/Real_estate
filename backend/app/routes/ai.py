from fastapi import APIRouter
from app.services.ai_client import ask_ai

router = APIRouter()

@router.post("/ask")
def ask_ai_route(data: dict):
    query = data.get("query", "")
    return ask_ai(query)