# ==========================================
# FINAL CODE
# ==========================================
"""Standalone research scanner for discovering and testing public APIs from APIs.guru."""

import argparse
import os
import sys

import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.scanner_eval import (  # noqa: E402
    API_DIRECTORY_URL,
    CSV_FIELDS,
    CSV_REPORT_PATH,
    JSON_REPORT_PATH,
    REQUEST_HEADERS,
    SOFT_AUTH_PHRASES,
    evaluate_response,
    save_reports,
    scan_single_api,
)
from scripts.scanner_spec import (  # noqa: E402
    AUTH_LIKELY_PATH_KEYWORDS,
    AUTH_PARAM_NAMES,
    BAD_HOSTS,
    PUBLIC_LIKELY_PATH_KEYWORDS,
    SKIP_PATH_KEYWORDS,
    analyze_security,
    collect_get_candidates,
    extract_base_url,
    extract_param_value,
    format_auth_summary,
    is_valid_public_url,
)

PREFERRED_CATEGORIES = [
    "open_data",
    "entertainment",
    "media",
    "education",
    "location",
    "search",
    "financial",
    "developer_tools",
    "tools",
    "social",
    "text",
    "machine_learning",
    "security",
    "iot",
    "transport",
    "ecommerce",
    "analytics",
    "cloud",
]

AUTH_HINT_KEYWORDS = (
    "api key", "apikey", "oauth", "bearer token", "access token",
    "subscription key", "paid plan", "enterprise account", "client secret",
)


def extract_doc_url(version_data, info):
    """Extract the best documentation link from an APIs.guru version entry."""
    ext_docs = version_data.get("externalDocs")
    if isinstance(ext_docs, dict) and ext_docs.get("url"):
        return str(ext_docs["url"]).strip()
    contact = info.get("contact")
    if isinstance(contact, dict) and contact.get("url"):
        return str(contact["url"]).strip()
    origins = info.get("x-origin")
    if isinstance(origins, list) and origins and isinstance(origins[0], dict):
        if origins[0].get("url"):
            return str(origins[0]["url"]).strip()
    return ""


def discover_apis():
    """Download the APIs.guru directory and return one preferred entry per API."""
    print(f"Downloading APIs.guru directory from {API_DIRECTORY_URL} ...")
    try:
        response = requests.get(API_DIRECTORY_URL, headers=REQUEST_HEADERS, timeout=25)
        response.raise_for_status()
        directory = response.json()
    except requests.exceptions.RequestException as err:
        print(f"Failed to download APIs.guru directory: {err}")
        return []
    except ValueError as err:
        print(f"Invalid JSON in APIs.guru directory: {err}")
        return []

    if not isinstance(directory, dict):
        print("Unexpected APIs.guru directory payload format.")
        return []

    discovered = []
    for provider_key, provider_data in directory.items():
        if not isinstance(provider_data, dict):
            continue
        versions = provider_data.get("versions")
        if not isinstance(versions, dict) or not versions:
            continue

        preferred = provider_data.get("preferred")
        version_key = preferred if preferred in versions else next(iter(versions))
        version_data = versions.get(version_key)
        if not isinstance(version_data, dict):
            continue

        spec_url = str(version_data.get("swaggerUrl") or "").strip()
        if not spec_url:
            continue

        info = version_data.get("info") if isinstance(version_data.get("info"), dict) else {}
        categories = info.get("x-apisguru-categories")
        category = str(categories[0]).strip() if isinstance(categories, list) and categories else "uncategorized"

        discovered.append({
            "name": str(info.get("title") or provider_key).strip(),
            "provider": str(provider_key).strip(),
            "root_domain": str(provider_key).split(":")[0].lower(),
            "version": str(info.get("version") or version_key).strip(),
            "description": str(info.get("description") or "").strip(),
            "category": category,
            "documentation_url": extract_doc_url(version_data, info),
            "specification_url": spec_url,
            "updated": str(version_data.get("updated") or ""),
        })

    print(f"Discovered {len(discovered)} unique APIs with specifications.")
    return discovered


def select_diverse_sample(apis, sample_size=65):
    """Select a diverse sample of unique-domain public APIs across categories."""
    best_by_domain = {}
    for api in apis:
        domain = api["root_domain"]
        if domain.endswith(".local") or "deprecated" in api["name"].lower():
            continue
        desc_lower = api["description"].lower()
        has_auth_hint = any(hint in desc_lower for hint in AUTH_HINT_KEYWORDS)
        score = (
            0 if not has_auth_hint else 1,
            0 if api["category"] in PREFERRED_CATEGORIES else 1,
            api["updated"],
        )
        existing = best_by_domain.get(domain)
        if existing is None or (score[0], score[1]) < (existing[0][0], existing[0][1]) or (
            (score[0], score[1]) == (existing[0][0], existing[0][1]) and score[2] > existing[0][2]
        ):
            best_by_domain[domain] = (score, api)

    by_category = {}
    for score, api in best_by_domain.values():
        if api["category"] in PREFERRED_CATEGORIES:
            by_category.setdefault(api["category"], []).append((score, api))

    for cat in by_category:
        no_hint = sorted([a for s, a in by_category[cat] if s[0] == 0], key=lambda x: x["updated"], reverse=True)
        with_hint = sorted([a for s, a in by_category[cat] if s[0] == 1], key=lambda x: x["updated"], reverse=True)
        by_category[cat] = no_hint + with_hint

    ordered_categories = [c for c in PREFERRED_CATEGORIES if c in by_category]
    selected = []
    pointers = {cat: 0 for cat in ordered_categories}
    while len(selected) < sample_size:
        added_this_round = False
        for cat in ordered_categories:
            idx = pointers[cat]
            if idx < len(by_category[cat]):
                selected.append(by_category[cat][idx])
                pointers[cat] += 1
                added_this_round = True
                if len(selected) >= sample_size:
                    break
        if not added_this_round:
            break

    print(f"Selected {len(selected)} diverse APIs across {len({a['category'] for a in selected})} categories.")
    return selected


def main():
    """Run the APIs.guru discovery and live unauthenticated GET endpoint scanner."""
    parser = argparse.ArgumentParser(description="Discover and test public APIs from APIs.guru.")
    parser.add_argument("--limit", type=int, default=65, help="Maximum number of sampled APIs to inspect and test.")
    parser.add_argument(
        "--target-working",
        type=int,
        default=0,
        help="Stop early once this many WORKING_NO_AUTH APIs are found (0 disables early stop).",
    )
    args = parser.parse_args()

    discovered = discover_apis()
    if not discovered:
        print("Aborting: could not retrieve APIs.guru directory.")
        return

    sample = select_diverse_sample(discovered, sample_size=args.limit)
    results = []
    working_count = 0
    for idx, api in enumerate(sample, start=1):
        res = scan_single_api(api, idx, len(sample))
        results.append(res)
        if res["classification"] == "WORKING_NO_AUTH":
            working_count += 1
            if args.target_working > 0 and working_count >= args.target_working:
                print(f"\nReached target of {args.target_working} WORKING_NO_AUTH candidates after testing {idx} APIs.")
                break

    save_reports(results, len(discovered))


if __name__ == "__main__":
    main()
