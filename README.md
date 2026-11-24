# LOOKUPAPI

LOOKUPAPI is a Python desktop application I built for discovering, saving, and testing public REST APIs in one place. It connects to the APIs.guru directory to browse OpenAPI specifications, stores saved APIs in a local MySQL database, logs save/remove actions to `data/activity_log.txt`, and includes a `GET` request tester preloaded with 15 verified public APIs that work without API keys.

## Why I Built It

When learning how to work with REST APIs, a lot of time goes into finding public APIs that actually work without registration, figuring out their endpoints from long documentation pages, and switching between a browser, a database client, and an HTTP tool just to run a basic request. LOOKUPAPI puts those steps together in a single desktop app aimed at students and beginner Python developers.

## Main Features

- **Discover APIs:** Search the live APIs.guru directory by API name or provider and inspect its description, documentation link, base URL, and OpenAPI endpoints.
- **My Saved APIs:** Save APIs to a local MySQL database, view their saved endpoint and documentation details, and delete entries when you no longer need them.
- **Test APIs (`GET` only):** Browse 15 verified unauthenticated public APIs from `data/verified_free_apis.json`, grouped alphabetically by category (Education, Entertainment, Finance, Geography, Open Data, Science, Technology, and Weather). You can edit the URL, query parameters, and headers before sending a live `GET` request.
- **Response Viewer:** Shows the HTTP status code, response time in milliseconds, and formatted JSON or plain-text output (with truncation for very large responses), along with Copy and Clear buttons.
- **Activity History:** Keeps a timestamped log of saved and removed APIs in `data/activity_log.txt`.

## Tech Stack

- **Python 3**
- **CustomTkinter** for the desktop GUI
- **Requests** for HTTP calls (`APIs.guru` discovery, OpenAPI spec loading, and `GET` testing)
- **PyMySQL** + **MySQL Server** for persistent storage
- **python-dotenv** for database credentials in `.env`
- **Standard library:** `unittest`, `unittest.mock`, `logging`, `functools`, `re`, `urllib.parse`, `json`, `os`, `tempfile`, `time`, `datetime`, `threading`, `queue`

## Setup & Installation

### 1. Clone and set up a virtual environment

```bash
git clone https://github.com/unknownahmad/lookupAPI.git
cd lookupAPI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure MySQL and `.env`

Start MySQL Server locally and create the `lookupapis` database and `apis` table:

```sql
CREATE DATABASE lookupapis;
USE lookupapis;

CREATE TABLE apis (
    api_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    endpoint_url VARCHAR(500) NOT NULL,
    documentation_url VARCHAR(500) NOT NULL,
    http_method VARCHAR(10) NOT NULL DEFAULT 'GET',
    requires_auth TINYINT(1) NOT NULL DEFAULT 0
);
```

Create a `.env` file in the project root with your MySQL connection details (`.env` and generated runtime logs like `data/lookupapi.log` are ignored in `.gitignore`):

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=lookupapis
```

### 3. Run the application and unit tests

Start the desktop app:

```bash
python main.py
```

Run the offline unit test suite (38 tests across 5 modules):

```bash
python -m unittest discover -s tests -v
```

## App Walkthrough

1. **Home:** Shows quick summary counts for saved MySQL APIs, activity log entries, and the 15 verified catalogue APIs, with shortcuts to each screen.

<img width="1153" height="714" alt="Screenshot 2026-11-24 at 14 45 41" src="https://github.com/user-attachments/assets/38184f0f-1941-4e39-b53b-0ea58189d321" />

2. **Discover APIs:** Filter the APIs.guru catalogue by name or provider, click an API to inspect its OpenAPI specification and endpoints, and click **Save API** to store it in MySQL.

<img width="1153" height="713" alt="Screenshot 2026-11-24 at 14 45 56" src="https://github.com/user-attachments/assets/f054b3e9-572f-429c-94eb-a042ac16ca3b" />

3. **My Saved APIs:** Pick any saved API from the database list to inspect its documentation link, endpoint URL, and description, or remove it from MySQL.

<img width="1150" height="715" alt="Screenshot 2026-11-24 at 14 46 19" src="https://github.com/user-attachments/assets/fe3d5ed1-4f68-4a39-afbf-84a3b301dbe3" />

4. **Test APIs:** Choose a category or `All`, select one of the 15 verified public APIs to prefill its `GET` URL, query parameters, and headers, adjust any values if needed, and click **Send Request** to inspect the formatted JSON or raw response.

