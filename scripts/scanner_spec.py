# ==========================================
# FINAL CODE
# ==========================================
"""OpenAPI and Swagger specification parsing helpers for the API research scanner."""

import re
from urllib.parse import urlparse

AUTH_PARAM_NAMES = {
    "api_key", "apikey", "key", "token", "access_token", "auth",
    "authorization", "x-api-key", "appid", "app_id", "secret",
    "client_id", "client_secret", "subscription-key", "ocp-apim-subscription-key",
}

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
PATH_VAR_REGEX = re.compile(r"\{([^}]+)\}")


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
        scheme = ("https" if "https" in schemes else str(schemes[0])) if isinstance(schemes, list) and schemes else "https"
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
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    if port is not None and not (1 <= port <= 65535):
        return False
    host = parsed.hostname.lower()
    return not (host in BAD_HOSTS or host.endswith(".local") or "." not in host)


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

    return {"schemes": schemes, "global_required": global_required}


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


def _resolve_endpoint_security(op, sec_info):
    """Determine effective authentication requirements for a single endpoint operation."""
    if "security" in op and isinstance(op["security"], list):
        op_sec = op["security"]
        if len(op_sec) == 0 or any(isinstance(item, dict) and len(item) == 0 for item in op_sec):
            return False, "explicit_none"
        return True, "explicit_required"
    return sec_info["global_required"], "inherited"


def _resolve_endpoint_params(path_str, path_item, op):
    """Resolve required path and query parameters using spec defaults or examples."""
    all_params = []
    for source in (path_item.get("parameters"), op.get("parameters")):
        if isinstance(source, list):
            all_params.extend([p for p in source if isinstance(p, dict)])

    path_vars = PATH_VAR_REGEX.findall(path_str)
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

    return resolved_path, query_params, path_vars, missing_required, auth_param_found


def collect_get_candidates(spec, sec_info):
    """Collect and prioritize safe GET endpoints from an OpenAPI/Swagger specification."""
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return []

    candidates = []
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        op = next(
            (val for key, val in path_item.items() if str(key).lower() == "get" and isinstance(val, dict)),
            None,
        )
        if op is None:
            continue

        path_str = str(path)
        lower_path = path_str.lower()
        if any(skip in lower_path for skip in SKIP_PATH_KEYWORDS):
            continue

        ep_auth_required, ep_auth_override = _resolve_endpoint_security(op, sec_info)
        resolved_path, query_params, path_vars, missing_required, auth_param_found = _resolve_endpoint_params(
            path_str, path_item, op
        )
        if missing_required or "{" in resolved_path or "}" in resolved_path:
            continue

        priority = (
            0 if ep_auth_override == "explicit_none" else (2 if (ep_auth_required or auth_param_found) else 1),
            1 if (path_vars or query_params) else 0,
            1 if any(kw in lower_path for kw in AUTH_LIKELY_PATH_KEYWORDS) else 0,
            0 if any(kw in lower_path for kw in PUBLIC_LIKELY_PATH_KEYWORDS) else 1,
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
