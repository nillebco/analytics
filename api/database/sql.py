import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import AsyncGenerator, Optional

from sqlalchemy.exc import InterfaceError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel
from sqlmodel.sql.expression import _T, SelectOfScalar

from ..constants import IS_TESTING
from ..logger import logger
from ..secrets import DATABASE_URL
from ..times import utc_now
from .types import AnalyticsEvent

IN_MEMORY_DATABASE = "sqlite+aiosqlite://"
connection_string = (
    IN_MEMORY_DATABASE if IS_TESTING or not DATABASE_URL else DATABASE_URL
)
if connection_string == IN_MEMORY_DATABASE:
    logger.warning("Using in-memory database")

engine: AsyncEngine = create_async_engine(connection_string, echo=True)
async_session = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)

SESSION_HORIZON = {"minutes": 60}
MAXIMUM_SESSION_DURATION = {"minutes": 30}


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    session: AsyncSession = async_session()
    try:
        yield session
        await session.commit()
    except:
        await session.rollback()
        raise
    finally:
        await session.close()


async def recreate_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_tables():
    async with engine.begin():
        await engine.run_sync(SQLModel.metadata.drop_all, engine)


async def execute_statement(session: AsyncSession, stmt: SelectOfScalar[_T]):
    for _ in range(3):
        try:
            return await session.execute(stmt)
        except InterfaceError:
            await asyncio.sleep(0.1)


async def collect(
    event_type: str,
    page_url: Optional[str] = None,
    user_agent: Optional[str] = None,
    referrer: Optional[str] = None,
):
    async with session_scope() as session:
        event = AnalyticsEvent(
            event_type=event_type,
            page_url=page_url,
            referrer=referrer,
            user_agent=user_agent,
        )

        session.add(event)
        session.commit()


async def cleanup_old_data():
    retention_period = timedelta(days=180)
    cutoff_date = utc_now() - retention_period
    async with session_scope() as session:
        await execute_statement(
            session,
            "DELETE FROM analytics WHERE timestamp < :cutoff_date",
            {"cutoff_date": cutoff_date},
        )
        session.commit()