<img width="1148" height="712" alt="Screenshot 2026-11-24 at 14 47 13" src="https://github.com/user-attachments/assets/26389222-0e76-4231-acb3-1c21903ab7a0" />
<img width="1157" height="713" alt="Screenshot 2026-11-24 at 14 48 43" src="https://github.com/user-attachments/assets/81faff09-8586-4443-bff9-7f0a1d418573" />

5. **Activity History:** Open **Activity History** from the sidebar to review timestamped save and removal events stored in `data/activity_log.txt`.

<img width="1150" height="710" alt="Screenshot 2026-11-24 at 14 46 33" src="https://github.com/user-attachments/assets/d2cde97b-68e6-4972-9a9a-e04149721552" />

## Demo Video

Watch the LOOKUPAPI walkthrough:

https://github.com/user-attachments/assets/3c283c28-6a3c-4f20-99c2-334daa9a5a90

## Project Structure

```text
lookupAPI/
├── main.py                         # App entry point
├── requirements.txt                # Project dependencies
├── README.md                       # Project documentation
├── .gitignore                      # Ignores venv, __pycache__, *.py[cod], .env, lookupapi.log
├── data/
│   ├── verified_free_apis.json     # 15 verified unauthenticated public APIs
│   ├── API_CATALOGUE_REPORT.md     # Notes from verifying the 15-API catalogue
│   └── activity_log.txt            # Timestamped save and removal log
├── functions/
│   ├── models.py                   # APIResource, CatalogAPI(APIResource), SavedAPI(APIResource)
│   ├── logger.py                   # Centralized Python logging setup
│   ├── decorators.py               # @log_execution decorator using functools.wraps
│   ├── validators.py               # Regex and urllib.parse URL/header validation
│   ├── api_tester.py               # GET-only HTTP request runner and response formatter
│   ├── test_catalogue.py           # Catalogue generators, CatalogAPI parsing, lambda sorting
│   ├── saved_apis.py               # SavedAPI conversion for MySQL CRUD and activity log
│   ├── list_of_APIs.py             # MySQL queries for reading, inserting, and deleting APIs
│   ├── database.py                 # PyMySQL connection setup via .env
│   ├── activity.py                 # Read/write helpers for data/activity_log.txt
│   ├── api_directory.py            # APIs.guru directory fetch and search
│   └── api_details.py              # OpenAPI/Swagger specification parser
├── tests/
│   ├── test_models.py              # Inheritance, round-trips, URL/port validation
│   ├── test_decorators.py          # @log_execution metadata, timing, errors, privacy
│   ├── test_catalogue.py           # Catalogue loading, generators, lambda sorting, filtering
│   ├── test_saved_apis.py          # SavedAPI mapping, activity OSError, mocked DB errors
│   └── test_api_tester.py          # GET tester, unsupported method rejection, header validation
└── ui/
    ├── window.py                   # Main window, navigation, Discover APIs screen
    ├── menu.py                     # Sidebar, Home, My Saved APIs, and Activity History screens
    ├── test_apis_screen.py         # Test APIs catalogue browser and category filter
    ├── api_tester_panel.py         # GET request inputs and background request runner
    ├── response_panel.py           # Status/timing badges, response box, copy/clear actions
    └── theme.py                    # Shared colors, spacing, and font helpers
```

## Future Improvements

- Add support for `POST`, `PUT`, and `DELETE` requests with an optional request body editor.
- Add search and export options (e.g. JSON/CSV) for My Saved APIs.
- Split the larger UI layout functions under `ui/` into smaller helper functions.

## Academic Python Requirement Mapping

This table maps each course Python requirement to where it is actively implemented in the backend (`functions/`) and tested under `tests/`:

