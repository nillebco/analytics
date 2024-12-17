import os

import dotenv
import yaml

from .logger import logger

dotenv.load_dotenv()

PWD = os.path.dirname(os.path.abspath(__file__))
path = f"{PWD}/../secrets/secrets.yaml"

if not os.path.exists(path):
    _raw_configuration = {}
else:
    with open(path, "r") as stream:
        _raw_configuration = yaml.safe_load(stream)


def get_secret(lowercase_secret_name: str, default=None):
    if not default:
        default = ""

    uppercase = lowercase_secret_name.upper()
    secret = _raw_configuration.get(
        lowercase_secret_name, os.environ.get(uppercase, default)
    )

    return secret


DATABASE_URL = get_secret("DATABASE_URL")

checks = {
    "DATABASE_URL": DATABASE_URL,
}

for var_name, var_value in checks.items():
    if not var_value:
        logger.warning(
            "Unexpected: the variable {var_name} has the value '{var_value}'".format(
                var_name=var_name, var_value=var_value
            )
        )
