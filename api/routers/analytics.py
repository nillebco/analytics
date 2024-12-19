from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..constants import ANALYTICS_API
from ..database.sql import collect, get_property_by_id
from .identify import identify

router = APIRouter(prefix=ANALYTICS_API)

SECONDS_IN_A_DAY = 86400


@router.post("/collect")
async def collect_analytics(request: Request, property_id: Optional[str] = None):
    property = await get_property_by_id(property_id)
    if not property:
        return JSONResponse({"status": "not found"}, status_code=404)

    data = await request.json()
    event = await identify(data, request.headers, request.client, property_id)
    await collect(event)

    return {"status": "success", "messsage": "Thank you!"}
