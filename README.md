# LOOKUPAPI

## Project Description

LOOKUPAPI is a Python desktop application for discovering, saving, and testing public web APIs. It combines live OpenAPI directory search (via APIs.guru), persistent MySQL storage for saved APIs, file-based activity and request history logs, and an interactive HTTP tester backed by a verified catalogue of 15 unauthenticated public APIs.

## Problem Being Solved

Students and junior developers learning how to integrate REST APIs often struggle to find reliable, genuinely free public APIs that work without account registration or API keys, inspect their OpenAPI specifications, and test HTTP requests in one place without juggling separate browser tabs, database tools, and external HTTP clients. LOOKUPAPI brings API discovery, specification inspection, bookmarking, and live HTTP testing into a single lightweight desktop tool.

## Intended Users

- Computer science and software engineering students learning REST API integration, HTTP methods, and JSON parsing.
- Beginner Python developers who want a curated set of verified unauthenticated public APIs for practice and prototyping.
- Instructors or evaluators reviewing a modular Python backend with database, external API, validation, logging, and unit-testing integrations.

## Main Features

- **Discover APIs:** Search the live APIs.guru public OpenAPI directory by API name or provider and inspect titles, versions, descriptions, documentation URLs, base URLs, and parsed endpoints with HTTP methods.
- **My Saved APIs (MySQL):** Save discovered APIs to a local MySQL database, review saved endpoint and documentation metadata, and remove saved records with confirmation.
- **Test APIs (15 Verified Unauthenticated Public APIs):** Browse 15 curated, verified no-auth public APIs grouped alphabetically by category (Weather, Finance, Geography, Science, Education, Technology, Entertainment, Open Data) and send live `GET`, `POST`, `PUT`, and `DELETE` requests with editable URLs, query parameters, headers, and validated JSON request bodies.
- **Response Inspection & Request History:** View HTTP status codes, elapsed response time in milliseconds, pretty-printed JSON or raw text responses (with truncation protection for oversized payloads), copy/clear controls, and sanitized request history stored in `data/test_request_history.json` (masking sensitive query parameters and excluding request headers and credentials).
- **Activity History:** View timestamped save and removal events persisted in `data/activity_log.txt`.
- **Research Scanner CLI (`scripts/api_scanner.py`):** Optional modular command-line scanner used to sample APIs.guru specifications and generate JSON/CSV evaluation reports.

## Technology Stack

- **Language:** Python 3
- **GUI Presentation Layer:** CustomTkinter (`customtkinter`)
- **HTTP Client:** Requests (`requests`)
- **Database Driver:** PyMySQL (`PyMySQL`) with MySQL Server
- **Environment Configuration:** `python-dotenv`
- **Standard Library Modules:** `unittest`, `unittest.mock`, `logging`, `functools`, `re`, `urllib.parse`, `json`, `csv`, `os`, `tempfile`, `time`, `datetime`, `threading`, `queue`, `argparse`

## Screenshots

No screenshot images are currently committed to the repository. Before final submission, capture and add the following screenshots (for example under `docs/screenshots/`) and link them here:

1. `docs/screenshots/home.png` — Home dashboard showing summary cards and navigation sidebar.
2. `docs/screenshots/discover.png` — Discover APIs search results and parsed OpenAPI endpoints.
3. `docs/screenshots/saved_apis.png` — My Saved APIs collection loaded from MySQL.
4. `docs/screenshots/test_apis.png` — Test APIs screen showing the 15-API catalogue, request editor (`GET`/`POST`/`PUT`/`DELETE`), and formatted JSON response.
5. `docs/screenshots/request_history.png` — Sanitized Test Request History view and Activity History view.

## Installation

1. Clone the repository and enter the project folder:

```bash
git clone https://github.com/unknownahmad/lookupAPI.git
cd lookupAPI
```

2. Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the project dependencies:

```bash
pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file in the project root directory with your local MySQL connection details. `.env` is listed in `.gitignore` and must never be committed to Git.

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=lookupapis
```

Runtime files `data/lookupapi.log` and `data/test_request_history.json` are also ignored by `.gitignore`.

## Database Setup and SQL Instructions

Make sure MySQL Server is running, then create the `lookupapis` database and the `apis` table:

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

### Launch the Desktop Application

```bash
python main.py
```

### Run the Automated Unit Tests (Offline)

```bash
python -m unittest discover -s tests -v
```

### Run the Research Scanner CLI (Optional)

```bash
python scripts/api_scanner.py --help
```

## How to Use Main Features

