import hashlib

from fastapi import APIRouter, Request

from ..constants import ANALYTICS_API
from ..database.sql import collect

router = APIRouter(prefix=ANALYTICS_API)

SECONDS_IN_A_DAY = 86400


@router.post("/collect")
async def collect_analytics(request: Request):
    data = await request.json()
    event_type = data.get("event_type", "page_view")
    page_url = data.get("page_url", "unknown")
    referrer = data.get("referrer", None)
    user_agent = request.headers.get("user-agent", None)
    hashed_user_agent = (
        hashlib.sha256(user_agent.encode()).hexdigest() if user_agent else None
    )
    await collect(event_type, page_url, hashed_user_agent, referrer)

    return {"status": "success", "messsage": "Thank you!"}
