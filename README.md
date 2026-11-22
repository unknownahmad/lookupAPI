# LOOKUPAPI

LOOKUPAPI is a Python desktop application for discovering, organizing, and testing public web APIs. It is built with Python, CustomTkinter, Requests, PyMySQL, and python-dotenv.

## Main Features

- **Discover APIs:** Search the APIs.guru public directory by API name or provider and inspect OpenAPI specifications, versions, descriptions, documentation links, base URLs, and available endpoints with HTTP methods.
- **My Saved APIs:** Save discovered APIs to a local MySQL database, inspect saved endpoint and documentation details, and remove saved entries.
- **Activity History:** View timestamped save, removal, and activity entries stored in `data/activity_log.txt`.
- **Test APIs:** Browse a curated catalogue of 15 verified unauthenticated public APIs grouped by category and send live `GET`, `POST`, `PUT`, and `DELETE` requests with editable URLs, query parameters, headers, and validated JSON request bodies.
- **Response Inspection & Request History:** View HTTP status codes, response times, formatted JSON or raw text output, copy or clear responses, and review past test runs stored in `data/test_request_history.json` (with sensitive query parameters masked and without storing headers or credentials).

## Prerequisites

- Python 3
- MySQL Server (running locally or accessible over the network)

## Installation

1. Clone the repository and move into the project directory:

```bash
git clone https://github.com/unknownahmad/lookupAPI.git
cd lookupAPI
```

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Database and Environment Configuration

1. Create a MySQL database and the `apis` table:

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

2. Create a `.env` file in the project root directory with your local MySQL credentials (`.env` is ignored by Git and should not be committed):

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=lookupapis
```

## Running the Application

Start LOOKUPAPI from the project root directory:

```bash
python main.py
```

## Running Tests

Run the automated unit tests for request history masking and file handling:

```bash
python -m unittest discover -s tests
```