1. **Home:** Displays live counts for saved MySQL APIs, activity log entries, verified catalogue APIs, and recorded test runs, with quick navigation buttons.
2. **Discover APIs:** Type an API name or provider (for example, `GitHub` or `NASA`) to filter the APIs.guru directory, click an entry to download and inspect its OpenAPI specification and endpoints, and click **Save API** to store it in MySQL.
3. **My Saved APIs:** Select any saved API from the left list to inspect its documentation URL, endpoint URL, HTTP method, authentication status, and description, or click **Remove Saved API** to delete it from MySQL.
4. **Test APIs:** Choose a category or `All`, select one of the 15 verified public APIs, review or edit the HTTP method (`GET`, `POST`, `PUT`, or `DELETE`), URL, query parameters, headers, or optional JSON body (for `POST`/`PUT`), and click **Send Request**.
5. **Request History:** Click **Request History** on the Test APIs screen to inspect previous test runs (newest first) with status badges, response times, and masked URLs.
6. **Activity History:** Open **Activity History** from the sidebar to review timestamped save and removal actions stored in `data/activity_log.txt`.

## Demo GIF / Video

No demo recording is currently committed to the repository. Before final submission, record a short 60–90 second walkthrough video or GIF showing:

1. Launching `python main.py` and viewing the Home dashboard.
2. Searching and saving an API from Discover APIs to MySQL.
3. Viewing and deleting a record in My Saved APIs and checking Activity History.
4. Sending a live request in Test APIs and inspecting the formatted JSON response and Request History.
5. Running `python -m unittest discover -s tests -v` in the terminal.

## Completed Functionality

- Modular Python backend organized under `functions/` and `scripts/`, with all backend modules under 300 lines and all backend functions under 80 lines.
- Object-oriented domain models (`APIResource`, `CatalogAPI`, `SavedAPI`) actively integrated into catalogue loading and MySQL saved-API operations.
- Safe `@log_execution` decorator and centralized Python `logging` (`functions/logger.py`) that avoid logging credentials, headers, query parameters, or sensitive inputs.
- Explicit `yield` generators for streaming validated catalogue APIs (`iter_catalogue_apis`, `iter_apis_by_category`) and request history entries (`iter_request_history`).
- Active `lambda` sorting for alphabetically ordering APIs within categories (`group_apis_by_category`).
- Compiled regular expressions combined with `urllib.parse` for URL, port, RFC header-name, and rate-limit validation.
- Full `GET`, `POST`, `PUT`, and `DELETE` HTTP testing with JSON body validation, timeout handling, HTTP 429 rate-limit reporting, and sensitive query parameter masking.
- 49 offline unit tests across 7 test modules covering models, inheritance, decorator behavior, catalogue operations, saved APIs, file/database error handling, API request validation/execution, request history masking/streaming, and the modular API scanner.

## TODO / Future Improvements

- Capture and embed application screenshots and a short demo video/GIF in the repository before final presentation.
- Refactor oversized AI-assisted frontend layout functions (`ui/api_tester_panel.py`, `ui/menu.py`, `ui/test_apis_screen.py`, `ui/window.py`) into smaller UI helpers if strict file/function line limits are applied to the presentation layer.
- Add export/import support for saved API collections and optional custom request collections.
- Add optional search filtering inside the Test APIs catalogue and Request History panel.

## Project Structure

