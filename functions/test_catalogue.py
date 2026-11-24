# ==========================================
# FINAL CODE
# ==========================================

import json
import os
import re
from urllib.parse import urlencode

from functions.decorators import log_execution
from functions.logger import get_logger
from functions.models import CatalogAPI

CATALOGUE_FILE = "data/verified_free_apis.json"


def _as_dict(api):
    """Return a dictionary view of either a CatalogAPI model or a plain dict."""
    if isinstance(api, CatalogAPI):
        return api.to_dict()
    return api if isinstance(api, dict) else None


def is_valid_catalogue_entry(entry):
    """Return True if a catalogue entry is unauthenticated and has valid required fields."""
    if isinstance(entry, CatalogAPI):
        model = entry
        raw_auth = model.auth
    elif isinstance(entry, dict):
        raw_auth = entry.get("authentication")
        if raw_auth is None:
            raw_auth = entry.get("auth")
        model = CatalogAPI.from_dict(entry)
    else:
        return False

    if str(raw_auth or "").strip().upper() != "NONE":
        return False
    if not model.name or not model.endpoint_url or not model.sample_endpoint:
        return False
    return model.has_valid_url()


def iter_catalogue_apis(file_path=CATALOGUE_FILE):
    """Yield validated, deduplicated CatalogAPI objects from the verified JSON catalogue."""
    logger = get_logger("lookupapi.catalogue")
    if not os.path.exists(file_path):
        logger.warning("Verified API catalogue file not found.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, ValueError) as error:
        logger.error("Error reading verified API catalogue (%s).", type(error).__name__)
        return

    raw_apis = payload.get("apis") if isinstance(payload, dict) else []
    if not isinstance(raw_apis, list):
        logger.warning("Verified API catalogue payload has an invalid 'apis' list.")
        return

    seen_keys = set()
    for entry in raw_apis:
        if not is_valid_catalogue_entry(entry):
            continue
        model = entry if isinstance(entry, CatalogAPI) else CatalogAPI.from_dict(entry)
        dedupe_key = (
            model.name.lower(),
            model.endpoint_url.rstrip("/").lower(),
            model.sample_endpoint,
        )
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        yield model


def iter_apis_by_category(apis, category=None):
    """Yield catalogue APIs (CatalogAPI or dict) matching a category, or all if None/'All'."""
    if apis is None:
        return

    target = str(category or "").strip().lower()
    include_all = target in ("", "all")

    for api in apis:
        if isinstance(api, CatalogAPI):
            api_cat = api.category
        elif isinstance(api, dict):
            api_cat = str(api.get("category") or "Other").strip() or "Other"
        else:
            continue

        if include_all or api_cat.lower() == target:
            yield api


@log_execution
def load_verified_free_apis(file_path=CATALOGUE_FILE):
    """Load and validate the approved no-auth public API catalogue as UI-compatible dicts."""
    logger = get_logger("lookupapi.catalogue")
    approved = [api.to_dict() for api in iter_catalogue_apis(file_path=file_path)]
    logger.info("Loaded %d verified catalogue APIs.", len(approved))
    return approved


def group_apis_by_category(apis):
    """Group approved APIs into an alphabetically ordered category dictionary sorted by name."""
    if not isinstance(apis, (list, tuple)):
        return {}

    grouped = {}
    for api in iter_apis_by_category(apis):
        category = (
            api.category
            if isinstance(api, CatalogAPI)
            else str(api.get("category") or "Other").strip() or "Other"
        )
        grouped.setdefault(category, []).append(api)

    return {
        cat: sorted(
            grouped[cat],
            key=lambda item: (
                item.name.lower()
                if isinstance(item, CatalogAPI)
                else str(item.get("api_name") or item.get("name") or "").strip().lower()
            ),
        )
        for cat in sorted(grouped)
    }


def format_example_endpoint(api):
    """Build the full example GET endpoint path including query parameters."""
    data = _as_dict(api)
    if data is None:
        return "Not available"

    endpoint = str(data.get("working_get_endpoint") or data.get("sample_endpoint") or "").strip()
    if not endpoint:
        return "Not available"

    params = data.get("example_query_parameters")
    if isinstance(params, dict):
        clean_params = {str(k).strip(): str(v) for k, v in params.items() if str(k or "").strip()}
        if clean_params:
            return f"{endpoint}?{urlencode(clean_params)}"
    return endpoint


def extract_attribution_info(api):
    """Identify license or attribution notes stated in the catalogue entry."""
    data = _as_dict(api)
    evidence = str(data.get("free_access_evidence") or "") if data is not None else ""
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
    data = _as_dict(api)
    evidence = str(data.get("free_access_evidence") or "") if data is not None else ""
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
