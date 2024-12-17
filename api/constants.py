import os
import sys

AUTHOR = "Ivo Bellin Salarin <ivo@nilleb.com>"
APP_NAME = "analytics"

IS_TESTING: bool = "pytest" in sys.modules
IS_DEV: bool = os.getenv("IS_DEV") == "true"
DATA_FOLDER: str = "data"
API_PREFIX: str = "/api/v1"

ANALYTICS_API: str = "/analytics"
