# ==========================================
# FINAL CODE
# ==========================================

from datetime import datetime
import json
import os
import tempfile
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from functions.decorators import log_execution
from functions.logger import get_logger

HISTORY_FILE = "data/test_request_history.json"
MASK_VALUE = "REDACTED"
MAX_HISTORY_ENTRIES = 200
SENSITIVE_QUERY_PARAMS = {
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "password",
    "passwd",
    "secret",
    "client_secret",
    "authorization",
    "auth_token",
    "x_api_key",
}


def mask_sensitive_query_params(url):
    """Mask values of common sensitive query parameters while preserving ordinary parameters."""
    cleaned = str(url or "").strip()
    if not cleaned or "?" not in cleaned:
        return cleaned

    parsed = urlsplit(cleaned)
    if not parsed.query:
        return cleaned

    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    masked_pairs = []
    changed = False

    for key, value in pairs:
        normalized_key = key.strip().lower().replace("-", "_")
        if normalized_key in SENSITIVE_QUERY_PARAMS:
            masked_pairs.append((key, MASK_VALUE))
            changed = True
        else:
            masked_pairs.append((key, value))

    if not changed:
        return cleaned

    masked_query = urlencode(masked_pairs)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, masked_query, parsed.fragment))


def build_history_entry(api_name, method, url, result):
    """Create a sanitized request history record without credentials or headers."""
    safe_result = result if isinstance(result, dict) else {}
    status_code = safe_result.get("status_code")
    response_time = safe_result.get("response_time_ms")
    raw_url = str(url or safe_result.get("final_url") or "").strip()

    valid_status = isinstance(status_code, int) and not isinstance(status_code, bool)
    valid_time = isinstance(response_time, (int, float)) and not isinstance(response_time, bool)

    return {
        "api_name": str(api_name or "Custom Request").strip() or "Custom Request",
        "method": str(method or safe_result.get("method") or "GET").strip().upper(),
        "url": mask_sensitive_query_params(raw_url),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status_code": int(status_code) if valid_status else None,
        "response_time_ms": round(float(response_time), 1) if valid_time else None,
        "success": bool(safe_result.get("ok", False)),
    }


def iter_request_history(file_path=HISTORY_FILE):
    """Yield valid request history records one by one from the JSON history file."""
    logger = get_logger("lookupapi.request_history")
    if not os.path.exists(file_path):
        return

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            raw_content = file.read().strip()
        if not raw_content:
            return
        data = json.loads(raw_content)
    except (OSError, ValueError) as error:
        logger.warning("Could not read request history file (%s).", type(error).__name__)
        return

    if not isinstance(data, list):
        logger.warning("Request history file format is invalid (expected a JSON list).")
        return

    for entry in data:
        if not isinstance(entry, dict):
            continue
        if not str(entry.get("url") or "").strip() and not str(entry.get("api_name") or "").strip():
            continue
        yield entry


def load_request_history(file_path=HISTORY_FILE):
    """Load saved API tester request history safely as a list."""
    return list(iter_request_history(file_path=file_path))


@log_execution
def save_request_history(api_name, method, url, result, file_path=HISTORY_FILE, max_entries=MAX_HISTORY_ENTRIES):
    """Append a sanitized request summary entry atomically to the JSON request history file."""
    logger = get_logger("lookupapi.request_history")
    entry = build_history_entry(api_name, method, url, result)
    history = load_request_history(file_path=file_path)
    history.append(entry)

    if isinstance(max_entries, int) and not isinstance(max_entries, bool) and max_entries > 0:
        history = history[-max_entries:]

    parent_dir = os.path.dirname(file_path) or "."
    tmp_path = None
    try:
        os.makedirs(parent_dir, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=parent_dir, prefix=".history_", suffix=".tmp", delete=False
        ) as tmp_file:
            tmp_path = tmp_file.name
            json.dump(history, tmp_file, indent=2, ensure_ascii=False)
        os.replace(tmp_path, file_path)
    except OSError as error:
        logger.error("Could not save request history (%s).", type(error).__name__)
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return None

    return entry
