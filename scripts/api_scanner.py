"""Standalone research scanner for discovering and testing public APIs from APIs.guru."""

import argparse
import csv
import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

API_DIRECTORY_URL = "https://api.apis.guru/v2/list.json"
JSON_REPORT_PATH = "data/api_test_results.json"
CSV_REPORT_PATH = "data/api_test_results.csv"

REQUEST_HEADERS = {
    "User-Agent": "LOOKUPAPI-Research-Scanner/1.0 (Academic API Discovery Project)",
    "Accept": "application/json, text/plain, */*",
}

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

AUTH_PARAM_NAMES = {
    "api_key", "apikey", "key", "token", "access_token", "auth",
    "authorization", "x-api-key", "appid", "app_id", "secret",
    "client_id", "client_secret", "subscription-key", "ocp-apim-subscription-key",
}

AUTH_HINT_KEYWORDS = (
    "api key", "apikey", "oauth", "bearer token", "access token",
    "subscription key", "paid plan", "enterprise account", "client secret",
)

SOFT_AUTH_PHRASES = (
    "api key", "apikey", "unauthorized", "unauthenticated", "authentication required",
    "invalid key", "missing key", "access denied", "not authorized", "forbidden",
    "token required", "invalid token", "login required", "must be authenticated",
)

SKIP_PATH_KEYWORDS = (
    "logout", "login", "signin", "signup", "oauth", "authorize",
    "callback", "delete", "remove", "destroy", "revoke",
    "openapi.json", "openapi.yaml", "swagger.json", "swagger.yaml",
)

AUTH_LIKELY_PATH_KEYWORDS = (
    "/me", "/user", "/users", "/account", "/accounts", "/profile",
    "/admin", "/webhook", "/token", "/secret", "/billing", "/setting",
    "/private", "/console",
)

PUBLIC_LIKELY_PATH_KEYWORDS = (
    "info", "status", "health", "version", "list", "articles", "tags",
    "categories", "search", "public", "random", "latest", "currencies",
    "countries", "services", "voices", "peers", "about", "feeds", "items",
)

BAD_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "example.com", "api.example.com"}

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
        if isinstance(categories, list) and categories:
            category = str(categories[0]).strip()
        else:
            category = "uncategorized"

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


def extract_base_url(spec, api):
    """Extract and validate the API base URL from an OpenAPI 3 or Swagger 2 spec."""
    url = ""
    servers = spec.get("servers")
    if isinstance(servers, list) and servers:
        for server in servers:
            if not isinstance(server, dict) or not server.get("url"):
                continue
            candidate = str(server["url"]).strip()
            variables = server.get("variables")
            if isinstance(variables, dict):
                for var_name, var_def in variables.items():
                    if isinstance(var_def, dict) and "default" in var_def:
                        candidate = candidate.replace("{" + var_name + "}", str(var_def["default"]))
            if candidate:
                url = candidate
                break

    if not url and spec.get("host"):
        host = str(spec["host"]).strip()
        schemes = spec.get("schemes")
        if isinstance(schemes, list) and schemes:
            scheme = "https" if "https" in schemes else str(schemes[0])
        else:
            scheme = "https"
        base_path = str(spec.get("basePath") or "").strip()
        if base_path and not base_path.startswith("/"):
            base_path = "/" + base_path
        url = f"{scheme}://{host}{base_path}"

    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        origin = api.get("documentation_url") or ""
        parsed_origin = urlparse(origin)
        if parsed_origin.scheme in ("http", "https") and parsed_origin.netloc:
            host_only = parsed_origin.hostname or ""
            if host_only not in ("github.com", "raw.githubusercontent.com", "api.apis.guru"):
                url = f"{parsed_origin.scheme}://{parsed_origin.netloc}{url}"

    return url.rstrip("/")


def is_valid_public_url(url):
    """Check whether a base URL is a concrete public HTTP(S) URL without unresolved templates."""
    if not url or "{" in url or "}" in url:
        return False
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    if parsed.hostname.lower() in BAD_HOSTS or parsed.hostname.lower().endswith(".local") or "." not in parsed.hostname:
        return False
    return True


