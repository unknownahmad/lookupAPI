# ==========================================
# FINAL CODE
# ==========================================

import json
import os
import re
from urllib.parse import urlencode, urlparse

CATALOGUE_FILE = "data/verified_free_apis.json"


def is_valid_catalogue_entry(entry):
    """Return True if a catalogue entry is unauthenticated and has required valid fields."""
    if not isinstance(entry, dict):
        return False
    if str(entry.get("authentication") or "").strip().upper() != "NONE":
        return False

    name = str(entry.get("api_name") or "").strip()
    base_url = str(entry.get("base_url") or "").strip()
    endpoint = str(entry.get("working_get_endpoint") or "").strip()
    if not name or not base_url or not endpoint:
        return False

    parsed = urlparse(base_url)
    return parsed.scheme in ("http", "https") and bool(parsed.hostname)


def load_verified_free_apis(file_path=CATALOGUE_FILE):
    """Load and validate the approved no-auth public API catalogue from JSON."""
    if not os.path.exists(file_path):
        print("Verified API catalogue file not found:", file_path)
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, ValueError) as error:
        print("Error reading verified API catalogue:", error)
        return []

    raw_apis = payload.get("apis") if isinstance(payload, dict) else []
    if not isinstance(raw_apis, list):
        return []

    approved = []
    seen_keys = set()
    for entry in raw_apis:
        if not is_valid_catalogue_entry(entry):
            continue
        dedupe_key = (
            str(entry.get("api_name") or "").strip().lower(),
            str(entry.get("base_url") or "").strip().rstrip("/").lower(),
            str(entry.get("working_get_endpoint") or "").strip(),
        )
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        approved.append(entry)

    return approved


def group_apis_by_category(apis):
    """Group approved APIs into an alphabetically ordered category dictionary."""
    if not isinstance(apis, list):
        return {}

    grouped = {}
    for api in apis:
        if not isinstance(api, dict):
            continue
        category = str(api.get("category") or "Other").strip() or "Other"
        grouped.setdefault(category, []).append(api)

    return {cat: grouped[cat] for cat in sorted(grouped)}


def format_example_endpoint(api):
    """Build the full example GET endpoint path including query parameters."""
    if not isinstance(api, dict):
        return "Not available"

    endpoint = str(api.get("working_get_endpoint") or "").strip()
    if not endpoint:
        return "Not available"

    params = api.get("example_query_parameters")
    if isinstance(params, dict):
        clean_params = {str(k).strip(): str(v) for k, v in params.items() if str(k or "").strip()}
        if clean_params:
            return f"{endpoint}?{urlencode(clean_params)}"
    return endpoint


def extract_attribution_info(api):
    """Identify license or attribution notes stated in the catalogue entry."""
    evidence = str(api.get("free_access_evidence") or "") if isinstance(api, dict) else ""
    lower = evidence.lower()
    notes = []

    license_checks = [
        ("cc by-sa 4.0", "CC BY-SA 4.0 (attribution required)"),
        ("cc by 4.0", "CC BY 4.0 (attribution required)"),
        ("cc-by", "Creative Commons CC-BY (attribution required)"),
        ("cc0 1.0", "CC0 1.0 Universal (Public Domain)"),
        ("public domain", "Public Domain (U.S. Government / Open Data)"),
        ("bsd-3-clause", "BSD-3-Clause open-source code"),
        ("agplv3", "AGPLv3 open-source code"),
        ("mit", "MIT License"),
    ]
    for keyword, label in license_checks:
        if keyword in lower and label not in notes:
            notes.append(label)

    if "geonames" in lower:
        notes.append("Built on GeoNames open data")
    if "internet archive" in lower:
        notes.append("Non-profit Internet Archive catalog")
    if "crossref" in lower or "scholarly" in lower:
        notes.append("Non-profit Crossref scholarly metadata")

    return "; ".join(notes) if notes else "See official documentation for attribution details"


def extract_rate_limit_info(api):
    """Extract documented rate limits or usage guidance from catalogue evidence."""
    evidence = str(api.get("free_access_evidence") or "") if isinstance(api, dict) else ""
    lower = evidence.lower()
    notes = []

    match_patterns = [
        r"up to [\d,]+\s+calls/day",
        r"\d+\s+requests/second",
        r"~?\d+\s+req/\d+s",
    ]
    for pattern in match_patterns:
        match = re.search(pattern, evidence, flags=re.IGNORECASE)
        if match:
            notes.append(match.group(0))

    if "non-commercial" in lower:
        notes.append("Non-commercial / academic use")
    if "caching" in lower:
        notes.append("Fair-use local caching policy")
    if "user-agent" in lower:
        notes.append("Descriptive User-Agent header requested/required")
    if "best-effort" in lower:
        notes.append("Best-effort public service")
    if "public pool" in lower:
        notes.append("Free public pool rate limits apply")

    return "; ".join(notes) if notes else "No specific rate limit documented (use fair-use rates)"
