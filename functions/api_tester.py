# ==========================================
# FINAL CODE
# ==========================================

import json
import time

import requests

from functions.decorators import log_execution
from functions.logger import get_logger
from functions.models import CatalogAPI
from functions.validators import (
    HEADER_NAME_REGEX,
    validate_json_body,
    validate_request_headers,
    validate_request_url,
)

DEFAULT_USER_AGENT = "LOOKUPAPI/1.0 (Python Desktop API Explorer; University Course Project)"
DEFAULT_TIMEOUT = 15
SUPPORTED_METHODS = ("GET", "POST", "PUT", "DELETE")
MAX_RESPONSE_DISPLAY_CHARS = 250_000


def build_default_request(api):
    """Build initial request method, URL, query parameters, headers, and empty body from a catalogue entry."""
    safe_api = api.to_dict() if isinstance(api, CatalogAPI) else (api if isinstance(api, dict) else {})
    base_url = str(safe_api.get("base_url") or safe_api.get("endpoint_url") or "").strip().rstrip("/")
    endpoint = str(safe_api.get("working_get_endpoint") or safe_api.get("sample_endpoint") or "").strip()
    if endpoint and not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    full_url = base_url + endpoint if base_url else endpoint

    params = {}
    raw_params = safe_api.get("example_query_parameters")
    if isinstance(raw_params, dict):
        for key, value in raw_params.items():
            clean_key = str(key or "").strip()
            if clean_key:
                params[clean_key] = str(value)

    headers = {"Accept": "application/json", "User-Agent": DEFAULT_USER_AGENT}
    raw_headers = safe_api.get("default_headers") or safe_api.get("headers")
    if isinstance(raw_headers, dict):
        for key, value in raw_headers.items():
            clean_key = str(key or "").strip()
            if clean_key:
                headers[clean_key] = str(value)

    return {"method": "GET", "url": full_url, "params": params, "headers": headers, "body": ""}


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


def _build_result(
    ok,
    method,
    status_code=None,
    reason="",
    response_time_ms=0.0,
    is_json=False,
    body="",
    error="",
    rate_limited=False,
    final_url="",
):
    """Create a standardized HTTP test result dictionary."""
    return {
        "ok": ok,
        "method": method,
        "status_code": status_code,
        "reason": reason,
        "response_time_ms": response_time_ms,
        "is_json": is_json,
        "body": body,
        "error": error,
        "rate_limited": rate_limited,
        "final_url": final_url,
    }


def _prepare_request_inputs(method, url, params, headers, json_body, timeout):
    """Validate method, URL, JSON body, timeout, query parameters, and headers before sending."""
    clean_method = str(method or "GET").strip().upper()
    if clean_method not in SUPPORTED_METHODS:
        msg = f"Unsupported HTTP method '{clean_method}'. Choose GET, POST, PUT, or DELETE."
        return None, _build_result(False, clean_method, reason="Unsupported Method", error=msg)

    is_valid_url, validated_or_err = validate_request_url(url)
    if not is_valid_url:
        return None, _build_result(False, clean_method, error=validated_or_err)

    parsed_json = None
    if clean_method in ("POST", "PUT"):
        is_valid_json, parsed_json, json_err = validate_json_body(json_body)
        if not is_valid_json:
            return None, _build_result(
                False, clean_method, reason="Invalid JSON", error=json_err, final_url=validated_or_err
            )

    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        return None, _build_result(
            False,
            clean_method,
            reason="Invalid Timeout",
            error="Request timeout must be a positive number of seconds.",
            final_url=validated_or_err,
        )

    clean_params = {}
    if isinstance(params, dict):
        for key, value in params.items():
            clean_key = str(key or "").strip()
            if clean_key:
                clean_params[clean_key] = str(value if value is not None else "")

    headers_ok, clean_headers, header_err = validate_request_headers(headers)
    if not headers_ok:
        return None, _build_result(
            False, clean_method, reason="Invalid Header", error=header_err, final_url=validated_or_err
        )

    return {
        "method": clean_method,
        "url": validated_or_err,
        "params": clean_params or None,
        "headers": clean_headers or None,
        "json": parsed_json,
        "timeout": timeout,
    }, None


