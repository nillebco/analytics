from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.types import TIMESTAMP
from sqlmodel import Field, Relationship, SQLModel

from ..times import utc_now


class User(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    email: str


class Property(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    slug: str
    owner_id: str = Field(foreign_key="user.id")
    owner: User = Relationship()


class Event(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        default_factory=utc_now,
    )
    event_type: str
    page_url: str
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    property_id: str = Field(foreign_key="property.id")
    property: Property = Relationship()
    accept_language: Optional[str] = None
    hashed_ip_address: Optional[str] = None
    unique_user_id: Optional[str] = None
    domain: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    device: Optional[str] = None
    is_mobile: Optional[bool] = None
    is_tablet: Optional[bool] = None
    is_pc: Optional[bool] = None
    is_bot: Optional[bool] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    page_path: Optional[str] = None
    session_id: Optional[str] = None
