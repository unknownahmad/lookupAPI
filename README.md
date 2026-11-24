# LOOKUPAPI

LOOKUPAPI is a Python desktop application I built for browsing, discovering, saving, and testing public REST APIs in one place.

When learning how REST APIs work, you often have to look through long documentation pages to find free endpoints without API keys, check OpenAPI files in one tab, track bookmarks somewhere else, and open a separate HTTP tool to send a request. LOOKUPAPI brings those steps together into a simple desktop app aimed at students and beginner Python developers.

## Features

- **Browse a verified API catalogue:** Load 15 public APIs that do not require API keys from `data/verified_free_apis.json`, grouped alphabetically by category (`Education`, `Entertainment`, `Finance`, `Geography`, `Open Data`, `Science`, `Technology`, and `Weather`).
- **Discover live APIs:** Fetch the public [APIs.guru](https://apis.guru/) directory over HTTPS and search by API name or provider.
- **View API details and endpoints:** Download a discovered API's OpenAPI/Swagger specification to inspect its description, documentation link, base URL, and available endpoints.
- **Test public APIs with `GET`:** Send real HTTP `GET` requests with editable URLs, query parameters, and request headers (only `GET` requests are supported).
- **Inspect responses:** View the HTTP status code, response time in milliseconds, pretty-printed JSON or plain-text output (truncated if very large), and Copy/Clear buttons.
- **Save and manage APIs in MySQL:** Save discovered APIs to a local MySQL database, inspect saved details, and remove entries with confirmation.
- **Activity history:** Log timestamped save and removal actions to `data/activity_log.txt` and view them in the app.

## Technologies

- **Python 3:** Core programming language for the backend logic and GUI.
- **CustomTkinter (`customtkinter`):** Desktop GUI framework used for all screens and controls.
- **Requests (`requests`):** Sends live HTTP `GET` requests to APIs.guru and public APIs.
- **MySQL + PyMySQL (`PyMySQL`):** Stores and retrieves saved APIs in a local relational database.
- **python-dotenv (`python-dotenv`):** Loads MySQL connection settings from a local `.env` file.
- **Python Standard Library:** `unittest` (unit tests), `logging` (application logging), `functools` (decorator wrapper), `re` and `urllib.parse` (URL and header validation), `json` (catalogue and JSON response formatting), `os`, `time`, and `datetime` (file paths, timing, timestamps), plus `threading` and `queue` (keeping the UI responsive during HTTP requests).

## Screenshots and Demo

1. **Home:** Shows summary counts for saved APIs, logged events, and the 15 catalogue APIs, with quick navigation buttons.

<img width="1153" height="714" alt="Screenshot 2026-11-24 at 14 45 41" src="https://github.com/user-attachments/assets/38184f0f-1941-4e39-b53b-0ea58189d321" />

2. **Discover APIs:** Search the APIs.guru directory, open an API to view its OpenAPI specification and endpoints, and click **Save API** to store it in MySQL.

<img width="1153" height="713" alt="Screenshot 2026-11-24 at 14 45 56" src="https://github.com/user-attachments/assets/f054b3e9-572f-429c-94eb-a042ac16ca3b" />

3. **My Saved APIs:** Select a saved API from MySQL to inspect its documentation link, endpoint URL, and description, or remove it.

<img width="1150" height="715" alt="Screenshot 2026-11-24 at 14 46 19" src="https://github.com/user-attachments/assets/fe3d5ed1-4f68-4a39-afbf-84a3b301dbe3" />

4. **Test APIs:** Pick a verified public API by category, edit its URL, parameters, or headers, and click **Send Request** to inspect the live response.

<img width="1148" height="712" alt="Screenshot 2026-11-24 at 14 47 13" src="https://github.com/user-attachments/assets/26389222-0e76-4231-acb3-1c21903ab7a0" />
<img width="1157" height="713" alt="Screenshot 2026-11-24 at 14 48 43" src="https://github.com/user-attachments/assets/81faff09-8586-4443-bff9-7f0a1d418573" />

5. **Activity History:** View timestamped save and remove actions stored in `data/activity_log.txt`.

<img width="1150" height="710" alt="Screenshot 2026-11-24 at 14 46 33" src="https://github.com/user-attachments/assets/d2cde97b-68e6-4972-9a9a-e04149721552" />

### Demo Video

Watch the application walkthrough on GitHub:

https://github.com/user-attachments/assets/3c283c28-6a3c-4f20-99c2-334daa9a5a90

## Project Structure

```text
lookupAPI/
├── main.py                         # Entry point that launches the GUI
├── requirements.txt                # Required third-party Python packages
├── schema.sql                      # MySQL database and apis table creation script
├── .env.example                    # Example MySQL environment variables
├── .gitignore                      # Ignores venv, __pycache__, .env, and runtime logs
├── README.md                       # Project documentation
├── data/
│   ├── verified_free_apis.json     # 15 verified unauthenticated public APIs
│   ├── API_CATALOGUE_REPORT.md     # Verification notes for the 15-API catalogue
│   └── activity_log.txt            # Timestamped save and removal log
├── functions/
│   ├── models.py                   # APIResource, CatalogAPI, and SavedAPI classes
│   ├── catalogue.py                # Catalogue loading, generators, lambda sorting, and notes
│   ├── api_directory.py            # Live APIs.guru fetch, search, and OpenAPI spec parser
│   ├── api_tester.py               # Live HTTP GET tester and response formatter
│   ├── database.py                 # MySQL connection, CRUD queries, and activity integration
│   ├── validators.py               # Regex and urllib.parse validation for URLs and headers
│   ├── decorators.py               # @log_execution decorator using functools.wraps
│   ├── logger.py                   # Standard Python logging setup (console + data/lookupapi.log)
│   └── utils.py                    # Number parsing helpers and activity log read/write helpers
├── tests/
│   └── test_core.py                # Three unit tests for core backend helper functions
└── ui/
    ├── window.py                   # Main window, screen navigation, and Discover APIs view
    ├── menu.py                     # Sidebar, Home, My Saved APIs, and Activity History views
    ├── test_apis_screen.py         # Test APIs catalogue browser and category filter bar
    ├── api_tester_panel.py         # GET request inputs and background request thread
    ├── response_panel.py           # Status/timing badges, response box, and Copy/Clear buttons
    └── theme.py                    # Shared dark theme colors, spacing, and font helpers
```

The backend is organized into `main.py` plus nine focused modules under `functions/` (10 files total), while `ui/` holds the CustomTkinter interface, `data/` holds the JSON catalogue and logs, and `tests/` holds the unit test file.

## How to Install and Run

1. **Clone the repository:**

```bash
git clone https://github.com/unknownahmad/lookupAPI.git
cd lookupAPI
```

2. **Create and activate a virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Create the MySQL database using `schema.sql`:**

Make sure MySQL Server is running locally, then run:

```bash
mysql -u root -p < schema.sql
```

5. **Configure `.env` using `.env.example`:**

Copy `.env.example` to `.env` and fill in your local MySQL credentials:

```bash
cp .env.example .env
```

The `.env.example` file contains:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=lookupapis
```

6. **Run the application:**

```bash
python main.py
```

The desktop window stays open until you click **Exit** in the sidebar or close the window. If MySQL is not running or a network request fails, the app catches the error and continues running without crashing.

## How to Use LOOKUPAPI

1. **Browse the catalogue (`Test APIs`):** Open **Test APIs** from the sidebar or Home screen and filter by category (`All`, `Education`, `Entertainment`, `Finance`, `Geography`, `Open Data`, `Science`, `Technology`, `Weather`).
2. **Test an API:** Select any API in **Test APIs** to prefill its `GET` URL, query parameters, and headers. Edit any values if needed, then click **Send Request** to see the status code, response time in ms, and formatted output.
3. **Discover live APIs (`Discover APIs`):** Open **Discover APIs** to load the APIs.guru directory and type in the search bar to filter by API name or provider.
4. **View API details:** Click any search result to download its OpenAPI specification and inspect its description, documentation link, base URL, and endpoints.
5. **Save an API:** While viewing an API in **Discover APIs**, click **Save API** to store it in your MySQL database.
6. **View or remove saved APIs (`My Saved APIs`):** Open **My Saved APIs** to view saved records from MySQL or select one and click **Remove Saved API** (with confirmation) to delete it.
7. **View activity history (`Activity History`):** Open **Activity History** to see timestamped `Saved` and `Removed` entries recorded in `data/activity_log.txt`.

## Python Concepts Demonstrated

- **Lists, dictionaries, sets, and tuples:** Used throughout the backend—for example, API dictionaries and category lists in `functions/catalogue.py` and `functions/api_directory.py`, `ALLOWED_HTTP_METHODS` (`set`) and `seen_keys` (`set` of deduplication `tuple` keys) in `functions/api_directory.py` and `functions/catalogue.py`, and `SUPPORTED_METHODS = ("GET",)` plus `REQUIRED_API_FIELDS` (`tuple`) in `functions/api_tester.py` and `functions/database.py`.
- **Generators using `yield`:** `iter_catalogue_apis()` and `iter_apis_by_category()` in `functions/catalogue.py` yield validated `CatalogAPI` objects and filtered entries on demand.
- **Lambda functions:** `group_apis_by_category()` in `functions/catalogue.py` uses a `lambda` key function to sort APIs alphabetically by name within each category.
- **Classes and inheritance:** `functions/models.py` defines the base class `APIResource` and two subclasses, `CatalogAPI(APIResource)` and `SavedAPI(APIResource)`, using `super().__init__()` and `super().to_dict()` to handle catalogue entries and MySQL rows consistently.
- **Custom decorator:** `functions/decorators.py` defines `@log_execution` using `functools.wraps` and `time.perf_counter()` to log function execution time and exception types (without logging arguments or credentials), applied in `functions/catalogue.py`, `functions/database.py`, and `functions/api_tester.py`.
- **Exception handling:** Targeted `try`/`except` blocks catch `requests.exceptions` (`Timeout`, `ConnectionError`, `RequestException`) in `functions/api_directory.py` and `functions/api_tester.py`, `pymysql.Error` and `IntegrityError` in `functions/database.py`, and `OSError`/`ValueError` in `functions/catalogue.py` and `functions/utils.py`.
- **Regular expressions:** `functions/validators.py` uses compiled regexes (`URL_REGEX` with `urllib.parse` port validation, and `HEADER_NAME_REGEX` for HTTP header names), and `functions/catalogue.py` uses `re.search()` to extract rate-limit notes.
- **Logging:** `functions/logger.py` configures Python's standard `logging` module (`configure_logger()` and `get_logger()`) to log events to the console and `data/lookupapi.log`.
- **Functions and functional decomposition:** The backend is split into small single-purpose functions across `main.py` and the nine modules in `functions/`.
- **External API integration:** `functions/api_directory.py` fetches live data from `https://api.apis.guru/v2/list.json` and OpenAPI spec URLs, and `functions/api_tester.py` sends real `GET` requests to public APIs using `requests.get()`.
- **Database integration:** `functions/database.py` reads `.env` credentials with `python-dotenv` and runs MySQL `SELECT`, `INSERT`, and `DELETE` queries with `PyMySQL`.

## Unit Testing

The repository includes three beginner-friendly unit tests in `tests/test_core.py` using Python's built-in `unittest` module:

1. **`test_is_valid_url`:** Checks `is_valid_url()` from `functions/validators.py` with one valid HTTPS URL (`True`) and one invalid URL string (`False`).
2. **`test_format_example_endpoint`:** Checks `format_example_endpoint()` from `functions/catalogue.py` using a small dictionary with a path and query parameters.
3. **`test_search_apis`:** Checks `search_apis()` from `functions/api_directory.py` by passing a small two-item list of API dictionaries and verifying the matching API is returned.

Run the tests from the project root:

```bash
python -m unittest discover -s tests -v
```

Note: these three tests cover the three selected backend helper functions above; they do not cover the entire application, live HTTP requests, or the MySQL database.

## Database

Saved APIs are stored in a MySQL database named `lookupapis` with a single table called `apis` defined in `schema.sql`:

| Column | Type | Description |
|---|---|---|
| `api_id` | `INT AUTO_INCREMENT PRIMARY KEY` | Unique ID generated for each saved API |
| `name` | `VARCHAR(100) NOT NULL UNIQUE` | API name (prevents saving duplicate names) |
| `category` | `VARCHAR(50) NOT NULL` | Category label (defaults to `General` when missing) |
| `description` | `TEXT NOT NULL` | Short summary of the API |
| `endpoint_url` | `VARCHAR(500) NOT NULL` | Base URL or endpoint URL of the API |
| `documentation_url` | `VARCHAR(500) NOT NULL` | Link to the API's documentation |
| `http_method` | `VARCHAR(10) NOT NULL DEFAULT 'GET'` | Primary HTTP method |
| `requires_auth` | `TINYINT(1) NOT NULL DEFAULT 0` | Whether authentication is required (`0` or `1`) |

## AI Assistance and Acknowledgements

- **AI Assistance Disclosure:** I used AI assistance for parts of the CustomTkinter graphical interface under `ui/`. The Python backend modules, MySQL integration, external API workflows, tests, and documentation were developed and integrated for my university Python project.
- **Acknowledgements:** Thanks to [APIs.guru](https://apis.guru/) for the public OpenAPI directory, the providers of the 15 public APIs included in `data/verified_free_apis.json`, and the maintainers of CustomTkinter, Requests, PyMySQL, and python-dotenv.
- **Author:** Ahmad Sbai ([unknownahmad](https://github.com/unknownahmad/lookupAPI))