| Requirement | Where It Is Used in the Backend | Unit Tests |
|---|---|---|
| Dictionaries | Catalogue records, MySQL row dicts, HTTP params/headers/results (`functions/models.py`, `functions/api_tester.py`, `functions/test_catalogue.py`, `functions/saved_apis.py`) | `tests/test_models.py`, `tests/test_api_tester.py`, `tests/test_catalogue.py` |
| Lists | API lists, grouped category lists, parsed OpenAPI endpoints, activity log lines (`functions/test_catalogue.py`, `functions/activity.py`, `functions/api_details.py`) | `tests/test_catalogue.py`, `tests/test_saved_apis.py` |
| Sets | Catalogue deduplication keys and allowed HTTP methods in specs (`functions/test_catalogue.py`, `functions/api_details.py`) | `tests/test_catalogue.py` |
| Tuples | `SUPPORTED_METHODS = ("GET",)`, `REQUIRED_API_FIELDS`, dedupe tuples, validator `(ok, value)` return pairs (`functions/api_tester.py`, `functions/list_of_APIs.py`, `functions/validators.py`) | `tests/test_api_tester.py`, `tests/test_saved_apis.py` |
| Generators (`yield`) | `iter_catalogue_apis()` and `iter_apis_by_category()` in `functions/test_catalogue.py` | `tests/test_catalogue.py` |
| Lambda expressions | Alphabetical API sorting by name inside `group_apis_by_category()` (`functions/test_catalogue.py`) | `tests/test_catalogue.py` |
| Application classes (`>= 2`) | `APIResource`, `CatalogAPI`, and `SavedAPI` (`functions/models.py`), used in `functions/test_catalogue.py`, `functions/saved_apis.py`, and `functions/api_tester.py` | `tests/test_models.py`, `tests/test_catalogue.py`, `tests/test_saved_apis.py` |
| Inheritance | `CatalogAPI(APIResource)` and `SavedAPI(APIResource)` using `super().__init__()` and `super().to_dict()` (`functions/models.py`) | `tests/test_models.py` |
| Decorators | `@log_execution` with `functools.wraps` (`functions/decorators.py`), applied to `load_verified_free_apis`, `save_API`, `get_saved_APIs`, `remove_saved_API`, and `send_api_request` | `tests/test_decorators.py`, `tests/test_api_tester.py`, `tests/test_saved_apis.py` |
| Exception handling | Targeted `try`/`except` blocks for `OSError`, `ValueError`, `pymysql.Error`/`IntegrityError`, and `requests.exceptions.*` across `functions/` | `tests/test_saved_apis.py`, `tests/test_api_tester.py`, `tests/test_catalogue.py` |
| Regular expressions | `URL_REGEX` (`functions/models.py`), `HEADER_NAME_REGEX` (`functions/validators.py`), rate-limit regexes (`functions/test_catalogue.py`) | `tests/test_models.py`, `tests/test_api_tester.py`, `tests/test_catalogue.py` |
| Standard `logging` | `configure_logger()` and `get_logger()` (`functions/logger.py`), used across `decorators.py`, `test_catalogue.py`, `saved_apis.py`, `activity.py`, `database.py`, `list_of_APIs.py`, and `api_tester.py` | `tests/test_decorators.py`, `tests/test_api_tester.py`, `tests/test_saved_apis.py` |
| External API integration | `requests` calls in `functions/api_directory.py`, `functions/api_details.py`, and `functions/api_tester.py` | `tests/test_api_tester.py` (mocked) |
| MySQL integration | `PyMySQL` CRUD in `functions/database.py`, `functions/list_of_APIs.py`, and `functions/saved_apis.py` | `tests/test_saved_apis.py`, `tests/test_models.py` |
| Unit testing | 38 offline unit tests across 5 files in `tests/` using mocks and temp files | `python -m unittest discover -s tests -v` |
| Modularity & line limits | All 13 backend files (`main.py` and `functions/*.py`) are <= 300 lines and all backend functions are <= 80 lines | Verified via AST audit |

### Note on UI Line Counts

I used AI assistance for parts of the CustomTkinter interface. I kept the interface unchanged and focused most of my development work on the Python backend. Four UI files currently exceed the 300-line file or 80-line function guideline: `ui/menu.py` (373 lines), `ui/window.py` (315 lines), `ui/test_apis_screen.py` (251 lines; `render_test_api_details` is 88 lines), and `ui/api_tester_panel.py` (228 lines; `render_tester_panel` is 84 lines). All backend and test files stay within both limits.

## Acknowledgements

- [APIs.guru](https://apis.guru/) for the public OpenAPI specification directory.
- Providers of the 15 public APIs in `data/verified_free_apis.json` (Open-Meteo, NOAA National Weather Service, Frankfurter / ECB, U.S. Treasury Fiscal Data, Zippopotam.us, USGS Earthquake Hazards Program, NIH PubChem, Open Library, Crossref, DEV.to / Forem, CIRCL Hashlookup, PokeAPI, TVmaze, APIs.guru, and The World Bank).
- Maintainers of CustomTkinter, Requests, PyMySQL, and python-dotenv.

## Support

- **Author:** Ahmad Sbai (`unknownahmad`)
- For setup issues, double-check `.env` and MySQL settings or open an issue at https://github.com/unknownahmad/lookupAPI/issues.
