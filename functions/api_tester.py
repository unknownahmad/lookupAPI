# ==========================================
# FINAL CODE
# ==========================================

import json
import time
from urllib.parse import urlparse

import requests

DEFAULT_USER_AGENT = "LOOKUPAPI/1.0 (Python Desktop API Explorer; University Course Project)"
DEFAULT_TIMEOUT = 15
SUPPORTED_METHODS = ("GET", "POST", "PUT", "DELETE")
MAX_RESPONSE_DISPLAY_CHARS = 250_000


def build_default_request(api):
    """Build initial request method, URL, query parameters, headers, and empty body from a catalogue entry."""
    safe_api = api if isinstance(api, dict) else {}
    base_url = str(safe_api.get("base_url") or "").strip().rstrip("/")
    endpoint = str(safe_api.get("working_get_endpoint") or "").strip()
    if endpoint and not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    full_url = base_url + endpoint if base_url else endpoint

    raw_params = safe_api.get("example_query_parameters")
    params = {}
    if isinstance(raw_params, dict):
        for key, value in raw_params.items():
            clean_key = str(key or "").strip()
            if clean_key:
                params[clean_key] = str(value)

    headers = {
        "Accept": "application/json",
        "User-Agent": DEFAULT_USER_AGENT,
    }
    raw_headers = safe_api.get("default_headers") or safe_api.get("headers")
    if isinstance(raw_headers, dict):
        for key, value in raw_headers.items():
            clean_key = str(key or "").strip()
            if clean_key:
                headers[clean_key] = str(value)

    return {
        "method": "GET",
        "url": full_url,
        "params": params,
        "headers": headers,
        "body": "",
    }


def validate_request_url(url):
    """Validate that the request URL is a non-empty http or https URL with a valid host and port."""
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

    return True, cleaned


def validate_request_headers(headers):
    """Clean and validate request headers, rejecting CR/LF control characters."""
    clean_headers = {}
    if not isinstance(headers, dict):
        return True, clean_headers, ""

    for key, value in headers.items():
        clean_key = str(key or "").strip()
        if not clean_key:
            continue
        clean_val = str(value if value is not None else "")
        if any(ch in clean_key or ch in clean_val for ch in ("\r", "\n")):
            return False, {}, f"Invalid header '{clean_key.splitlines()[0]}': header names and values cannot contain newline characters."
        clean_headers[clean_key] = clean_val

    return True, clean_headers, ""


def validate_json_body(raw_body):
    """Validate an optional JSON request body string before sending POST or PUT requests."""
    if raw_body is None:
        return True, None, ""
    if not isinstance(raw_body, str):
        return True, raw_body, ""

    cleaned = raw_body.strip()
    if not cleaned:
        return True, None, ""

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as err:
        return False, None, f"Invalid JSON body (line {err.lineno}, column {err.colno}): {err.msg}."

    return True, parsed, ""


def format_response_body(response, max_chars=MAX_RESPONSE_DISPLAY_CHARS):
    """Format a requests.Response body as pretty JSON when valid, otherwise raw text."""
    headers = getattr(response, "headers", None) or {}
    content_type = str(headers.get("Content-Type") or "").lower()
    raw_text = getattr(response, "text", None) or ""
    stripped = raw_text.lstrip()

    formatted_text = raw_text
    is_json = False
    warning = ""

    expects_json = "json" in content_type or stripped.startswith(("{", "["))
    if expects_json and stripped:
        try:
            parsed = json.loads(raw_text)
            formatted_text = json.dumps(parsed, indent=2, ensure_ascii=False)
            is_json = True
        except ValueError:
            if "json" in content_type:
                warning = "Response declared JSON content type, but body was not valid JSON. Showing raw text."

    if max_chars and len(formatted_text) > max_chars:
        trunc_note = f"Response exceeded {max_chars:,} characters and was truncated for display."
        formatted_text = formatted_text[:max_chars] + f"\n\n... [Truncated: {trunc_note}]"
        warning = f"{warning} {trunc_note}".strip()

    return formatted_text, is_json, warning


