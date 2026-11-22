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


def build_default_request(api):
    """Build initial request method, URL, query parameters, headers, and empty body from a catalogue entry."""
    base_url = str(api.get("base_url") or "").strip().rstrip("/")
    endpoint = str(api.get("working_get_endpoint") or "").strip()
    if endpoint and not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    full_url = base_url + endpoint if base_url else endpoint

    raw_params = api.get("example_query_parameters")
    params = {}
    if isinstance(raw_params, dict):
        for key, value in raw_params.items():
            params[str(key)] = str(value)

    headers = {
        "Accept": "application/json",
        "User-Agent": DEFAULT_USER_AGENT,
    }
    raw_headers = api.get("default_headers") or api.get("headers")
    if isinstance(raw_headers, dict):
        for key, value in raw_headers.items():
            headers[str(key)] = str(value)

    return {
        "method": "GET",
        "url": full_url,
        "params": params,
        "headers": headers,
        "body": "",
    }


def validate_request_url(url):
    """Validate that the request URL is a non-empty http or https URL."""
    cleaned = str(url or "").strip()
    if not cleaned:
        return False, "Request URL cannot be empty."
    if any(ch.isspace() for ch in cleaned):
        return False, "Request URL cannot contain spaces."

    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False, "Please enter a valid URL starting with http:// or https://."

    return True, cleaned


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


def format_response_body(response):
    """Format a requests.Response body as pretty JSON when valid, otherwise raw text."""
    content_type = str(response.headers.get("Content-Type") or "").lower()
    raw_text = response.text or ""
    stripped = raw_text.lstrip()

    expects_json = "json" in content_type or stripped.startswith(("{", "["))
    if expects_json and stripped:
        try:
            parsed = json.loads(raw_text)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            return formatted, True, ""
        except ValueError:
            warning = ""
            if "json" in content_type:
                warning = "Response declared JSON content type, but body was not valid JSON. Showing raw text."
            return raw_text, False, warning

    return raw_text, False, ""


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

    clean_params = {}
    if isinstance(params, dict):
        for key, value in params.items():
            clean_key = str(key or "").strip()
            if clean_key:
                clean_params[clean_key] = str(value or "")

    clean_headers = {}
    if isinstance(headers, dict):
        for key, value in headers.items():
            clean_key = str(key or "").strip()
            if clean_key:
                clean_headers[clean_key] = str(value or "")

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
