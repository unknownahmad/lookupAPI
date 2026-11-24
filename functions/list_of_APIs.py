# ==========================================
# MIDTERM CODE
# ==========================================

import pymysql
from functions.database import connect_database

# ==========================================
# FINAL CODE
# ==========================================
from functions.logger import get_logger

REQUIRED_API_FIELDS = (
    "name",
    "category",
    "description",
    "endpoint_url",
    "documentation_url",
    "http_method",
    "requires_auth",
)


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


# ==========================================
# MIDTERM CODE
# ==========================================
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
        apis = cursor.fetchall()
        return list(apis)

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