```text
lookupAPI/
├── main.py                         # Application entry point
├── requirements.txt                # Project Python dependencies
├── README.md                       # Project documentation and self-assessment
├── .gitignore                      # Ignores .env, venv, caches, runtime logs/history
├── data/
│   ├── verified_free_apis.json     # Curated catalogue of 15 verified no-auth public APIs
│   ├── verified_free_apis.csv      # CSV export of the 15 verified public APIs
│   ├── API_CATALOGUE_REPORT.md     # Verification report for the public API catalogue
│   ├── api_test_results.json       # Raw scanner research output (JSON)
│   ├── api_test_results.csv        # Raw scanner research output (CSV)
│   └── activity_log.txt            # Timestamped save/remove activity log
├── functions/
│   ├── models.py                   # APIResource, CatalogAPI(APIResource), SavedAPI(APIResource)
│   ├── logger.py                   # Centralized Python logging setup (no duplicate handlers)
│   ├── decorators.py               # Safe @log_execution decorator using functools.wraps
│   ├── validators.py               # Regex + urllib.parse URL, header, and JSON validators
│   ├── api_tester.py               # Modular GET/POST/PUT/DELETE request runner and formatter
│   ├── test_catalogue.py           # Catalogue generators, CatalogAPI integration, lambda sorting
│   ├── request_history.py          # Sensitive param masking, atomic JSON save, yield generator
│   ├── saved_apis.py               # SavedAPI integration with MySQL CRUD and activity log
│   ├── list_of_APIs.py             # MySQL CRUD queries for the apis table
│   ├── database.py                 # PyMySQL connection setup via .env
│   ├── activity.py                 # UTF-8 activity file read/write with OSError handling
│   ├── api_directory.py            # Live APIs.guru directory fetch and search
│   └── api_details.py              # Live OpenAPI/Swagger specification parser
├── scripts/
│   ├── api_scanner.py              # CLI entry point, APIs.guru discovery, diverse sampling
│   ├── scanner_spec.py             # OpenAPI/Swagger security and GET endpoint extraction
│   └── scanner_eval.py             # Endpoint probing, response classification, report export
├── tests/
│   ├── test_models.py              # Inheritance, round-trips, real catalogue & MySQL models
│   ├── test_decorators.py          # @log_execution metadata, timing, errors, privacy
│   ├── test_catalogue.py           # Catalogue loading, generators, lambda sorting, validation
│   ├── test_saved_apis.py          # SavedAPI integration, activity OSError, mocked DB errors
│   ├── test_api_tester.py          # HTTP methods, regex validation, formatting, response card
│   ├── test_request_history.py     # Masking, yield generator, atomic save, malformed files
│   └── test_api_scanner.py         # Modular scanner parsing, evaluation, report output
└── ui/
    ├── window.py                   # Main window, navigation, Discover APIs screen
    ├── menu.py                     # Sidebar, Home dashboard, Saved APIs & Activity screens
    ├── test_apis_screen.py         # Test APIs catalogue and category filter view
    ├── api_tester_panel.py         # Request configuration form and background thread runner
    ├── response_panel.py           # HTTP status badge, response display, copy/clear controls
    ├── request_history_panel.py    # Recorded test request history cards
    └── theme.py                    # Shared color tokens, spacing, and typography helpers
```

## Acknowledgements

