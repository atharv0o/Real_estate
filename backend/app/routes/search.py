from fastapi import APIRouter
from app.services.data_service import get_properties

router = APIRouter()

@router.get("/search")
def search(lat: float, lng: float, radius: float):
    try:
        return get_properties(lat, lng, radius)
    except Exception as e:
        return {"error": str(e)}