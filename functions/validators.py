# ==========================================
# FINAL CODE
# ==========================================

import re
from urllib.parse import urlparse

from functions.models import APIResource

HEADER_NAME_REGEX = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def validate_request_url(url):
    """Validate that a request URL is a non-empty http(s) URL with a valid host and port."""
    cleaned = str(url or "").strip()
    if not cleaned:
        return False, "Request URL cannot be empty."
    if any(ch.isspace() for ch in cleaned):
        return False, "Request URL cannot contain spaces."

    try:
        parsed = urlparse(cleaned)
        port = parsed.port
    except ValueError:
        return False, "Request URL contains an invalid port number."

    if parsed.scheme not in ("http", "https") or not parsed.netloc or not parsed.hostname:
        return False, "Please enter a valid URL starting with http:// or https:// and a host name."
    if port is not None and not (1 <= port <= 65535):
        return False, "Request URL port must be between 1 and 65535."
    if not APIResource.validate_url(cleaned):
        return False, "Please enter a valid http:// or https:// URL with a valid host name."

    return True, cleaned


def validate_request_headers(headers):
    """Clean and validate request headers using RFC header-name regex and newline checks."""
    clean_headers = {}
    if not isinstance(headers, dict):
        return True, clean_headers, ""

    for key, value in headers.items():
        clean_key = str(key or "").strip()
        if not clean_key:
            continue
        clean_val = str(value if value is not None else "")
        if any(ch in clean_key or ch in clean_val for ch in ("\r", "\n")):
            safe_name = clean_key.splitlines()[0]
            return (
                False,
                {},
                f"Invalid header '{safe_name}': header names and values cannot contain newline characters.",
            )
        if not HEADER_NAME_REGEX.match(clean_key):
            return (
                False,
                {},
                f"Invalid header name '{clean_key}': use valid HTTP header token characters only.",
            )
        clean_headers[clean_key] = clean_val

    return True, clean_headers, ""