- [APIs.guru](https://apis.guru/) for the open directory of public OpenAPI specifications.
- The public API providers included in `data/verified_free_apis.json` (Open-Meteo, NOAA National Weather Service, Frankfurter / ECB, U.S. Treasury Fiscal Data, Zippopotam.us, USGS Earthquake Hazards Program, NIH PubChem, Open Library / Internet Archive, Crossref, Forem / DEV.to, CIRCL Hashlookup, PokeAPI, TVmaze, APIs.guru, and The World Bank).
- Maintainers of CustomTkinter, Requests, PyMySQL, and python-dotenv.

## Team Information

- **Author:** Ahmad Sbai (GitHub: `unknownahmad`)
- **Project Type:** Individual university Python programming project

## Support

If you encounter setup or runtime issues:

- Confirm your virtual environment is activated and `pip install -r requirements.txt` completed without errors.
- Confirm MySQL Server is running and that `.env` matches your database host, port, username, password, and `lookupapis` schema.
- Run `python -m unittest discover -s tests -v` to verify backend modules offline.
- Open an issue on the repository at https://github.com/unknownahmad/lookupAPI/issues.

## Transparent Self-Assessment Against Course Requirements

This checklist maps each required Python programming concept to its active backend implementation and unit test coverage. No official grade is claimed.

| Requirement | Backend Implementation Evidence | Automated Test Evidence | Status |
|---|---|---|---|
| 1. Dictionaries | Catalogue entries, saved API payloads, HTTP headers/params/results (`functions/models.py`, `functions/api_tester.py`, `functions/test_catalogue.py`, `functions/saved_apis.py`) | `tests/test_models.py`, `tests/test_api_tester.py`, `tests/test_catalogue.py` | Implemented |
| 2. Lists | API listings, grouped category lists, endpoints, request history records (`functions/test_catalogue.py`, `functions/request_history.py`, `functions/api_details.py`) | `tests/test_catalogue.py`, `tests/test_request_history.py` | Implemented |
| 3. Sets | Deduplication keys, sensitive query param names, allowed HTTP methods (`functions/test_catalogue.py`, `functions/request_history.py`, `functions/api_details.py`) | `tests/test_catalogue.py`, `tests/test_request_history.py` | Implemented |
| 4. Tuples | Supported HTTP methods, required DB fields, deduplication keys, validation return pairs (`functions/api_tester.py`, `functions/list_of_APIs.py`, `functions/validators.py`) | `tests/test_api_tester.py`, `tests/test_saved_apis.py` | Implemented |
| 5. Generators (`yield`) | `iter_catalogue_apis()` and `iter_apis_by_category()` in `functions/test_catalogue.py`; `iter_request_history()` in `functions/request_history.py` | `tests/test_catalogue.py`, `tests/test_request_history.py` | Implemented |
| 6. Lambda functions | Alphabetical sorting of APIs within each category in `group_apis_by_category()` (`functions/test_catalogue.py`); candidate sorting in `scripts/scanner_spec.py` | `tests/test_catalogue.py`, `tests/test_api_scanner.py` | Implemented |
| 7. Application classes (`>= 2`) | `APIResource`, `CatalogAPI`, and `SavedAPI` (`functions/models.py`), actively used by `functions/test_catalogue.py`, `functions/saved_apis.py`, and `functions/api_tester.py` | `tests/test_models.py`, `tests/test_catalogue.py`, `tests/test_saved_apis.py` | Implemented |
| 8. Inheritance | `CatalogAPI(APIResource)` and `SavedAPI(APIResource)` using `super().__init__()` and `super().to_dict()` (`functions/models.py`) | `tests/test_models.py` (`issubclass`, `isinstance`) | Implemented |
| 9. Decorators | `@log_execution` using `functools.wraps` (`functions/decorators.py`), applied to `load_verified_free_apis`, `save_API`, `get_saved_APIs`, `remove_saved_API`, `save_request_history`, and `send_api_request` | `tests/test_decorators.py`, `tests/test_api_tester.py`, `tests/test_saved_apis.py` | Implemented |
| 10. Exception handling (`try`/`except`) | Targeted `OSError`, `ValueError`, `json.JSONDecodeError`, `pymysql.Error`/`IntegrityError`, and `requests.exceptions.*` handling across `functions/` and `scripts/` | `tests/test_saved_apis.py`, `tests/test_request_history.py`, `tests/test_api_tester.py`, `tests/test_catalogue.py` | Implemented |
| 11. Regular expressions | `URL_REGEX` (`functions/models.py`), `HEADER_NAME_REGEX` (`functions/validators.py`), rate-limit patterns (`functions/test_catalogue.py`), `PATH_VAR_REGEX` (`scripts/scanner_spec.py`) | `tests/test_models.py`, `tests/test_api_tester.py`, `tests/test_catalogue.py`, `tests/test_api_scanner.py` | Implemented |
| 12. Standard `logging` | `configure_logger()` and `get_logger()` (`functions/logger.py`), integrated across `decorators.py`, `test_catalogue.py`, `saved_apis.py`, `activity.py`, `database.py`, `list_of_APIs.py`, `request_history.py`, `api_tester.py`, and `scanner_eval.py` | `tests/test_decorators.py`, `tests/test_api_tester.py`, `tests/test_saved_apis.py`, `tests/test_request_history.py` | Implemented |
| 13. External API integration | Live HTTP integration via `requests` in `functions/api_directory.py`, `functions/api_details.py`, and `functions/api_tester.py` | `tests/test_api_tester.py`, `tests/test_api_scanner.py` (offline mocked) | Implemented |
| 14. Database integration | MySQL CRUD operations via `PyMySQL` in `functions/database.py`, `functions/list_of_APIs.py`, and `functions/saved_apis.py` | `tests/test_saved_apis.py`, `tests/test_models.py` | Implemented |
| 15. Unit testing (`>= 3` functions) | 49 offline unit tests across 7 modules in `tests/` using `unittest`, `unittest.mock`, and temporary directories | `python -m unittest discover -s tests -v` (49/49 passing) | Implemented |
| 16. Decomposition & modularity | All 17 backend files (`main.py`, `functions/*.py`, `scripts/*.py`) are <= 300 lines and all backend functions are <= 80 lines | Verified via AST audit | Implemented (backend) |

### Honest Notes on Remaining Items

- **Frontend line counts:** The CustomTkinter presentation layer (`ui/`) was built with AI assistance and intentionally preserved without unnecessary redesign. Four UI files currently exceed the 300-line file or 80-line function guideline (`ui/menu.py`: 375 lines; `ui/window.py`: 315 lines; `ui/api_tester_panel.py`: 302 lines, `render_tester_panel` 115 lines; `ui/test_apis_screen.py`: 289 lines, `render_test_api_details` 92 lines and `show_test_apis_screen` 88 lines). All backend and test files satisfy both limits.
- **Manual media still required:** Application screenshots and a short demo GIF/video are not yet committed and should be captured by the student before final submission.
