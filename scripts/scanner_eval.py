# ==========================================
# FINAL CODE
# ==========================================
"""HTTP endpoint probing, response evaluation, and report generation for the API scanner."""

import csv
import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from functions.logger import get_logger
from scripts.scanner_spec import (
    analyze_security,
    collect_get_candidates,
    extract_base_url,
    format_auth_summary,
    is_valid_public_url,
)

API_DIRECTORY_URL = "https://api.apis.guru/v2/list.json"
JSON_REPORT_PATH = "data/api_test_results.json"
CSV_REPORT_PATH = "data/api_test_results.csv"

REQUEST_HEADERS = {
    "User-Agent": "LOOKUPAPI-Research-Scanner/1.0 (Academic API Discovery Project)",
    "Accept": "application/json, text/plain, */*",
}

SOFT_AUTH_PHRASES = (
    "api key", "apikey", "unauthorized", "unauthenticated", "authentication required",
    "invalid key", "missing key", "access denied", "not authorized", "forbidden",
    "token required", "invalid token", "login required", "must be authenticated",
)

CSV_FIELDS = [
    "api_name",
    "provider",
    "category",
    "base_url",
    "tested_endpoint",
    "http_method",
    "http_status_code",
    "response_time",
    "authentication_requirements",
    "classification",
    "documentation_url",
    "specification_url",
    "error_details",
]


def evaluate_response(response):
    """Inspect an HTTP response to distinguish genuine data, auth errors, and HTML/error pages."""
    status = response.status_code
    content_type = str(response.headers.get("Content-Type") or "").lower()
    body_text = (response.text or "")[:1500]
    body_lower = body_text.lower()

    if status in (401, 403):
        return "AUTH_REQUIRED", f"HTTP {status} authentication/authorization required"
    if status == 429:
        return "RATE_LIMITED", "HTTP 429 Too Many Requests (rate limit reached)"
    if status >= 500 or status == 410:
        return "UNAVAILABLE", f"HTTP {status} server error or gone"

    if 200 <= status < 300:
        if not body_text.strip() and not response.content:
            return "INCONCLUSIVE", f"HTTP {status} returned empty body"

        if "text/html" in content_type or body_lower.lstrip().startswith(("<!doctype html", "<html")):
            if any(phrase in body_lower for phrase in ("sign in", "log in", "login", "unauthorized")):
                return "AUTH_REQUIRED", f"HTTP {status} redirected to HTML login page"
            return "INCONCLUSIVE", f"HTTP {status} returned HTML page instead of API data"

        if "json" in content_type or body_text.lstrip().startswith(("{", "[")):
            try:
                parsed = response.json()
                if isinstance(parsed, dict):
                    err_keys = (
                        "error", "errors", "message", "detail", "status",
                        "reason", "return_message", "error_message", "msg", "err",
                    )
                    err_blob = " ".join(str(parsed.get(k) or "") for k in err_keys).lower()
                    if any(phrase in err_blob for phrase in SOFT_AUTH_PHRASES):
                        return "AUTH_REQUIRED", f"HTTP {status} JSON response indicates auth required"
                return "WORKING_NO_AUTH", ""
            except ValueError:
                return "INCONCLUSIVE", f"HTTP {status} claimed JSON but body was invalid JSON"

        if any(phrase in body_lower for phrase in SOFT_AUTH_PHRASES):
            return "AUTH_REQUIRED", f"HTTP {status} response body indicates auth required"
        return "WORKING_NO_AUTH", ""

    return "INCONCLUSIVE", f"HTTP {status} client response"


def _build_candidate_url(base_url, resolved_path):
    """Combine a base URL and candidate endpoint path without duplicating shared path prefixes."""
    clean_path = "/" + resolved_path.lstrip("/")
    base_path = urlparse(base_url).path.rstrip("/")
    if base_path and clean_path.startswith(base_path + "/"):
        return base_url[: -len(base_path)] + clean_path
    return base_url.rstrip("/") + clean_path


