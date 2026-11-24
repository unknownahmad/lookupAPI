from datetime import datetime
import os

from functions.logger import get_logger

ACTIVITY_FILE = "data/activity_log.txt"


def parse_optional_int(value):
    """Convert value to int when valid, otherwise return None."""
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_optional_float(value):
    """Convert value to float when valid, otherwise return None."""
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def save_activity(api_name, status, status_code="N/A", file_path=ACTIVITY_FILE):
    """Append a timestamped activity entry to the activity log file."""
    logger = get_logger("lookupapi.activity")
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{date} | {api_name} | {status} | {status_code}\n"

    try:
        parent_dir = os.path.dirname(file_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(entry)
    except OSError as error:
        logger.error("Could not save activity entry (%s).", type(error).__name__)
        return False

    logger.info("Activity entry recorded.")
    return True


def get_activity(file_path=ACTIVITY_FILE):
    """Read and return all lines stored in the activity log file."""
    logger = get_logger("lookupapi.activity")
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.readlines()
    except OSError as error:
        logger.error("Could not read activity log (%s).", type(error).__name__)
        return []