def _execute_http_request(prepared):
    """Execute the prepared HTTP request and map requests exceptions to result dictionaries."""
    logger = get_logger("lookupapi.api_tester")
    method, target_url, timeout = prepared["method"], prepared["url"], prepared["timeout"]
    start = time.perf_counter()

    try:
        response = requests.request(
            method,
            target_url,
            params=prepared["params"],
            headers=prepared["headers"],
            json=prepared["json"],
            timeout=timeout,
        )
        return response, round((time.perf_counter() - start) * 1000, 1), None
    except requests.exceptions.InvalidHeader as err:
        reason, msg = "Invalid Header", f"Invalid request header: {err}"
    except requests.exceptions.InvalidURL as err:
        reason, msg = "Invalid URL", f"Invalid request URL: {err}"
    except requests.exceptions.Timeout:
        reason, msg = "Timeout", f"Request timed out after {timeout} seconds. The server did not respond in time."
    except requests.exceptions.ConnectionError as err:
        reason, msg = "Connection Error", f"Connection failed: could not reach host ({err})."
    except requests.exceptions.RequestException as err:
        reason, msg = "Request Error", f"Request failed: {err}"

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.warning("%s request failed (%s) after %.1f ms.", method, reason, elapsed_ms)
    return None, elapsed_ms, _build_result(
        False, method, reason=reason, response_time_ms=elapsed_ms, error=msg, final_url=target_url
    )


def _handle_http_response(method, response, elapsed_ms):
    """Format an HTTP response into a structured success, rate-limited, or error result."""
    logger = get_logger("lookupapi.api_tester")
    formatted_body, is_json, parse_warning = format_response_body(response)
    status_code = response.status_code
    reason = str(response.reason or "")
    final_url = str(response.url)

    logger.info("%s request completed with HTTP %s in %.1f ms.", method, status_code, elapsed_ms)

    if status_code == 429:
        retry_after = response.headers.get("Retry-After")
        retry_note = f" Retry after {retry_after}s." if retry_after else " Please wait before trying again."
        return _build_result(
            False,
            method,
            status_code=429,
            reason=reason or "Too Many Requests",
            response_time_ms=elapsed_ms,
            is_json=is_json,
            body=formatted_body,
            error=f"Rate limit exceeded (HTTP 429 Too Many Requests).{retry_note}",
            rate_limited=True,
            final_url=final_url,
        )

    if status_code >= 400:
        return _build_result(
            False,
            method,
            status_code=status_code,
            reason=reason,
            response_time_ms=elapsed_ms,
            is_json=is_json,
            body=formatted_body,
            error=f"HTTP {status_code} {reason}: the server returned an error response.".strip(),
            final_url=final_url,
        )

    return _build_result(
        True,
        method,
        status_code=status_code,
        reason=reason or "OK",
        response_time_ms=elapsed_ms,
        is_json=is_json,
        body=formatted_body,
        error=parse_warning,
        final_url=final_url,
    )


@log_execution
def send_api_request(method, url, params=None, headers=None, json_body=None, timeout=DEFAULT_TIMEOUT):
    """Send a single GET, POST, PUT, or DELETE request and return a structured result dictionary."""
    prepared, validation_error = _prepare_request_inputs(method, url, params, headers, json_body, timeout)
    if validation_error is not None:
        get_logger("lookupapi.api_tester").warning(
            "Rejected %s request before sending (%s).",
            validation_error["method"],
            validation_error["reason"] or "Validation Error",
        )
        return validation_error

    response, elapsed_ms, request_error = _execute_http_request(prepared)
    if request_error is not None:
        return request_error

    return _handle_http_response(prepared["method"], response, elapsed_ms)


def send_get_request(url, params=None, headers=None, timeout=DEFAULT_TIMEOUT):
    """Send a single GET request and return a structured result dictionary."""
    return send_api_request("GET", url, params=params, headers=headers, timeout=timeout)