def _probe_candidate_endpoints(base_url, candidates, sec_info, result):
    """Test up to two prioritized safe GET candidates and update result with the outcome."""
    last_outcome = ("INCONCLUSIVE", "", "", "", "")
    for ep_idx, candidate in enumerate(candidates[:2]):
        if ep_idx > 0:
            time.sleep(0.25)

        full_url = _build_candidate_url(base_url, candidate["resolved_path"])
        start = time.perf_counter()
        try:
            resp = requests.get(
                full_url,
                params=candidate["query_params"] or None,
                headers=REQUEST_HEADERS,
                timeout=10,
                allow_redirects=True,
            )
            elapsed = round(time.perf_counter() - start, 3)
            outcome, detail = evaluate_response(resp)

            result["tested_endpoint"] = candidate["resolved_path"]
            result["http_status_code"] = resp.status_code
            result["response_time"] = elapsed

            if outcome == "WORKING_NO_AUTH":
                result["classification"] = "WORKING_NO_AUTH"
                result["error_details"] = ""
                print(f"    -> WORKING_NO_AUTH | GET {candidate['resolved_path']} | HTTP {resp.status_code} ({elapsed}s)")
                return result

            if outcome == "RATE_LIMITED":
                result["classification"] = "INCONCLUSIVE"
                result["error_details"] = detail
                print("    -> INCONCLUSIVE (HTTP 429 rate limit) — stopping tests for this API")
                return result

            if outcome == "AUTH_REQUIRED":
                last_outcome = ("AUTH_REQUIRED", candidate["resolved_path"], resp.status_code, elapsed, detail)
                if ep_idx + 1 >= len(candidates[:2]) or candidates[ep_idx + 1]["ep_auth_required"]:
                    break
            else:
                last_outcome = (outcome, candidate["resolved_path"], resp.status_code, elapsed, detail)

        except requests.exceptions.Timeout:
            elapsed = round(time.perf_counter() - start, 3)
            last_outcome = ("UNAVAILABLE", candidate["resolved_path"], "", elapsed, "Request timed out after 10s")
            break
        except requests.exceptions.RequestException as err:
            elapsed = round(time.perf_counter() - start, 3)
            last_outcome = ("UNAVAILABLE", candidate["resolved_path"], "", elapsed, f"Connection error: {err}")
            break

    final_cls, ep_path, status_code, elapsed, err_detail = last_outcome
    if final_cls == "INCONCLUSIVE" and (sec_info["global_required"] or candidates[0]["ep_auth_required"]):
        final_cls = "AUTH_REQUIRED"
        err_detail = f"{err_detail}; spec explicitly requires authentication"

    result["classification"] = final_cls
    result["tested_endpoint"] = ep_path
    result["http_status_code"] = status_code
    result["response_time"] = elapsed
    result["error_details"] = err_detail
    print(f"    -> {final_cls} | GET {ep_path} | HTTP {status_code or 'N/A'} | {err_detail[:75]}")
    return result


def scan_single_api(api, index, total):
    """Inspect one API's OpenAPI spec and test up to 2 safe GET endpoints."""
    print(f"[{index}/{total}] {api['name']} ({api['provider']}) [{api['category']}]")
    result = {
        "api_name": api["name"],
        "provider": api["provider"],
        "category": api["category"],
        "base_url": "",
        "tested_endpoint": "",
        "http_method": "GET",
        "http_status_code": "",
        "response_time": "",
        "authentication_requirements": "Unknown",
        "classification": "INCONCLUSIVE",
        "documentation_url": api["documentation_url"],
        "specification_url": api["specification_url"],
        "error_details": "",
    }

    try:
        spec_resp = requests.get(api["specification_url"], headers=REQUEST_HEADERS, timeout=12)
        spec_resp.raise_for_status()
        spec = spec_resp.json()
    except requests.exceptions.RequestException as err:
        result["classification"] = "UNAVAILABLE"
        result["error_details"] = f"Spec download failed: {err}"
        print(f"    -> UNAVAILABLE ({result['error_details'][:80]})")
        return result
    except ValueError as err:
        result["classification"] = "INCONCLUSIVE"
        result["error_details"] = f"Invalid spec JSON: {err}"
        print(f"    -> INCONCLUSIVE ({result['error_details'][:80]})")
        return result

    if not isinstance(spec, dict):
        result["error_details"] = "Spec root is not a JSON object"
        print("    -> INCONCLUSIVE (Spec root is not a JSON object)")
        return result

    base_url = extract_base_url(spec, api)
    result["base_url"] = base_url
    sec_info = analyze_security(spec)
    candidates = collect_get_candidates(spec, sec_info)
    result["authentication_requirements"] = format_auth_summary(spec, sec_info, candidates)

    if not is_valid_public_url(base_url):
        result["classification"] = "AUTH_REQUIRED" if sec_info["global_required"] else "INCONCLUSIVE"
        result["error_details"] = f"Missing or non-concrete base URL: '{base_url}'"
        print(f"    -> {result['classification']} ({result['error_details']})")
        return result

    if not candidates:
        result["classification"] = "AUTH_REQUIRED" if sec_info["global_required"] else "INCONCLUSIVE"
        result["error_details"] = "No parameter-free safe GET endpoints found in specification"
        print(f"    -> {result['classification']} ({result['error_details']})")
        return result

    return _probe_candidate_endpoints(base_url, candidates, sec_info, result)


def save_reports(results, total_discovered, json_path=JSON_REPORT_PATH, csv_path=CSV_REPORT_PATH):
    """Write scan results to JSON and CSV reports."""
    logger = get_logger("lookupapi.scanner")
    counts = {
        "WORKING_NO_AUTH": 0,
        "AUTH_REQUIRED": 0,
        "UNAVAILABLE": 0,
        "INCONCLUSIVE": 0,
    }
    for row in results:
        cls = row.get("classification", "INCONCLUSIVE")
        counts[cls] = counts.get(cls, 0) + 1

    json_payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": API_DIRECTORY_URL,
        "note": (
            "A WORKING_NO_AUTH result reflects unauthenticated access at scan time only "
            "and does not guarantee permanent free access or unlimited rate quotas."
        ),
        "summary": {
            "total_directory_apis": total_discovered,
            "tested_apis": len(results),
            **counts,
        },
        "results": results,
    }

    try:
        for report_path in (json_path, csv_path):
            parent = os.path.dirname(report_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(json_payload, jf, indent=2, ensure_ascii=False)
        with open(csv_path, "w", encoding="utf-8", newline="") as cf:
            writer = csv.DictWriter(cf, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for row in results:
                writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})
    except OSError as error:
        logger.error("Could not write scanner report files (%s).", type(error).__name__)
        return False

    print(f"\nSaved JSON report to {json_path}")
    print(f"Saved CSV report to {csv_path}")
    print(f"Summary: {counts}")
    return True
