from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from starlette.datastructures import Address, Headers

from api.database import sql
from api.routers.identify import identify, without_query

VISITOR = Headers(
    {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/605.1.15",
        "accept-language": "fr-FR,fr;q=0.9",
        "x-forwarded-for": "203.0.113.7, 10.0.0.1",
    }
)
CLIENT = Address("10.0.0.1", 1234)


def at(day: int):
    return patch(
        "api.database.sql.utc_now",
        return_value=datetime(2026, 11, day, 9, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_stores_no_ip_and_strips_query_strings(async_session):
    sql._SALT_CACHE.clear()
    with at(19):
        event = await identify(
            {
                "page_url": "https://pressto.app/?token=secret#x",
                "referrer": "https://mail.example/?u=a@b.c",
            },
            VISITOR,
            CLIENT,
            "p",
        )
    assert event.page_url == "https://pressto.app/"
    assert event.referrer == "https://mail.example/"
    assert event.hashed_ip_address is None
    assert event.region is None and event.city is None
    assert "203.0.113.7" not in repr(event.model_dump())


@pytest.mark.asyncio
async def test_visitor_id_is_stable_within_a_day_and_rotates_across_days(async_session):
    sql._SALT_CACHE.clear()
    with at(19):
        first = await identify(
            {"page_url": "https://pressto.app/"}, VISITOR, CLIENT, "p"
        )
        again = await identify(
            {"page_url": "https://pressto.app/faq"}, VISITOR, CLIENT, "p"
        )
    with at(20):
        tomorrow = await identify(
            {"page_url": "https://pressto.app/"}, VISITOR, CLIENT, "p"
        )
    assert first.unique_user_id == again.unique_user_id
    assert first.unique_user_id != tomorrow.unique_user_id


@pytest.mark.asyncio
async def test_only_todays_salt_is_kept(async_session):
    sql._SALT_CACHE.clear()
    with at(19):
        yesterday = await sql.daily_salt()
    with at(20):
        today = await sql.daily_salt()
    async with sql.session_scope() as session:
        rows = (await session.execute(sql.select(sql.DailySalt))).scalars().all()
    assert [r.day for r in rows] == ["2026-11-20"]
    assert yesterday != today


@pytest.mark.asyncio
async def test_retention_deletes_events_older_than_13_months(async_session):
    from api.database.types import Event, Property, User

    async with sql.session_scope() as session:
        session.add(User(id="u", name="n", email="e"))
        session.add(Property(id="p", slug="s", owner_id="u"))
        await session.commit()
    old = Event(
        id="old",
        event_type="page_view",
        page_url="/",
        property_id="p",
        timestamp=datetime(2024, 12, 1, tzinfo=timezone.utc),
    )
    new = Event(id="new", event_type="page_view", page_url="/", property_id="p")
    await sql.collect(old)
    await sql.collect(new)
    await sql.cleanup_old_data()
    async with sql.session_scope() as session:
        ids = [e.id for e in (await session.execute(sql.select(Event))).scalars().all()]
    assert ids == ["new"]


def test_without_query_keeps_relative_paths():
    assert without_query("/a/b?c=d") == "/a/b"
    assert without_query(None) is None
