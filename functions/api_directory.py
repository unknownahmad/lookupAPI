import requests


API_DIRECTORY_URL = "https://api.apis.guru/v2/list.json"
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
    if isinstance(origins, list) and len(origins) > 0:
        first_origin = origins[0]
        if isinstance(first_origin, dict) and first_origin.get("url"):
            return str(first_origin["url"])

    return ""


def get_api_directory(force_refresh=False):
    """Fetch and cache the list of public APIs from the APIs.guru directory."""
    global cached_apis

    if cached_apis is not None and not force_refresh:
        return list(cached_apis)

    try:
        response = requests.get(API_DIRECTORY_URL, timeout=20)
        response.raise_for_status()

        directory = response.json()
        if not isinstance(directory, dict):
            print("Unexpected API directory format.")
            return []

        apis = []

        for provider, provider_data in directory.items():
            if not isinstance(provider_data, dict):
                continue

            versions = provider_data.get("versions")
            if not isinstance(versions, dict):
                continue

            for version, version_data in versions.items():
                if not isinstance(version_data, dict):
                    continue

                api_info = version_data.get("info")
                if not isinstance(api_info, dict):
                    api_info = {}

                api = {
                    "name": str(api_info.get("title") or "Unknown API").strip(),
                    "provider": str(provider),
                    "version": str(api_info.get("version") or version),
                    "description": str(
                        api_info.get("description") or "No description available"
                    ),
                    "documentation_url": extract_documentation_url(
                        version_data, api_info
                    ),
                    "specification_url": str(
                        version_data.get("swaggerUrl") or ""
                    ),
                }

                apis.append(api)

        cached_apis = apis
        return list(cached_apis)

    except requests.exceptions.RequestException as error:
        print("Error connecting to APIs.guru:", error)
        return []

    except (ValueError, KeyError, TypeError) as error:
        print("Error reading API directory:", error)
        return []


def search_apis(search_text, apis=None):
    """Filter loaded APIs by matching API name or provider name."""
    if apis is None:
        apis = get_api_directory()

    if not isinstance(apis, list):
        return []

    cleaned_text = str(search_text or "").strip().lower()

    if cleaned_text == "":
        return list(apis)

    matching_apis = []

    for api in apis:
        if not isinstance(api, dict):
            continue

        name = str(api.get("name") or "").lower()
        provider = str(api.get("provider") or "").lower()

        if cleaned_text in name or cleaned_text in provider:
            matching_apis.append(api)

    return matching_apis
