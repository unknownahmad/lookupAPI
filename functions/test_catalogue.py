# ==========================================
# FINAL CODE
# ==========================================

import json
import os
import re
from urllib.parse import urlencode

CATALOGUE_FILE = "data/verified_free_apis.json"


def load_verified_free_apis(file_path=CATALOGUE_FILE):
    """Load the approved no-auth public API catalogue from JSON."""
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
    for entry in raw_apis:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("authentication") or "").strip().upper() != "NONE":
            continue
        approved.append(entry)

    return approved


def group_apis_by_category(apis):
    """Group approved APIs into an alphabetically ordered category dictionary."""
    grouped = {}
    for api in apis:
        category = str(api.get("category") or "Other").strip() or "Other"
        grouped.setdefault(category, []).append(api)

    return {cat: grouped[cat] for cat in sorted(grouped)}


def format_example_endpoint(api):
    """Build the full example GET endpoint path including query parameters."""
    endpoint = str(api.get("working_get_endpoint") or "").strip() or "Not available"
    params = api.get("example_query_parameters")
    if isinstance(params, dict) and len(params) > 0:
        return f"{endpoint}?{urlencode(params)}"
    return endpoint


def extract_attribution_info(api):
    """Identify license or attribution notes stated in the catalogue entry."""
    evidence = str(api.get("free_access_evidence") or "")
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
    evidence = str(api.get("free_access_evidence") or "")
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
