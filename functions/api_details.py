import requests


ALLOWED_HTTP_METHODS = {"get", "post", "put", "delete", "patch"}


def get_base_url(specification):
    """Extract the base URL from an OpenAPI or Swagger specification."""
    servers = specification.get("servers")
    if isinstance(servers, list) and len(servers) > 0:
        first_server = servers[0]
        if isinstance(first_server, dict) and first_server.get("url"):
            return str(first_server["url"])

    host = specification.get("host") or ""
    if host:
        schemes = specification.get("schemes")
        if isinstance(schemes, list) and len(schemes) > 0 and schemes[0]:
            scheme = str(schemes[0])
        else:
            scheme = "https"

        base_path = str(specification.get("basePath") or "")
        return scheme + "://" + str(host) + base_path

    return ""


def get_documentation_url(specification, info, api):
    """Find the best available documentation URL for an API."""
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

            http_method = str(method).upper()
            endpoint_path = str(path)
            endpoint_key = (http_method, endpoint_path)
            if endpoint_key in seen_endpoints:
                continue
            seen_endpoints.add(endpoint_key)

            summary = "No summary available"
            if isinstance(method_details, dict):
                summary = str(
                    method_details.get("summary") or "No summary available"
                ).strip()

            endpoint = {
                "method": http_method,
                "path": endpoint_path,
                "summary": summary,
            }
            endpoints.append(endpoint)

    return endpoints


def get_api_details(api):
    """Download and parse full details and endpoints for a selected API."""
    if not isinstance(api, dict):
        print("Invalid API data.")
        return None

    specification_url = api.get("specification_url") or ""
    if not specification_url:
        print("This API does not have a specification URL.")
        return None

    try:
        response = requests.get(specification_url, timeout=20)
        response.raise_for_status()

        specification = response.json()
        if not isinstance(specification, dict):
            print("Unexpected API specification format.")
            return None

        info = specification.get("info")
        if not isinstance(info, dict):
            info = {}

        details = {
            "name": str(info.get("title") or api.get("name") or "Unknown API").strip(),
            "provider": str(api.get("provider") or ""),
            "version": str(info.get("version") or api.get("version") or ""),
            "description": str(
                info.get("description")
                or api.get("description")
                or "No description available"
            ),
            "documentation_url": get_documentation_url(specification, info, api),
            "base_url": get_base_url(specification),
            "specification_url": str(specification_url),
            "endpoints": get_endpoints(specification),
        }

        return details

    except requests.exceptions.RequestException as error:
        print("Error downloading API specification:", error)
        return None

    except (ValueError, KeyError, TypeError) as error:
        print("Error reading API specification:", error)
        return None
