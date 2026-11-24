# ==========================================
# MIDTERM CODE
# ==========================================

import os
import pymysql
from dotenv import load_dotenv

# ==========================================
# FINAL CODE
# ==========================================
from functions.logger import get_logger


# ==========================================
# MIDTERM CODE
# ==========================================
def connect_database():
    """Create and return a MySQL database connection using .env settings."""
    load_dotenv()
    logger = get_logger("lookupapi.database")

    try:
        db_port = int(os.getenv("DB_PORT") or 3306)

        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            port=db_port,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
        )

        logger.info("Database connected successfully.")
        return connection

    except (pymysql.Error, ValueError, TypeError) as error:
        logger.error("Database connection failed (%s).", type(error).__name__)
        return None