def send_api_request(method, url, params=None, headers=None, json_body=None, timeout=DEFAULT_TIMEOUT):
    """Send a single GET, POST, PUT, or DELETE request and return a structured result dictionary."""
    clean_method = str(method or "GET").strip().upper()
    if clean_method not in SUPPORTED_METHODS:
        return {
            "ok": False,
            "method": clean_method,
            "status_code": None,
            "reason": "Unsupported Method",
            "response_time_ms": 0.0,
            "is_json": False,
            "body": "",
            "error": f"Unsupported HTTP method '{clean_method}'. Choose GET, POST, PUT, or DELETE.",
            "rate_limited": False,
            "final_url": "",
        }

    is_valid_url, validated_or_err = validate_request_url(url)
    if not is_valid_url:
        return {
            "ok": False,
            "method": clean_method,
            "status_code": None,
            "reason": "",
            "response_time_ms": 0.0,
            "is_json": False,
            "body": "",
            "error": validated_or_err,
            "rate_limited": False,
            "final_url": "",
        }

    parsed_json_payload = None
    if clean_method in ("POST", "PUT"):
        is_valid_json, parsed_json_payload, json_err = validate_json_body(json_body)
        if not is_valid_json:
            return {
                "ok": False,
                "method": clean_method,
                "status_code": None,
                "reason": "Invalid JSON",
                "response_time_ms": 0.0,
                "is_json": False,
                "body": "",
                "error": json_err,
                "rate_limited": False,
                "final_url": validated_or_err,
            }

    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        return {
            "ok": False,
            "method": clean_method,
            "status_code": None,
            "reason": "Invalid Timeout",
            "response_time_ms": 0.0,
            "is_json": False,
            "body": "",
            "error": "Request timeout must be a positive number of seconds.",
            "rate_limited": False,
            "final_url": validated_or_err,
        }

    clean_params = {}
    if isinstance(params, dict):
        for key, value in params.items():
            clean_key = str(key or "").strip()
            if clean_key:
                clean_params[clean_key] = str(value if value is not None else "")

    headers_ok, clean_headers, header_err = validate_request_headers(headers)
    if not headers_ok:
        return {
            "ok": False,
            "method": clean_method,
            "status_code": None,
            "reason": "Invalid Header",
            "response_time_ms": 0.0,
            "is_json": False,
            "body": "",
            "error": header_err,
            "rate_limited": False,
            "final_url": validated_or_err,
        }

    start = time.perf_counter()
    try:
        response = requests.request(
            clean_method,
            validated_or_err,
            params=clean_params or None,
            headers=clean_headers or None,
            json=parsed_json_payload,
            timeout=timeout,
        )
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    except requests.exceptions.InvalidHeader as err:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        return {
            "ok": False,
            "method": clean_method,
            "status_code": None,
            "reason": "Invalid Header",
            "response_time_ms": elapsed_ms,
            "is_json": False,
            "body": "",
            "error": f"Invalid request header: {err}",
            "rate_limited": False,
            "final_url": validated_or_err,
        }
    except requests.exceptions.InvalidURL as err:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        return {
            "ok": False,
            "method": clean_method,
            "status_code": None,
            "reason": "Invalid URL",
            "response_time_ms": elapsed_ms,
            "is_json": False,
            "body": "",
            "error": f"Invalid request URL: {err}",
            "rate_limited": False,
            "final_url": validated_or_err,
        }
    except requests.exceptions.Timeout:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        return {
            "ok": False,
            "method": clean_method,
            "status_code": None,
            "reason": "Timeout",
            "response_time_ms": elapsed_ms,
            "is_json": False,
            "body": "",
            "error": f"Request timed out after {timeout} seconds. The server did not respond in time.",
            "rate_limited": False,
            "final_url": validated_or_err,
        }
    except requests.exceptions.ConnectionError as err:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        return {
            "ok": False,
            "method": clean_method,
            "status_code": None,
            "reason": "Connection Error",
            "response_time_ms": elapsed_ms,
            "is_json": False,
            "body": "",
            "error": f"Connection failed: could not reach host ({err}).",
            "rate_limited": False,
            "final_url": validated_or_err,
        }
    except requests.exceptions.RequestException as err:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        return {
            "ok": False,
            "method": clean_method,
            "status_code": None,
            "reason": "Request Error",
            "response_time_ms": elapsed_ms,
            "is_json": False,
            "body": "",
            "error": f"Request failed: {err}",
            "rate_limited": False,
            "final_url": validated_or_err,
        }

    formatted_body, is_json, parse_warning = format_response_body(response)
    status_code = response.status_code
    reason = str(response.reason or "")

    if status_code == 429:
        retry_after = response.headers.get("Retry-After")
        retry_note = f" Retry after {retry_after}s." if retry_after else " Please wait before trying again."
        return {
            "ok": False,
            "method": clean_method,
            "status_code": 429,
            "reason": reason or "Too Many Requests",
            "response_time_ms": elapsed_ms,
            "is_json": is_json,
            "body": formatted_body,
            "error": f"Rate limit exceeded (HTTP 429 Too Many Requests).{retry_note}",
            "rate_limited": True,
            "final_url": str(response.url),
        }

    if status_code >= 400:
        return {
            "ok": False,
            "method": clean_method,
            "status_code": status_code,
            "reason": reason,
            "response_time_ms": elapsed_ms,
            "is_json": is_json,
            "body": formatted_body,
            "error": f"HTTP {status_code} {reason}: the server returned an error response.".strip(),
            "rate_limited": False,
            "final_url": str(response.url),
        }

    return {
        "ok": True,
        "method": clean_method,
        "status_code": status_code,
        "reason": reason or "OK",
        "response_time_ms": elapsed_ms,
        "is_json": is_json,
        "body": formatted_body,
        "error": parse_warning,
        "rate_limited": False,
        "final_url": str(response.url),
    }


def send_get_request(url, params=None, headers=None, timeout=DEFAULT_TIMEOUT):
    """Send a single GET request and return a structured result dictionary."""
    return send_api_request("GET", url, params=params, headers=headers, timeout=timeout)
