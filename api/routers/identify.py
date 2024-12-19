from typing import Optional
from urllib.parse import urlparse

import httpx
from fastapi import Request
from user_agents import parse
from uuid_extensions import uuid7str  # type: ignore

from api.times import utc_now

from ..common import sha256sum
from ..database.types import Event


def get_country_from_ip(ip_address):
    response = httpx.get(f"https://ipinfo.io/{ip_address}/json")
    if response.status_code == 200:
        data = response.json()
        return {
            "country": data.get("country"),
            "region": data.get("region"),
            "city": data.get("city"),
        }
    else:
        return {"error": "Unable to fetch IP information"}


async def identify(request: Request, property_id: Optional[str] = None):
    data = await request.json()
    event_type = data.get("event_type", "page_view")
    page_url = data.get("page_url", "unknown")
    referrer = request.headers.get("referrer", None)
    user_agent_str = request.headers.get("user-agent", None)
    user_agent = parse(user_agent_str)
    hashed_user_agent = sha256sum(user_agent_str) if user_agent_str else None
    accept_language = request.headers.get("accept-language", None)
    ip_address = request.client.host
    hashed_ip_address = sha256sum(ip_address)
    event_uid = uuid7str()
    hashed_accept_language = sha256sum(accept_language) if accept_language else None
    parsed = urlparse(page_url)
    domain = parsed.netloc
    page_path = parsed.path

    unique_user_id = sha256sum(
        f"{hashed_user_agent}{hashed_ip_address}{hashed_accept_language}{domain}"
    )
    date_hour = utc_now().strftime("%Y-%m-%d-%H")
    session_id = sha256sum(
        f"{date_hour}{hashed_user_agent}{hashed_ip_address}{hashed_accept_language}{domain}"
    )
    browser = user_agent.browser.family
    os = user_agent.os.family
    device = user_agent.device.family
    is_mobile = user_agent.is_mobile
    is_tablet = user_agent.is_tablet
    is_pc = user_agent.is_pc
    is_bot = user_agent.is_bot

    country = get_country_from_ip(ip_address)

    return Event(
        id=event_uid,
        event_type=event_type,
        page_url=page_url,
        referrer=referrer,
        user_agent=user_agent_str,
        hashed_user_agent=hashed_user_agent,
        accept_language=accept_language,
        hashed_ip_address=hashed_ip_address,
        unique_user_id=unique_user_id,
        domain=domain,
        browser=browser,
        os=os,
        device=device,
        is_mobile=is_mobile,
        is_tablet=is_tablet,
        is_pc=is_pc,
        is_bot=is_bot,
        country=country.get("country"),
        region=country.get("region"),
        city=country.get("city"),
        property_id=property_id,
        page_path=page_path,
        session_id=session_id,
    )
