# LOOKUPAPI

LOOKUPAPI is a Python desktop application I built for discovering, saving, and testing public REST APIs in one place. It connects to the live APIs.guru directory to browse OpenAPI specifications, stores saved APIs in a local MySQL database, records save and removal actions in `data/activity_log.txt`, and includes a `GET` request tester preloaded with 15 verified public APIs that work without API keys.

## What It Does

When learning how to work with REST APIs, a lot of time goes into finding public APIs that actually work without registration, reading through long specification files to find endpoints, and switching between a browser, a database client, and an HTTP tool just to send a basic request. LOOKUPAPI brings those steps together inside one desktop app aimed at students and beginner Python developers.

## Main Features

- **Discover APIs:** Fetches the live APIs.guru public OpenAPI directory, lets you filter by API name or provider, and downloads full OpenAPI/Swagger specifications to display base URLs, documentation links, and available endpoints.
- **My Saved APIs:** Saves discovered APIs to a local MySQL database (`apis` table), displays their stored metadata, and lets you delete entries with confirmation.
- **Test APIs (`GET` Only):** Loads 15 verified unauthenticated public APIs from `data/verified_free_apis.json`, grouped alphabetically by category (`Education`, `Entertainment`, `Finance`, `Geography`, `Open Data`, `Science`, `Technology`, and `Weather`), and sends real HTTP `GET` requests with editable URLs, query parameters, and headers.
- **Response Viewer:** Displays the HTTP status code, response time in milliseconds, pretty-printed JSON or plain-text responses (with truncation for large payloads), and Copy/Clear buttons.
- **Activity History:** Logs timestamped save and removal actions to `data/activity_log.txt` and displays them inside the app.

## Technologies and Libraries Used

- **Python 3**
- **CustomTkinter** (`customtkinter`) for the desktop GUI
- **Requests** (`requests`) for live HTTP calls to APIs.guru and public REST APIs
- **PyMySQL** (`PyMySQL`) + **MySQL Server** for persistent storage
- **python-dotenv** (`python-dotenv`) for reading database credentials from `.env`
- **Python Standard Library:** `unittest`, `unittest.mock`, `logging`, `functools`, `re`, `urllib.parse`, `json`, `os`, `time`, `datetime`, `threading`, `queue`, `tempfile`

## Project Folder Structure

```text
lookupAPI/
├── main.py                         # Application entry point
├── requirements.txt                # Required third-party Python packages
├── schema.sql                      # MySQL database and apis table setup script
├── .env.example                    # Example environment variables for MySQL config
├── .gitignore                      # Ignores venv, caches, .env, and runtime logs
├── README.md                       # Project documentation
├── data/
│   ├── verified_free_apis.json     # 15 verified unauthenticated public APIs
│   ├── API_CATALOGUE_REPORT.md     # Verification notes for the 15-API catalogue
│   └── activity_log.txt            # Timestamped save and removal history
├── functions/
│   ├── models.py                   # APIResource, CatalogAPI, and SavedAPI classes
│   ├── catalogue.py                # Catalogue loading, generators, lambda sorting, and metadata helpers
│   ├── api_directory.py            # Live APIs.guru directory fetch, search, and OpenAPI parser
│   ├── api_tester.py               # Real HTTP GET request runner and JSON/text response formatter
│   ├── database.py                 # MySQL connection, CRUD operations, and SavedAPI persistence
│   ├── validators.py               # Regex and urllib.parse validation for URLs and HTTP headers
│   ├── decorators.py               # @log_execution decorator using functools.wraps
│   ├── logger.py                   # Standard Python logging configuration (console + file)
│   └── utils.py                    # Type conversion helpers and activity log read/write helpers
├── tests/
│   ├── test_models.py              # Class inheritance, round-trips, and URL/port checks
│   ├── test_decorators.py          # @log_execution metadata, timing, errors, and secret safety
│   ├── test_catalogue.py           # Catalogue validation, generators, lambda sorting, and helpers
│   ├── test_api_directory.py       # APIs.guru fetch/caching, search, and OpenAPI spec parsing
│   ├── test_saved_apis.py          # SavedAPI mapping, activity file handling, and mocked DB CRUD
│   └── test_api_tester.py          # GET tester, method checks, header validation, response panel
└── ui/
    ├── window.py                   # Main window, navigation, and Discover APIs screen
    ├── menu.py                     # Sidebar, Home, My Saved APIs, and Activity History screens
    ├── test_apis_screen.py         # Test APIs catalogue browser and category filter
    ├── api_tester_panel.py         # GET request inputs and background worker thread
    ├── response_panel.py           # Status/timing badges, response box, copy/clear buttons
    └── theme.py                    # Shared colors, spacing, and font helpers
```

## Backend Modules Explained

