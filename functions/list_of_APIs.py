from functions.database import connect_database

def collect_all_APIs():
    connection=connect_database()
    if connection is None:
        return []
    try:
        c=connection.cursor(dictionary=True)
        c.execute('SELECT * FROM apis')
        APIs=c.fetchall()
        c.close()
        connection.close()
        return APIs
    except Exception as error:
        print('error getting APIs', error)
        connection.close()
        return
    
    
    
def add_API(api):
    required_fields = [
    "name",
    "category",
    "description",
    "endpoint_url",
    "documentation_url",
    "http_method",
    "requires_auth"
    ]

    for i in required_fields:
        if i not in api:
            print("Missing information:", i)
            return False
    connection = connect_database()
    if connection is None:
        return False
    try:
        c = connection.cursor()
        query = """
        INSERT INTO apis
        (name, category, description, endpoint_url,
         documentation_url, http_method, requires_auth)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            api["name"],
            api["category"],
            api["description"],
            api["endpoint_url"],
            api["documentation_url"],
            api["http_method"],
            api["requires_auth"]
        )
        c.execute(query, values)
        connection.commit()
        c.close()
        connection.close()
        return True
    except Exception as error:
        print("Error adding API:", error)
        connection.rollback()
        connection.close()
        return False