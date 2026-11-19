from functions.activity import save_activity
from functions.list_of_APIs import add_API, collect_all_APIs, remove_API


def save_API(api):
    """Save an API to the database and record the action in the activity log."""
    if not isinstance(api, dict):
        print("Invalid API data.")
        return False

    name = str(api.get("name") or "").strip()
    if not name:
        print("Cannot save an API without a name.")
        return False

    saved_api = {
        "name": name,
        "category": str(api.get("category") or "General"),
        "description": str(api.get("description") or "No description available"),
        "endpoint_url": str(api.get("endpoint_url") or ""),
        "documentation_url": str(api.get("documentation_url") or ""),
        "http_method": str(api.get("http_method") or "GET"),
        "requires_auth": bool(api.get("requires_auth", False)),
    }

    result = add_API(saved_api)

    if result:
        save_activity(name, "Saved", "N/A")
        print("API saved successfully!")

    return result


def get_saved_APIs():
    """Return all saved APIs from the database."""
    return collect_all_APIs()


def remove_saved_API(api_id):
    """Remove a saved API by ID and record the action in the activity log."""
    api_name = f"API #{api_id}"
    for api in collect_all_APIs():
        if str(api.get("api_id")) == str(api_id):
            api_name = str(api.get("name") or api_name)
            break

    result = remove_API(api_id)

    if result:
        save_activity(api_name, "Removed", "N/A")
        print("API removed successfully!")

    return result
