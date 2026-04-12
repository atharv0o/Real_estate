from fastapi import APIRouter, Query

from app.services.api_response import error_response, success_response
from app.services.property_service import get_property_details
from app.services.property_service import list_properties

router = APIRouter()


@router.get("/properties")
def get_properties(limit: int = Query(default=100, le=500), offset: int = Query(default=0, ge=0)):
    properties = list_properties(limit=limit, offset=offset)
    return success_response(properties)


@router.get("/property/{property_id}")
def get_property(property_id: str):
    try:
        property_record = get_property_details(property_id)
        if not property_record:
            return error_response("Property not found")
        return success_response(property_record)
    except Exception as exc:
        return error_response(str(exc))
