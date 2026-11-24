# ==========================================
# MIDTERM CODE
# ==========================================

from functions.activity import save_activity
from functions.list_of_APIs import add_API, collect_all_APIs, remove_API

# ==========================================
# FINAL CODE
# ==========================================
from functions.decorators import log_execution
from functions.logger import get_logger
from functions.models import SavedAPI


@log_execution
def save_API(api):
    """Save an API (dict or SavedAPI) to the database and record the action in the activity log."""
    logger = get_logger("lookupapi.saved_apis")

    if isinstance(api, SavedAPI):
        saved_model = api
    elif isinstance(api, dict):
        saved_model = SavedAPI.from_dict(api)
    else:
        logger.warning("Rejected invalid API payload type in save_API.")
        return False

    if not saved_model.name:
        logger.warning("Cannot save an API without a name.")
        return False

    result = add_API(saved_model.to_dict())

    # ==========================================
    # MIDTERM CODE
    # ==========================================
    if result:
        save_activity(saved_model.name, "Saved", "N/A")
        logger.info("Saved API record successfully.")

    return result


# ==========================================
# FINAL CODE
# ==========================================
def get_saved_api_models():
    """Return all saved APIs from the database as SavedAPI model objects."""
    rows = collect_all_APIs()
    models = []
    for row in rows:
        if isinstance(row, SavedAPI):
            models.append(row)
        elif isinstance(row, dict):
            models.append(SavedAPI.from_dict(row))
    return models


# ==========================================
# MIDTERM CODE
# ==========================================
@log_execution
def get_saved_APIs():
    """Return all saved APIs from the database as UI- and DB-compatible dictionaries."""
    return [model.to_dict() for model in get_saved_api_models()]


@log_execution
def remove_saved_API(api_id):
    """Remove a saved API by ID and record the action in the activity log."""
    logger = get_logger("lookupapi.saved_apis")
    api_name = f"API #{api_id}"
    for api in get_saved_api_models():
        if api.api_id is not None and str(api.api_id) == str(api_id):
            api_name = api.name or api_name
            break

    result = remove_API(api_id)

    if result:
        save_activity(api_name, "Removed", "N/A")
        logger.info("Removed saved API record successfully.")

    return result