- `main.py` — Calls `start_application()` from `ui/window.py` to launch the desktop GUI.
- `functions/models.py` — Defines the base class `APIResource` and two subclasses (`CatalogAPI` and `SavedAPI`) using `super()` so catalogue entries and MySQL records follow consistent formats.
- `functions/catalogue.py` — Reads `data/verified_free_apis.json`, validates entries using generator functions (`iter_catalogue_apis`, `iter_apis_by_category` with `yield`), deduplicates with a `set` of `tuple` keys, sorts APIs alphabetically with a `lambda` expression, and extracts attribution/rate-limit notes.
- `functions/api_directory.py` — Fetches and caches the live APIs.guru directory JSON, filters results by name or provider, and parses OpenAPI/Swagger specifications into base URLs and endpoint lists.
- `functions/api_tester.py` — Prepares and executes live HTTP `GET` requests via `requests.get`, handles timeouts/connection errors/HTTP 4xx/429 responses cleanly, and formats JSON or plain-text responses.
- `functions/database.py` — Reads `.env` credentials via `python-dotenv`, connects to MySQL with `PyMySQL`, implements `collect_all_APIs()`, `add_API()`, and `remove_API()`, and wraps them with `SavedAPI` models and activity logging (`save_API()`, `get_saved_APIs()`, `remove_saved_API()`).
- `functions/validators.py` — Uses compiled regular expressions (`URL_REGEX`, `HEADER_NAME_REGEX`) and `urllib.parse` to check URL schemes, hostnames, ports (`1–65535`), and HTTP header safety before any request is sent.
- `functions/decorators.py` — Implements `@log_execution` using `functools.wraps` and `time.perf_counter()` to log execution time and exception types without logging sensitive arguments.
- `functions/logger.py` — Configures the standard Python `logging` logger (`lookupapi`) to write safely to both the console and `data/lookupapi.log`.
- `functions/utils.py` — Holds small shared helpers for safe `int`/`float` parsing and reading/writing `data/activity_log.txt`.

## Database Setup

1. Make sure MySQL Server is installed and running locally.
2. Create the `lookupapis` database and `apis` table using the included [schema.sql](schema.sql) file:

```bash
mysql -u root -p < schema.sql
```

Or run the SQL manually in MySQL:

```sql
CREATE DATABASE IF NOT EXISTS lookupapis;
USE lookupapis;

CREATE TABLE IF NOT EXISTS apis (
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

## `.env` Configuration

Copy `.env.example` to `.env` and fill in your local MySQL credentials (never commit `.env`; both `.env` and `data/lookupapi.log` are ignored by `.gitignore`):

```bash
cp .env.example .env
```

Example variables in `.env.example`:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=lookupapis
```

## Installation

