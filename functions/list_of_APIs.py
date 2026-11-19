import pymysql
from functions.database import connect_database


def collect_all_APIs():
    """Retrieve and return all saved API records from the database."""
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
        print("Error getting APIs:", error)
        return []

    finally:
        if cursor is not None:
            cursor.close()
        if connection.open:
            connection.close()


def add_API(api):
    """Insert a new API record into the database if it is valid and unique."""
    if not isinstance(api, dict):
        print("Invalid API data.")
        return False

    required_fields = [
        "name",
        "category",
        "description",
        "endpoint_url",
        "documentation_url",
        "http_method",
        "requires_auth",
    ]

    for field in required_fields:
        if field not in api:
            print("Missing information:", field)
            return False

    name = str(api["name"] or "").strip()[:100]
    if not name:
        print("Missing information: name")
        return False

    category = str(api["category"] or "General").strip()[:50]
    description = str(api["description"] or "No description available")
    endpoint_url = str(api["endpoint_url"] or "").strip()[:500]
    documentation_url = str(api["documentation_url"] or "").strip()[:500]
    http_method = str(api["http_method"] or "GET").strip().upper()[:10]
    requires_auth = bool(api["requires_auth"])

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
        values = (
            name,
            category,
            description,
            endpoint_url,
            documentation_url,
            http_method,
            requires_auth,
        )
        cursor.execute(query, values)
        connection.commit()
        return True

    except pymysql.IntegrityError as error:
        if connection.open:
            connection.rollback()
        if error.args and error.args[0] == 1062:
            print("API is already saved:", name)
        else:
            print("Error adding API:", error)
        return False

    except pymysql.Error as error:
        if connection.open:
            connection.rollback()
        print("Error adding API:", error)
        return False

    finally:
        if cursor is not None:
            cursor.close()
        if connection.open:
            connection.close()


def remove_API(api_id):
    """Delete a saved API record from the database using its api_id."""
    if isinstance(api_id, bool):
        print("Invalid API ID.")
        return False

    try:
        api_id = int(api_id)
    except (ValueError, TypeError):
        print("Invalid API ID.")
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
            print("No saved API found with ID:", api_id)
            return False

        return True

    except pymysql.Error as error:
        if connection.open:
            connection.rollback()
        print("Error removing API:", error)
        return False

    finally:
        if cursor is not None:
            cursor.close()
        if connection.open:
            connection.close()
