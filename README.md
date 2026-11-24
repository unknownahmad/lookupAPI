# LOOKUPAPI

## Project Description

LOOKUPAPI is a Python desktop application for discovering, saving, and testing public web APIs. It combines live OpenAPI directory search (via APIs.guru), persistent MySQL storage for saved APIs, file-based activity and request history logs, and an interactive HTTP `GET` tester backed by a verified catalogue of 15 unauthenticated public APIs.

## Problem Being Solved

Students and beginner developers learning REST API integration often spend significant time searching for genuinely free public APIs that work without account registration or API keys, inspecting OpenAPI specifications, and testing `GET` endpoints across separate browser tabs and tools. LOOKUPAPI brings public API discovery, specification inspection, MySQL bookmarking, and live `GET` endpoint testing into a single straightforward desktop application.

## Intended Users

- Computer science and software engineering students learning REST APIs, HTTP `GET` requests, query parameters, headers, and JSON responses.
- Beginner Python developers looking for verified, unauthenticated public APIs for coursework and prototypes.
- Course evaluators reviewing a modular Python backend with external API integration, MySQL CRUD operations, OOP inheritance, decorators, generators, regular-expression validation, logging, and automated unit tests.

## Main Features

- **Discover APIs:** Search the live APIs.guru public OpenAPI directory by API name or provider and inspect titles, versions, descriptions, documentation URLs, base URLs, and parsed specification endpoints.
- **My Saved APIs (MySQL):** Save discovered APIs to a local MySQL database, inspect saved endpoint and documentation metadata, and remove saved records with confirmation.
- **Test APIs (15 Verified Public APIs · GET-Only):** Browse 15 curated, verified unauthenticated public APIs grouped alphabetically by category (Education, Entertainment, Finance, Geography, Open Data, Science, Technology, Weather) and send live HTTP `GET` requests with editable URLs, query parameters, and request headers.
- **Response Inspection & Request History:** View HTTP status codes, elapsed response time in milliseconds, pretty-printed JSON or raw text responses (with truncation protection for large payloads), copy/clear controls, and sanitized request history stored in `data/test_request_history.json` (masking sensitive query parameters and excluding headers and credentials).
- **Activity History:** View timestamped save and removal events persisted in `data/activity_log.txt`.

## Technology Stack

- **Language:** Python 3
- **GUI Presentation Layer:** CustomTkinter (`customtkinter`)
- **HTTP Client:** Requests (`requests`)
- **Database Driver:** PyMySQL (`PyMySQL`) with MySQL Server
- **Environment Configuration:** `python-dotenv`
- **Standard Library Modules:** `unittest`, `unittest.mock`, `logging`, `functools`, `re`, `urllib.parse`, `json`, `os`, `tempfile`, `time`, `datetime`, `threading`, `queue`

## Screenshots

No screenshot images are currently committed to the repository. Before final submission, capture and add the following screenshots (for example under `docs/screenshots/`) and link them here:

1. `docs/screenshots/home.png` — Home dashboard showing live summary cards and sidebar navigation.
2. `docs/screenshots/discover.png` — Discover APIs directory search and parsed OpenAPI specification details.
3. `docs/screenshots/saved_apis.png` — My Saved APIs collection retrieved from MySQL.
4. `docs/screenshots/test_apis.png` — Test APIs screen showing the 15-API catalogue, `GET` request configuration (URL, query parameters, headers), and formatted JSON response.
5. `docs/screenshots/request_history.png` — Sanitized Test Request History and Activity History views.

## Installation

1. Clone the repository and enter the project directory:

```bash
git clone https://github.com/unknownahmad/lookupAPI.git
cd lookupAPI
```

2. Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file in the project root directory with your local MySQL credentials. `.env` is listed in `.gitignore` and must never be committed to Git.

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=lookupapis
```

Runtime files `data/lookupapi.log` and `data/test_request_history.json` are also excluded by `.gitignore`.

## Database Setup and SQL Instructions

Start MySQL Server locally, then create the `lookupapis` database and `apis` table:

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

## How to Run the Application

### Start the Desktop Application

```bash
python main.py
```

### Run the Offline Unit Test Suite

```bash
python -m unittest discover -s tests -v
```

## How to Use Main Features

1. **Home:** View live counts of saved MySQL APIs, activity log entries, verified catalogue APIs, and recorded test runs, or jump directly to any section.
2. **Discover APIs:** Enter a search term (such as `GitHub` or `NASA`) to filter the APIs.guru directory, click an API to load its OpenAPI specification and endpoints, and click **Save API** to store it in MySQL.
3. **My Saved APIs:** Select a saved record to view its documentation link, endpoint URL, category, and description, or click **Remove Saved API** to delete it from MySQL.
4. **Test APIs:** Filter the 15 verified public APIs by category or `All`, select an API to prefill its verified `GET` URL, example query parameters, and headers, optionally edit any field, and click **Send Request** to inspect the formatted response.
5. **Request History:** Click **Request History** on the Test APIs screen to review past test runs (newest first) with status codes, response times, and masked query parameters.
6. **Activity History:** Open **Activity History** from the sidebar to review timestamped save and removal events from `data/activity_log.txt`.

## Demo GIF / Video

No demo video or GIF is currently committed to the repository. Before final submission, record a short 60–90 second walkthrough demonstrating:

1. Launching `python main.py` and navigating from the Home dashboard.
2. Searching an API in Discover APIs and saving it to MySQL.
3. Viewing and removing a saved API in My Saved APIs and checking Activity History.
4. Executing a live `GET` request in Test APIs and inspecting the formatted JSON response and Request History.
5. Running `python -m unittest discover -s tests -v` in the terminal.

## Completed Functionality

- Modular Python backend under `functions/` where all 14 backend files (`main.py` and `functions/*.py`) are under 300 lines and every backend function is under 80 lines.
- Object-oriented models (`APIResource`, `CatalogAPI`, `SavedAPI`) with inheritance actively used in catalogue loading, `GET` request defaults, and MySQL saved-API operations.
- Safe `@log_execution` decorator (`functools.wraps`) and centralized `logging` (`functions/logger.py`) that record execution timing and error types without logging URLs, headers, query parameters, or credentials.
- Explicit `yield` generators for streaming validated catalogue models (`iter_catalogue_apis`, `iter_apis_by_category`) and request history entries (`iter_request_history`).
- Active `lambda` expression sorting catalogue APIs alphabetically by name inside `group_apis_by_category()`.
- Compiled regular expressions combined with `urllib.parse` for URL, port, RFC header-name, and rate-limit validation.
- `GET`-only HTTP tester supporting editable URLs, query parameters, headers, timeouts, HTTP 429 rate-limit handling, pretty-printed JSON responses, and sensitive query-parameter masking.
- 45 offline unit tests across 6 test modules using `unittest`, `unittest.mock`, and isolated temporary directories.

## TODO / Future Improvements

- Capture and add application screenshots and a short walkthrough GIF/video before final presentation.
- Extend the HTTP tester in future versions to support additional HTTP methods and request bodies where appropriate.
- Split remaining longer CustomTkinter layout helpers in `ui/` if strict presentation-layer line limits are desired.
- Add search and export options for saved APIs and request history.

## Project Structure

```text
lookupAPI/
├── main.py                         # Application entry point
├── requirements.txt                # Project Python dependencies
├── README.md                       # Project documentation and requirement mapping
├── .gitignore                      # Excludes .env, venv, caches, runtime logs/history
├── data/
│   ├── verified_free_apis.json     # Curated catalogue of 15 verified no-auth public APIs
│   ├── verified_free_apis.csv      # CSV version of the 15 verified public APIs
│   ├── API_CATALOGUE_REPORT.md     # Verification documentation for the 15-API catalogue
│   └── activity_log.txt            # Timestamped save/remove activity log
├── functions/
│   ├── models.py                   # APIResource, CatalogAPI(APIResource), SavedAPI(APIResource)
│   ├── logger.py                   # Centralized Python logging configuration
│   ├── decorators.py               # Safe @log_execution decorator using functools.wraps
│   ├── validators.py               # Regex + urllib.parse URL and HTTP header validators
│   ├── api_tester.py               # GET-only HTTP request runner and response formatter
│   ├── test_catalogue.py           # Catalogue generators, CatalogAPI integration, lambda sorting
│   ├── request_history.py          # Query-param masking, atomic JSON save, yield generator
│   ├── saved_apis.py               # SavedAPI integration with MySQL CRUD and activity log
│   ├── list_of_APIs.py             # MySQL CRUD queries for the apis table
│   ├── database.py                 # PyMySQL connection helper using .env
│   ├── activity.py                 # UTF-8 activity log read/write with OSError handling
│   ├── api_directory.py            # Live APIs.guru directory fetch and search
│   └── api_details.py              # Live OpenAPI/Swagger specification parser
├── tests/
│   ├── test_models.py              # Inheritance, round-trips, real catalogue & MySQL models
│   ├── test_decorators.py          # @log_execution metadata, timing, errors, privacy
│   ├── test_catalogue.py           # Catalogue loading, generators, lambda sorting, validation
│   ├── test_saved_apis.py          # SavedAPI integration, activity OSError, mocked DB errors
│   ├── test_api_tester.py          # GET tester, unsupported method rejection, regex validation
│   └── test_request_history.py     # Masking, yield generator, atomic save, malformed files
└── ui/
    ├── window.py                   # Main window, navigation, Discover APIs screen
    ├── menu.py                     # Sidebar, Home dashboard, Saved APIs & Activity screens
    ├── test_apis_screen.py         # Test APIs catalogue and category filter view
    ├── api_tester_panel.py         # GET request configuration form and background worker
    ├── response_panel.py           # HTTP status badge, response viewer, copy/clear controls
    ├── request_history_panel.py    # Recorded test request history cards
    └── theme.py                    # Shared color tokens, spacing, and font helpers
```

## Acknowledgements

- [APIs.guru](https://apis.guru/) for maintaining the public OpenAPI specification directory.
- Providers of the 15 verified public APIs in `data/verified_free_apis.json` (Open-Meteo, NOAA National Weather Service, Frankfurter / ECB, U.S. Treasury Fiscal Data, Zippopotam.us, USGS Earthquake Hazards Program, NIH PubChem, Open Library / Internet Archive, Crossref, Forem / DEV.to, CIRCL Hashlookup, PokeAPI, TVmaze, APIs.guru, and The World Bank).
- Open-source maintainers of CustomTkinter, Requests, PyMySQL, and python-dotenv.

## Team and Support

- **Author:** Ahmad Sbai (GitHub: `unknownahmad`)
- **Project Type:** Individual university Python programming project
- **Support:** Ensure your virtual environment is active, dependencies from `requirements.txt` are installed, and MySQL Server matches your `.env` configuration. Run `python -m unittest discover -s tests -v` to verify backend functionality offline, or open an issue at https://github.com/unknownahmad/lookupAPI/issues.

## Academic Python Requirement Mapping

This checklist maps each required Python programming concept to active backend code and unit tests in the repository. No official grade is claimed.

| Requirement | Backend Implementation Evidence | Automated Test Evidence | Status |
|---|---|---|---|
| 1. Dictionaries | Catalogue entries, saved API payloads, HTTP params/headers/results (`functions/models.py`, `functions/api_tester.py`, `functions/test_catalogue.py`, `functions/saved_apis.py`) | `tests/test_models.py`, `tests/test_api_tester.py`, `tests/test_catalogue.py` | Implemented |
| 2. Lists | Directory listings, grouped category APIs, parsed OpenAPI endpoints, history entries (`functions/test_catalogue.py`, `functions/request_history.py`, `functions/api_details.py`) | `tests/test_catalogue.py`, `tests/test_request_history.py` | Implemented |
| 3. Sets | Catalogue deduplication keys, sensitive query parameter set, allowed spec methods (`functions/test_catalogue.py`, `functions/request_history.py`, `functions/api_details.py`) | `tests/test_catalogue.py`, `tests/test_request_history.py` | Implemented |
| 4. Tuples | `SUPPORTED_METHODS = ("GET",)`, `REQUIRED_API_FIELDS`, deduplication tuples, validator return pairs (`functions/api_tester.py`, `functions/list_of_APIs.py`, `functions/validators.py`) | `tests/test_api_tester.py`, `tests/test_saved_apis.py` | Implemented |
| 5. Generators (`yield`) | `iter_catalogue_apis()` and `iter_apis_by_category()` in `functions/test_catalogue.py`; `iter_request_history()` in `functions/request_history.py` | `tests/test_catalogue.py`, `tests/test_request_history.py` | Implemented |
| 6. Lambda expressions | Alphabetical API name sorting inside `group_apis_by_category()` (`functions/test_catalogue.py`) | `tests/test_catalogue.py` (`test_groups_apis_alphabetically_and_sorts_entries_by_name`) | Implemented |
| 7. Application classes (`>= 2`) | `APIResource`, `CatalogAPI`, and `SavedAPI` (`functions/models.py`), actively used by `functions/test_catalogue.py`, `functions/saved_apis.py`, and `functions/api_tester.py` | `tests/test_models.py`, `tests/test_catalogue.py`, `tests/test_saved_apis.py` | Implemented |
| 8. Inheritance | `CatalogAPI(APIResource)` and `SavedAPI(APIResource)` using `super().__init__()` and `super().to_dict()` (`functions/models.py`) | `tests/test_models.py` (`issubclass`, `isinstance`) | Implemented |
| 9. Decorators | `@log_execution` (`functools.wraps` in `functions/decorators.py`), applied to `load_verified_free_apis`, `save_API`, `get_saved_APIs`, `remove_saved_API`, `save_request_history`, and `send_api_request` | `tests/test_decorators.py`, `tests/test_api_tester.py`, `tests/test_saved_apis.py` | Implemented |
| 10. Exception handling (`try`/`except`) | Targeted `OSError`, `ValueError`, `pymysql.Error`/`IntegrityError`, and `requests.exceptions.*` handlers across `functions/` | `tests/test_saved_apis.py`, `tests/test_request_history.py`, `tests/test_api_tester.py`, `tests/test_catalogue.py` | Implemented |
| 11. Regular expressions | `URL_REGEX` (`functions/models.py`), `HEADER_NAME_REGEX` (`functions/validators.py`), rate-limit patterns (`functions/test_catalogue.py`) | `tests/test_models.py`, `tests/test_api_tester.py`, `tests/test_catalogue.py` | Implemented |
| 12. Standard `logging` | `configure_logger()` and `get_logger()` (`functions/logger.py`) integrated across `decorators.py`, `test_catalogue.py`, `saved_apis.py`, `activity.py`, `database.py`, `list_of_APIs.py`, `request_history.py`, and `api_tester.py` | `tests/test_decorators.py`, `tests/test_api_tester.py`, `tests/test_saved_apis.py`, `tests/test_request_history.py` | Implemented |
| 13. External API integration | Live HTTP integration via `requests` in `functions/api_directory.py`, `functions/api_details.py`, and `functions/api_tester.py` | `tests/test_api_tester.py` (offline mocked) | Implemented |
| 14. Database integration | MySQL CRUD operations via `PyMySQL` in `functions/database.py`, `functions/list_of_APIs.py`, and `functions/saved_apis.py` | `tests/test_saved_apis.py`, `tests/test_models.py` | Implemented |
| 15. Unit testing (`>= 3` functions) | 45 offline unit tests across 6 modules in `tests/` using mocks and isolated temporary files | `python -m unittest discover -s tests -v` (45/45 passing) | Implemented |
| 16. Functional decomposition | All 14 backend files (`main.py`, `functions/*.py`) are <= 300 lines and all backend functions are <= 80 lines | Verified via AST line/function audit | Implemented (backend) |

### Honest Notes on Remaining Items

- **Frontend line counts:** The AI-assisted CustomTkinter presentation layer (`ui/`) was preserved without visual redesign. Four UI files currently exceed the 300-line file or 80-line function guideline (`ui/menu.py`: 375 lines; `ui/window.py`: 315 lines; `ui/test_apis_screen.py`: 289 lines, `render_test_api_details` 92 lines and `show_test_apis_screen` 88 lines; `ui/api_tester_panel.py`: 245 lines, `render_tester_panel` 87 lines). All backend and test files satisfy both limits.
- **Manual media still required:** Application screenshots and a short demo video/GIF are not yet committed and should be captured by the student before submission.
