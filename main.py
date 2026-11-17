
# from functions.database import connect_database


# def main():
#     #test the connection to the apps database... and close it
#     connection = connect_database()

#     if connection:
#         connection.close()
#         print("Closed! All Good")


# if __name__ == "__main__":
#     main()




from functions.list_of_APIs import collect_all_APIs
from functions.list_of_APIs import add_API

def main():
    nasa = {
    "name": "NASA APOD",
    "category": "Science",
    "description": "Astronomy pictures from NASA.",
    "endpoint_url": "https://api.nasa.gov/planetary/apod",
    "documentation_url": "https://api.nasa.gov/",
    "http_method": "GET",
    "requires_auth": True
    }

    result = add_API(nasa)

    if result:
        print("API added successfully!")
        APIs = collect_all_APIs()

    if len(APIs) == 0:
        print("No APIs found.")

    else:
        print("APIs found:")

        for api in APIs:
            print(api["name"])


if __name__ == "__main__":
    main()
