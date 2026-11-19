"""Country lookup from a local database, so visitor IP addresses never leave the server.

The database is DB-IP's free "IP to Country Lite" (CC BY 4.0, https://db-ip.com), baked
into the image at build time. Only the country is kept: no region, no city.
"""

import os
from functools import lru_cache
from typing import Optional

import maxminddb

from .logger import logger

GEO_DB = os.environ.get("GEO_DB", "/app/geo/dbip-country-lite.mmdb")


@lru_cache(maxsize=1)
def _reader():
    try:
        return maxminddb.open_database(GEO_DB)
    except (FileNotFoundError, maxminddb.InvalidDatabaseError) as error:
        logger.warning(f"no country database at {GEO_DB}: {error}")
        return None


def country_of(ip_address: Optional[str]) -> Optional[str]:
    reader = _reader()
    if not reader or not ip_address:
        return None
    try:
        record = reader.get(ip_address)
    except ValueError:
        return None
    if not isinstance(record, dict):
        return None
    country = record.get("country")
    return country.get("iso_code") if isinstance(country, dict) else None
