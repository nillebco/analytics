import hashlib
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from uuid_extensions import uuid7str  # type: ignore

from ..constants import ANALYTICS_API
from ..database.sql import collect, get_property_by_id

router = APIRouter(prefix=ANALYTICS_API)

SECONDS_IN_A_DAY = 86400


@router.post("/collect")
async def collect_analytics(request: Request, property_id: Optional[str] = None):
    property = await get_property_by_id(property_id)
    if not property:
        return JSONResponse({"status": "not found"}, status_code=404)

    data = await request.json()
    event_type = data.get("event_type", "page_view")
    page_url = data.get("page_url", "unknown")
    referrer = data.get("referrer", None)
    user_agent = request.headers.get("user-agent", None)
    hashed_user_agent = (
        hashlib.sha256(user_agent.encode()).hexdigest() if user_agent else None
    )
    uid = uuid7str()
    await collect(uid, event_type, page_url, hashed_user_agent, referrer, property_id)

    return {"status": "success", "messsage": "Thank you!"}
