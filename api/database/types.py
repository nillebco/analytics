from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from ..times import utc_now


class AnalyticsEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=utc_now)
    event_type: str
    page_url: str
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