def analyze_security(spec):
    """Inspect global security definitions and requirements in an OpenAPI/Swagger spec."""
    schemes = {}
    raw_schemes = spec.get("securityDefinitions")
    if not isinstance(raw_schemes, dict):
        components = spec.get("components")
        if isinstance(components, dict):
            raw_schemes = components.get("securitySchemes")
    if isinstance(raw_schemes, dict):
        for scheme_name, scheme_def in raw_schemes.items():
            if isinstance(scheme_def, dict):
                schemes[scheme_name] = str(scheme_def.get("type") or "unknown")

    global_sec = spec.get("security")
    global_required = False
    if isinstance(global_sec, list) and len(global_sec) > 0:
        has_empty_override = any(isinstance(item, dict) and len(item) == 0 for item in global_sec)
        has_non_empty = any(isinstance(item, dict) and len(item) > 0 for item in global_sec)
        global_required = has_non_empty and not has_empty_override

    return {
        "schemes": schemes,
        "global_required": global_required,
    }


def extract_param_value(param):
    """Extract an explicit default, example, or enum value from a spec parameter if provided."""
    if not isinstance(param, dict):
        return None
    for key in ("default", "example"):
        if param.get(key) not in (None, ""):
            return str(param[key])
    enum_vals = param.get("enum")
    if isinstance(enum_vals, list) and enum_vals:
        return str(enum_vals[0])
    schema = param.get("schema")
    if isinstance(schema, dict):
        for key in ("default", "example"):
            if schema.get(key) not in (None, ""):
                return str(schema[key])
        s_enum = schema.get("enum")
        if isinstance(s_enum, list) and s_enum:
            return str(s_enum[0])
    return None


def collect_get_candidates(spec, sec_info):
    """Collect and prioritize safe GET endpoints from an OpenAPI/Swagger specification."""
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return []

    candidates = []
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        op = None
        for method_key, method_val in path_item.items():
            if str(method_key).lower() == "get" and isinstance(method_val, dict):
                op = method_val
                break
        if op is None:
            continue

        path_str = str(path)
        lower_path = path_str.lower()
        if any(skip in lower_path for skip in SKIP_PATH_KEYWORDS):
            continue

        if "security" in op and isinstance(op["security"], list):
            op_sec = op["security"]
            if len(op_sec) == 0 or any(isinstance(item, dict) and len(item) == 0 for item in op_sec):
                ep_auth_required = False
                ep_auth_override = "explicit_none"
            else:
                ep_auth_required = True
                ep_auth_override = "explicit_required"
        else:
            ep_auth_required = sec_info["global_required"]
            ep_auth_override = "inherited"

        all_params = []
        for source in (path_item.get("parameters"), op.get("parameters")):
            if isinstance(source, list):
                all_params.extend([p for p in source if isinstance(p, dict)])

        path_vars = re.findall(r"\{([^}]+)\}", path_str)
        resolved_path = path_str
        query_params = {}
        missing_required = []
        auth_param_found = False

        param_map = {str(p.get("name") or ""): p for p in all_params if p.get("name")}
        for p_name, p_def in param_map.items():
            p_in = str(p_def.get("in") or "").lower()
            is_req = bool(p_def.get("required")) or p_in == "path"
            if p_name.lower() in AUTH_PARAM_NAMES and is_req:
                auth_param_found = True
            if is_req and p_in in ("query", "header"):
                val = extract_param_value(p_def)
                if p_in == "query" and val is not None and p_name.lower() not in AUTH_PARAM_NAMES:
                    query_params[p_name] = val
                else:
                    missing_required.append(p_name)

        for var_name in path_vars:
            p_def = param_map.get(var_name)
            val = extract_param_value(p_def) if p_def else None
            if val is not None:
                resolved_path = resolved_path.replace("{" + var_name + "}", val)
            else:
                missing_required.append(var_name)

        if missing_required or "{" in resolved_path or "}" in resolved_path:
            continue

        has_filled_params = bool(path_vars or query_params)
        looks_auth_path = any(kw in lower_path for kw in AUTH_LIKELY_PATH_KEYWORDS)
        looks_public_path = any(kw in lower_path for kw in PUBLIC_LIKELY_PATH_KEYWORDS)
        priority = (
            0 if ep_auth_override == "explicit_none" else (2 if (ep_auth_required or auth_param_found) else 1),
            1 if has_filled_params else 0,
            1 if looks_auth_path else 0,
            0 if looks_public_path else 1,
            resolved_path.count("/"),
            len(resolved_path),
        )
        candidates.append({
            "raw_path": path_str,
            "resolved_path": resolved_path,
            "query_params": query_params,
            "ep_auth_required": ep_auth_required or auth_param_found,
            "ep_auth_override": ep_auth_override,
            "auth_param_found": auth_param_found,
            "priority": priority,
        })

    candidates.sort(key=lambda c: c["priority"])
    return candidates