```bash
git clone https://github.com/unknownahmad/lookupAPI.git
cd lookupAPI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## How to Run the Application

Make sure your virtual environment is active and MySQL is running (if MySQL is stopped, the rest of the app still launches and reports database errors gracefully):

```bash
python main.py
```

The GUI window stays open until you click **Exit** in the sidebar or close the window.

## How to Run the Unit Tests

Run the full offline unit test suite (42 tests across 6 test files, using mocks and temporary files so no network or MySQL server is needed):

```bash
python -m unittest discover -s tests -v
```

## Examples of Real External API Integrations

LOOKUPAPI communicates with live public endpoints over HTTPS:

1. **APIs.guru OpenAPI Directory (Live Discovery)**
   - **Endpoint:** `GET https://api.apis.guru/v2/list.json`
   - **Used in:** `functions/api_directory.py` (`get_api_directory()`, followed by `get_api_details()` fetching each API's `swaggerUrl` OpenAPI JSON).
2. **Open-Meteo Weather Forecast API (Live `GET` Test Example)**
   - **Endpoint:** `GET https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true`
   - **Returns:** Live weather JSON (`temperature`, `windspeed`, `weathercode`) without authentication.
3. **Frankfurter Exchange Rates API (Live `GET` Test Example)**
   - **Endpoint:** `GET https://api.frankfurter.dev/v1/latest?base=EUR&symbols=USD,GBP,JPY`
   - **Returns:** Live European Central Bank reference exchange rates in JSON without an API key.

## Screenshots

1. **Home:** Shows summary counts for saved MySQL APIs, activity log entries, and the 15 verified catalogue APIs, with quick navigation buttons.

<img width="1153" height="714" alt="Screenshot 2026-11-24 at 14 45 41" src="https://github.com/user-attachments/assets/38184f0f-1941-4e39-b53b-0ea58189d321" />

2. **Discover APIs:** Filter the APIs.guru catalogue by name or provider, inspect OpenAPI specifications and endpoints, and click **Save API** to store an API in MySQL.

<img width="1153" height="713" alt="Screenshot 2026-11-24 at 14 45 56" src="https://github.com/user-attachments/assets/f054b3e9-572f-429c-94eb-a042ac16ca3b" />

3. **My Saved APIs:** Select any saved API from the database to inspect its documentation link, endpoint URL, and description, or remove it from MySQL.

<img width="1150" height="715" alt="Screenshot 2026-11-24 at 14 46 19" src="https://github.com/user-attachments/assets/fe3d5ed1-4f68-4a39-afbf-84a3b301dbe3" />

4. **Test APIs:** Filter the 15 verified public APIs by category, prefill the `GET` URL, query parameters, and headers, and click **Send Request** to inspect the formatted JSON or raw response.

<img width="1148" height="712" alt="Screenshot 2026-11-24 at 14 47 13" src="https://github.com/user-attachments/assets/26389222-0e76-4231-acb3-1c21903ab7a0" />
<img width="1157" height="713" alt="Screenshot 2026-11-24 at 14 48 43" src="https://github.com/user-attachments/assets/81faff09-8586-4443-bff9-7f0a1d418573" />

5. **Activity History:** View timestamped save and removal events recorded in `data/activity_log.txt`.

<img width="1150" height="710" alt="Screenshot 2026-11-24 at 14 46 33" src="https://github.com/user-attachments/assets/d2cde97b-68e6-4972-9a9a-e04149721552" />

## Demo Video

Watch the LOOKUPAPI walkthrough:

https://github.com/user-attachments/assets/3c283c28-6a3c-4f20-99c2-334daa9a5a90

## Academic Python Requirement Mapping

| Requirement | Where It Is Implemented in the Backend | Unit Tests |
|---|---|---|
| Dictionaries | Catalogue entries, MySQL row dicts, HTTP params/headers/results (`models.py`, `api_tester.py`, `catalogue.py`, `database.py`) | `test_models.py`, `test_api_tester.py`, `test_catalogue.py` |
| Lists | API lists, grouped category lists, parsed endpoints, activity log lines (`catalogue.py`, `api_directory.py`, `utils.py`) | `test_catalogue.py`, `test_api_directory.py`, `test_saved_apis.py` |
| Sets | Catalogue deduplication keys and allowed OpenAPI HTTP methods (`catalogue.py`, `api_directory.py`) | `test_catalogue.py`, `test_api_directory.py` |
| Tuples | `SUPPORTED_METHODS = ("GET",)`, `REQUIRED_API_FIELDS`, dedupe tuples, validator `(ok, value)` pairs (`api_tester.py`, `database.py`, `validators.py`) | `test_api_tester.py`, `test_saved_apis.py` |
| Generators (`yield`) | `iter_catalogue_apis()` and `iter_apis_by_category()` (`functions/catalogue.py`) | `test_catalogue.py` |
| Lambda expressions | Alphabetical API sorting by name in `group_apis_by_category()` (`functions/catalogue.py`) | `test_catalogue.py` |
| Classes (`>= 2`) & Inheritance | `APIResource` base class, `CatalogAPI(APIResource)`, and `SavedAPI(APIResource)` (`functions/models.py`) | `test_models.py`, `test_catalogue.py`, `test_saved_apis.py` |
| Custom decorator | `@log_execution` using `functools.wraps` (`functions/decorators.py`) | `test_decorators.py`, `test_api_tester.py`, `test_saved_apis.py` |
| Exception handling | Targeted `try`/`except` for `OSError`, `ValueError`, `pymysql.Error`, and `requests.exceptions.*` | `test_saved_apis.py`, `test_api_tester.py`, `test_catalogue.py`, `test_api_directory.py` |
| Regular expressions | `URL_REGEX`, `HEADER_NAME_REGEX`, and rate-limit patterns (`validators.py`, `catalogue.py`) | `test_models.py`, `test_api_tester.py`, `test_catalogue.py` |
| Standard `logging` | `configure_logger()` and `get_logger()` (`functions/logger.py`) | `test_decorators.py`, `test_api_tester.py`, `test_saved_apis.py` |
| External API integration | Live HTTP integration via `requests` (`api_directory.py`, `api_tester.py`) | `test_api_tester.py`, `test_api_directory.py` |
| MySQL integration | `PyMySQL` CRUD (`database.py`) configured via `.env` | `test_saved_apis.py`, `test_models.py` |
| Unit testing (`>= 3` functions) | 42 offline unit tests across 6 modules in `tests/` | `python -m unittest discover -s tests -v` |
| Functional decomposition | 10 backend Python files (`main.py` + `functions/*.py`), all <= 300 lines and all functions <= 80 lines | Verified via AST audit |

## Acknowledgements & AI Assistance Disclosure

- I used AI assistance for parts of the CustomTkinter interface under `ui/`. I kept the visual interface unchanged and focused my development and simplification work on the Python backend (`main.py` and `functions/`).
- [APIs.guru](https://apis.guru/) for providing the public OpenAPI specification directory.
- Providers of the 15 verified public APIs in `data/verified_free_apis.json` (Open-Meteo, NOAA National Weather Service, Frankfurter / ECB, U.S. Treasury Fiscal Data, Zippopotam.us, USGS Earthquake Hazards Program, NIH PubChem, Open Library, Crossref, DEV.to / Forem, CIRCL Hashlookup, PokéAPI, TVmaze, APIs.guru, and The World Bank).
- Maintainers of CustomTkinter, Requests, PyMySQL, and python-dotenv.

## Support

- **Author:** Ahmad Sbai (`unknownahmad`)
- For setup issues, check `.env` and MySQL settings or open an issue at https://github.com/unknownahmad/lookupAPI/issues.
