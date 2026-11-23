# ==========================================
# FINAL CODE
# ==========================================

from functools import wraps
import time

from functions.logger import get_logger


def log_execution(func):
    """Log function name, execution time in ms, and error type without logging sensitive inputs."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger("lookupapi.decorators")
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception as error:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "Error in %s (%s) after %.1f ms",
                func.__name__,
                type(error).__name__,
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("Completed %s in %.1f ms", func.__name__, elapsed_ms)
        return result

    return wrapper
