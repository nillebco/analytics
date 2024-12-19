import os
import sys

from .common import generate_guid

AUTHOR = "Ivo Bellin Salarin <ivo@nilleb.com>"
APP_NAME = "analytics"

IS_TESTING: bool = "pytest" in sys.modules
IS_DEV: bool = os.getenv("IS_DEV") == "true"
DATA_FOLDER: str = "data"
API_PREFIX: str = "/api/v1"

ANALYTICS_API: str = "/analytics"

OWNER_NAME = "Ivo Bellin Salarin"
OWNER_EMAIL = "ivo@nilleb.com"
PROPERTY_SLUG = "default"

ANALYTICS_HOST_PROPERTY_SLUG = "analytics"
NOT_AUTHORIZED = "Not Authorized"
DEFAULT_PROPERTY_ID = generate_guid(OWNER_EMAIL + PROPERTY_SLUG)
ANALYTICS_PROPERTY_ID = generate_guid(OWNER_EMAIL + ANALYTICS_HOST_PROPERTY_SLUG)