def format_auth_summary(spec, sec_info, candidates):
    """Build a concise description of authentication requirements found in the spec."""
    parts = []
    if sec_info["global_required"]:
        scheme_types = sorted(set(sec_info["schemes"].values())) or ["unspecified"]
        parts.append(f"Global security declared ({', '.join(scheme_types)})")
    elif sec_info["schemes"]:
        scheme_types = sorted(set(sec_info["schemes"].values()))
        parts.append(f"Security schemes defined ({', '.join(scheme_types)}), not globally required")

    if any(c["ep_auth_override"] == "explicit_required" for c in candidates):
        parts.append("Endpoint-level security declared")
    if any(c["ep_auth_override"] == "explicit_none" for c in candidates):
        parts.append("Some endpoints explicitly allow unauthenticated access")
    if any(c["auth_param_found"] for c in candidates):
        parts.append("Auth parameter found in endpoint spec")

    paths = spec.get("paths")
    if not parts and isinstance(paths, dict):
        for p_item in paths.values():
            if isinstance(p_item, dict):
                for m_key, op in p_item.items():
                    if str(m_key).lower() == "get" and isinstance(op, dict):
                        op_sec = op.get("security")
                        if isinstance(op_sec, list) and any(isinstance(i, dict) and i for i in op_sec):
                            parts.append("Endpoint-level security declared")
                            break
            if parts:
                break

    return "; ".join(parts) if parts else "None declared in spec"


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

    last_outcome = ("INCONCLUSIVE", "", "", "", "")
    for ep_idx, candidate in enumerate(candidates[:2]):
        if ep_idx > 0:
            time.sleep(0.25)

        clean_path = "/" + candidate["resolved_path"].lstrip("/")
        base_path = urlparse(base_url).path.rstrip("/")
        if base_path and clean_path.startswith(base_path + "/"):
            full_url = base_url[: -len(base_path)] + clean_path
        else:
            full_url = base_url.rstrip("/") + clean_path
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
                print(f"    -> INCONCLUSIVE (HTTP 429 rate limit) — stopping tests for this API")
                return result

            if outcome == "AUTH_REQUIRED":
                last_outcome = ("AUTH_REQUIRED", candidate["resolved_path"], resp.status_code, elapsed, detail)
                # If no remaining candidate explicitly waives auth, stop immediately
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


def save_reports(results, total_discovered):
    """Write scan results to data/api_test_results.json and data/api_test_results.csv."""
    os.makedirs("data", exist_ok=True)

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

    with open(JSON_REPORT_PATH, "w", encoding="utf-8") as jf:
        json.dump(json_payload, jf, indent=2, ensure_ascii=False)

    with open(CSV_REPORT_PATH, "w", encoding="utf-8", newline="") as cf:
        writer = csv.DictWriter(cf, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in results:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})

    print(f"\nSaved JSON report to {JSON_REPORT_PATH}")
    print(f"Saved CSV report to {CSV_REPORT_PATH}")
    print(f"Summary: {counts}")


def main():
    """Run the APIs.guru discovery and live unauthenticated GET endpoint scanner."""
    parser = argparse.ArgumentParser(description="Discover and test public APIs from APIs.guru.")
    parser.add_argument("--limit", type=int, default=65, help="Maximum number of sampled APIs to inspect and test.")
    parser.add_argument("--target-working", type=int, default=0, help="Stop early once this many WORKING_NO_AUTH APIs are found (0 disables early stop).")
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
