from fastapi import APIRouter, Query

from app.services.api_response import error_response, success_response
from app.services.blockchain_service import compute_record_hash, get_cached_verification, verify_property_with_hash
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
        verification_hash = compute_record_hash(
            str(property_record.get("title") or ""),
            str(property_record.get("location") or ""),
            str(property_record.get("price") or property_record.get("price_numeric") or ""),
        )
        verification = get_cached_verification(verification_hash) or verify_property_with_hash(
            str(property_record.get("title") or ""),
            str(property_record.get("location") or ""),
            str(property_record.get("price") or property_record.get("price_numeric") or ""),
        )
        property_record["verification_hash"] = verification_hash
        property_record["blockchain_verified"] = bool(verification.get("verified"))
        return success_response(property_record)
    except Exception as exc:
        return error_response(str(exc))
