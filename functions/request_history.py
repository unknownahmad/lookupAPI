# ==========================================
# FINAL CODE
# ==========================================

from datetime import datetime
import json
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

HISTORY_FILE = "data/test_request_history.json"
MASK_VALUE = "REDACTED"
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
    "x-api-key",
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
        if key.strip().lower() in SENSITIVE_QUERY_PARAMS:
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

    return {
        "api_name": str(api_name or "Custom Request").strip() or "Custom Request",
        "method": str(method or safe_result.get("method") or "GET").strip().upper(),
        "url": mask_sensitive_query_params(raw_url),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status_code": int(status_code) if isinstance(status_code, int) else None,
        "response_time_ms": round(float(response_time), 1) if isinstance(response_time, (int, float)) else None,
        "success": bool(safe_result.get("ok", False)),
    }


def load_request_history(file_path=HISTORY_FILE):
    """Load saved API tester request history safely, tolerating missing, empty, or malformed files."""
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            raw_content = file.read().strip()
        if not raw_content:
            return []
        data = json.loads(raw_content)
    except (OSError, ValueError) as error:
        print("Warning: Could not read request history file:", error)
        return []

    if not isinstance(data, list):
        print("Warning: Request history file format is invalid (expected a JSON list).")
        return []

    return [entry for entry in data if isinstance(entry, dict)]


def save_request_history(api_name, method, url, result, file_path=HISTORY_FILE):
    """Append a single request summary entry to the JSON request history file."""
    entry = build_history_entry(api_name, method, url, result)
    history = load_request_history(file_path=file_path)
    history.append(entry)

    parent_dir = os.path.dirname(file_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=2, ensure_ascii=False)
    except OSError as error:
        print("Warning: Could not save request history:", error)
        return None

    return entry
