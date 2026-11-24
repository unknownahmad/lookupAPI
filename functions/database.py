import os

from dotenv import load_dotenv
import pymysql

from functions.decorators import log_execution
from functions.logger import get_logger
from functions.models import SavedAPI
from functions.utils import save_activity

REQUIRED_API_FIELDS = (
    "name",
    "category",
    "description",
    "endpoint_url",
    "documentation_url",
    "http_method",
    "requires_auth",
)


def connect_database():
    """Create and return a MySQL database connection using .env settings."""
    load_dotenv()
    logger = get_logger("lookupapi.database")

    try:
        db_port = int(os.getenv("DB_PORT") or 3306)
        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            port=db_port,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
        )
        logger.info("Database connected successfully.")
        return connection
    except (pymysql.Error, ValueError, TypeError) as error:
        logger.error("Database connection failed (%s).", type(error).__name__)
        return None


def _prepare_api_insert_values(api):
    """Validate and normalize a saved API dictionary into a MySQL insert tuple."""
    logger = get_logger("lookupapi.database")
    if not isinstance(api, dict):
        logger.warning("Invalid API data passed to add_API.")
        return None

    for field in REQUIRED_API_FIELDS:
        if field not in api:
            logger.warning("Missing required API field: %s", field)
            return None

    name = str(api["name"] or "").strip()[:100]
    if not name:
        logger.warning("Missing required API field: name")
        return None

    return (
        name,
        str(api["category"] or "General").strip()[:50],
        str(api["description"] or "No description available"),
        str(api["endpoint_url"] or "").strip()[:500],
        str(api["documentation_url"] or "").strip()[:500],
        str(api["http_method"] or "GET").strip().upper()[:10],
        bool(api["requires_auth"]),
    )


def collect_all_APIs():
    """Retrieve and return all saved API records from the database."""
    logger = get_logger("lookupapi.database")
    connection = connect_database()
    if connection is None:
        return []

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM apis ORDER BY api_id")
        return list(cursor.fetchall())
    except pymysql.Error as error:
        logger.error("Error retrieving saved APIs (%s).", type(error).__name__)
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if connection.open:
            connection.close()


def add_API(api):
    """Insert a new API record into the database if it is valid and unique."""
    logger = get_logger("lookupapi.database")
    values = _prepare_api_insert_values(api)
    if values is None:
        return False

    connection = connect_database()
    if connection is None:
        return False

    cursor = None
    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO apis
        (name, category, description, endpoint_url,
         documentation_url, http_method, requires_auth)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, values)
        connection.commit()
        return True
    except pymysql.IntegrityError as error:
        if connection.open:
            connection.rollback()
        if error.args and error.args[0] == 1062:
            logger.warning("API record already exists in database.")
        else:
            logger.error("Database integrity error adding API (%s).", type(error).__name__)
        return False
    except pymysql.Error as error:
        if connection.open:
            connection.rollback()
        logger.error("Database error adding API (%s).", type(error).__name__)
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if connection.open:
            connection.close()


def remove_API(api_id):
    """Delete a saved API record from the database using its api_id."""
    logger = get_logger("lookupapi.database")
    if isinstance(api_id, bool):
        logger.warning("Invalid API ID type passed to remove_API.")
        return False

    try:
        api_id = int(api_id)
    except (ValueError, TypeError):
        logger.warning("Invalid API ID value passed to remove_API.")
        return False

    connection = connect_database()
    if connection is None:
        return False

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM apis WHERE api_id = %s", (api_id,))
        connection.commit()
        if cursor.rowcount == 0:
            logger.info("No saved API found for deletion.")
            return False
        return True
    except pymysql.Error as error:
        if connection.open:
            connection.rollback()
        logger.error("Database error removing API (%s).", type(error).__name__)
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if connection.open:
            connection.close()


@log_execution
def save_API(api):
    """Save an API (dict or SavedAPI) to MySQL and record the action in the activity log."""
    logger = get_logger("lookupapi.database")
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
    if result:
        save_activity(saved_model.name, "Saved", "N/A")
        logger.info("Saved API record successfully.")
    return result


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


@log_execution
def get_saved_APIs():
    """Return all saved APIs from the database as UI- and DB-compatible dictionaries."""
    return [model.to_dict() for model in get_saved_api_models()]


@log_execution
def remove_saved_API(api_id):
    """Remove a saved API by ID and record the action in the activity log."""
    logger = get_logger("lookupapi.database")
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
