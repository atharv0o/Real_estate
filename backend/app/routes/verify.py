from fastapi import APIRouter
from app.services.verify_service import verify_property

router = APIRouter()

@router.post("/verify")
def verify(data: dict):
    return verify_property(data)