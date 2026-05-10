from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    area: str = ""
    city: str = ""
    district: str = ""
    pincode: str = Field(default="", alias="pinCode")
    land_area_code: str = Field(default="", alias="landAreaCode")
    radius: float = Field(default=5.0, gt=0, le=200)
    min_price: Optional[float] = Field(default=None, ge=0, alias="minPrice")
    max_price: Optional[float] = Field(default=None, ge=0, alias="maxPrice")
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    page: int = Field(default=1, ge=1)
