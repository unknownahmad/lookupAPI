import logging
import os

LOGGER_NAME = "lookupapi"
LOG_FILE = "data/lookupapi.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logger(name=LOGGER_NAME, log_file=LOG_FILE, level=logging.INFO):
    """Configure and return a Python logger with console and optional file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        try:
            parent_dir = os.path.dirname(log_file)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError as error:
            logger.warning("File logging unavailable (%s); continuing with console logging.", type(error).__name__)

    return logger


def get_logger(name=LOGGER_NAME):
    """Return a configured application logger without adding duplicate handlers."""
    configure_logger(LOGGER_NAME)
    if name == LOGGER_NAME:
        return logging.getLogger(LOGGER_NAME)
    return logging.getLogger(name)
