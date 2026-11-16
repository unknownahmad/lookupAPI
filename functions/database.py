
import mysql.connector
from dotenv import load_dotenv
import os

def connect_database():
    #to connect to the database, and return if the connection is successful. 
    load_dotenv()
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )

        print("GOOODDDD databse connected")
        return connection

    except mysql.connector.Error as error:
        print("BADDDDDDD database not connected :", error)
        return None
