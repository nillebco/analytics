from typing import Optional
from urllib.parse import urlparse

from starlette.datastructures import Address, Headers
from user_agents import parse
from uuid_extensions import uuid7str  # type: ignore

from api.times import utc_now

from ..common import sha256sum
from ..database.sql import daily_salt
from ..database.types import Event
from ..geo import country_of


def without_query(url: Optional[str]) -> Optional[str]:
    """scheme://host/path only: query strings and fragments can carry tokens or emails."""
    if not url:
        return url
    parsed = urlparse(url)
    if not parsed.scheme and not parsed.netloc:
        return parsed.path or None
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def client_ip(headers: Headers) -> Optional[str]:
    # the service is behind a reverse proxy; the first hop is the visitor
    forwarded = headers.get("x-forwarded-for")
    return forwarded.split(",")[0].strip() if forwarded else None


async def identify(
    data: dict, headers: Headers, client: Address, property_id: Optional[str] = None
):
    event_type = data.get("event_type", "page_view")
    page_url = without_query(data.get("page_url")) or "unknown"
    # the Referer header of the beacon is the tracked page itself: the visitor's
    # real source is document.referrer, sent by simple.js in the payload
    referrer = without_query(data.get("referrer")) or None
    user_agent_str = headers.get("user-agent", None)
    user_agent = parse(user_agent_str)
    accept_language = headers.get("accept-language", None)
    ip_address = client_ip(headers)
    event_uid = uuid7str()
    parsed = urlparse(page_url or "")  # force the type to be a string
    domain = parsed.netloc
    page_path = parsed.path

    # Visitor and session ids are salted with a random value that is replaced every UTC
    # day, so they count unique visitors per day without identifying anyone: the IP
    # address itself is never stored, and once the salt is gone the ids cannot be
    # recomputed from it.
    salt = await daily_salt()
    fingerprint = f"{user_agent_str}|{ip_address}|{accept_language}|{domain}"
    unique_user_id = sha256sum(f"{salt}|{fingerprint}")
    date_hour = utc_now().strftime("%Y-%m-%d-%H")
    session_id = sha256sum(f"{salt}|{date_hour}|{fingerprint}")
    browser = user_agent.browser.family
    os = user_agent.os.family
    device = user_agent.device.family
    is_mobile = user_agent.is_mobile
    is_tablet = user_agent.is_tablet
    is_pc = user_agent.is_pc
    is_bot = user_agent.is_bot

    country = country_of(ip_address)

    return Event(
        id=event_uid,
        event_type=event_type,
        page_url=page_url,
        referrer=referrer,
        user_agent=user_agent_str,
        accept_language=accept_language,
        unique_user_id=unique_user_id,
        domain=domain,
        browser=browser,
        os=os,
        device=device,
        is_mobile=is_mobile,
        is_tablet=is_tablet,
        is_pc=is_pc,
        is_bot=is_bot,
        country=country,
        property_id=property_id,
        page_path=page_path,
        session_id=session_id,
    )
