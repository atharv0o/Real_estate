from fastapi import APIRouter, Query

from app.services.property_service import list_properties

router = APIRouter()


@router.get("/properties")
def get_properties(limit: int = Query(default=100, le=500), offset: int = Query(default=0, ge=0)):
    properties = list_properties(limit=limit, offset=offset)
    return {"count": len(properties), "properties": properties}
