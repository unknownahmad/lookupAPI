
from functions.database import connect_database


def main():
    #test the connection to the apps database... and close it
    connection = connect_database()

    if connection:
        connection.close()
        print("Closed! All Good")


if __name__ == "__main__":
    main()
