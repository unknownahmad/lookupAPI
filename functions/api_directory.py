import requests

from functions.logger import get_logger

API_DIRECTORY_URL = "https://api.apis.guru/v2/list.json"
ALLOWED_HTTP_METHODS = {"get", "post", "put", "delete", "patch"}
cached_apis = None


def extract_documentation_url(version_data, api_info):
    """Extract a documentation link from an APIs.guru version entry."""
    external_docs = version_data.get("externalDocs")
    if isinstance(external_docs, dict) and external_docs.get("url"):
        return str(external_docs["url"])

    contact = api_info.get("contact")
    if isinstance(contact, dict) and contact.get("url"):
        return str(contact["url"])

    origins = api_info.get("x-origin")
    if isinstance(origins, list) and origins:
        first_origin = origins[0]
        if isinstance(first_origin, dict) and first_origin.get("url"):
            return str(first_origin["url"])

    return ""


def _parse_directory_payload(directory):
    """Convert the raw APIs.guru JSON dictionary into a flat list of API dicts."""
    apis = []
    for provider, provider_data in directory.items():
        versions = provider_data.get("versions") if isinstance(provider_data, dict) else None
        if not isinstance(versions, dict):
            continue

        for version, version_data in versions.items():
            if not isinstance(version_data, dict):
                continue
            api_info = version_data.get("info")
            if not isinstance(api_info, dict):
                api_info = {}

            apis.append(
                {
                    "name": str(api_info.get("title") or "Unknown API").strip(),
                    "provider": str(provider),
                    "version": str(api_info.get("version") or version),
                    "description": str(api_info.get("description") or "No description available"),
                    "documentation_url": extract_documentation_url(version_data, api_info),
                    "specification_url": str(version_data.get("swaggerUrl") or ""),
                }
            )
    return apis


def get_api_directory(force_refresh=False):
    """Fetch and cache the list of public APIs from the APIs.guru directory."""
    global cached_apis
    logger = get_logger("lookupapi.directory")

    if cached_apis is not None and not force_refresh:
        return list(cached_apis)

    try:
        response = requests.get(API_DIRECTORY_URL, timeout=20)
        response.raise_for_status()
        directory = response.json()
        if not isinstance(directory, dict):
            logger.warning("Unexpected APIs.guru directory payload format.")
            return []

        cached_apis = _parse_directory_payload(directory)
        logger.info("Loaded %d entries from APIs.guru directory.", len(cached_apis))
        return list(cached_apis)
    except requests.exceptions.RequestException as error:
        logger.error("Error connecting to APIs.guru (%s).", type(error).__name__)
        return []
    except (ValueError, KeyError, TypeError) as error:
        logger.error("Error reading APIs.guru directory (%s).", type(error).__name__)
        return []


def search_apis(search_text, apis=None):
    """Filter loaded APIs by matching API name or provider name."""
    if apis is None:
        apis = get_api_directory()
    if not isinstance(apis, list):
        return []

    cleaned_text = str(search_text or "").strip().lower()
    if not cleaned_text:
        return list(apis)

    matches = []
    for api in apis:
        if not isinstance(api, dict):
            continue
        name = str(api.get("name") or "").lower()
        provider = str(api.get("provider") or "").lower()
        if cleaned_text in name or cleaned_text in provider:
            matches.append(api)
    return matches


def get_base_url(specification):
    """Extract the base URL from an OpenAPI or Swagger specification."""
    servers = specification.get("servers")
    if isinstance(servers, list) and servers:
        first_server = servers[0]
        if isinstance(first_server, dict) and first_server.get("url"):
            return str(first_server["url"])

    host = specification.get("host") or ""
    if host:
        schemes = specification.get("schemes")
        scheme = str(schemes[0]) if isinstance(schemes, list) and schemes and schemes[0] else "https"
        base_path = str(specification.get("basePath") or "")
        return f"{scheme}://{host}{base_path}"
    return ""


def get_documentation_url(specification, info, api):
    """Find the best available documentation URL for an API specification."""
    external_docs = specification.get("externalDocs")
    if isinstance(external_docs, dict) and external_docs.get("url"):
        return str(external_docs["url"])
    if api.get("documentation_url"):
        return str(api["documentation_url"])
    contact = info.get("contact")
    if isinstance(contact, dict) and contact.get("url"):
        return str(contact["url"])
    return ""


def get_endpoints(specification):
    """Extract unique HTTP method and path endpoints from an API specification."""
    endpoints = []
    seen_endpoints = set()
    paths = specification.get("paths")
    if not isinstance(paths, dict):
        return endpoints

    for path, path_details in paths.items():
        if not isinstance(path_details, dict):
            continue
        for method, method_details in path_details.items():
            if str(method).lower() not in ALLOWED_HTTP_METHODS:
                continue
            endpoint_key = (str(method).upper(), str(path))
            if endpoint_key in seen_endpoints:
                continue
            seen_endpoints.add(endpoint_key)
            summary = "No summary available"
            if isinstance(method_details, dict):
                summary = str(method_details.get("summary") or "No summary available").strip()
            endpoints.append({"method": endpoint_key[0], "path": endpoint_key[1], "summary": summary})
    return endpoints


def get_api_details(api):
    """Download and parse full details and endpoints for a selected API."""
    logger = get_logger("lookupapi.directory")
    if not isinstance(api, dict) or not api.get("specification_url"):
        return None

    spec_url = str(api["specification_url"])
    try:
        response = requests.get(spec_url, timeout=20)
        response.raise_for_status()
        specification = response.json()
        if not isinstance(specification, dict):
            return None

        info = specification.get("info")
        if not isinstance(info, dict):
            info = {}

        return {
            "name": str(info.get("title") or api.get("name") or "Unknown API").strip(),
            "provider": str(api.get("provider") or ""),
            "version": str(info.get("version") or api.get("version") or ""),
            "description": str(info.get("description") or api.get("description") or "No description available"),
            "documentation_url": get_documentation_url(specification, info, api),
            "base_url": get_base_url(specification),
            "specification_url": spec_url,
            "endpoints": get_endpoints(specification),
        }
    except requests.exceptions.RequestException as error:
        logger.warning("Failed to fetch API specification (%s).", type(error).__name__)
        return None
    except (ValueError, KeyError, TypeError) as error:
        logger.warning("Failed to parse API specification (%s).", type(error).__name__)
        return None
