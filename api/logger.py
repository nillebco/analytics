import logging

from .constants import APP_NAME


def init_logger():
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.INFO)
    # set a format that includes the timestamp and the log level
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # set formatter to the logger
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logging.basicConfig(level=logging.INFO)
    return logger


logger = init_logger()
