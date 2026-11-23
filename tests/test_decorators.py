# ==========================================
# FINAL CODE
# ==========================================

import logging
import os
import tempfile
import unittest

from functions.decorators import log_execution
from functions.logger import LOGGER_NAME, configure_logger


class TestLogExecutionDecorator(unittest.TestCase):
    """Unit tests for the safe @log_execution backend decorator."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._log_file = os.path.join(self._tmpdir.name, "test_lookupapi.log")
        self._reset_logger()
        configure_logger(LOGGER_NAME, log_file=self._log_file)

    def tearDown(self):
        self._reset_logger()
        self._tmpdir.cleanup()

    def _reset_logger(self):
        base_logger = logging.getLogger(LOGGER_NAME)
        for handler in list(base_logger.handlers):
            handler.flush()
            handler.close()
            base_logger.removeHandler(handler)

    def test_normal_execution_logs_name_and_elapsed_ms(self):
        @log_execution
        def add_numbers(a, b):
            """Return the sum of two numbers."""
            return a + b

        with self.assertLogs(LOGGER_NAME, level="INFO") as captured:
            result = add_numbers(4, 6)

        self.assertEqual(result, 10)
        combined = "\n".join(captured.output)
        self.assertIn("Completed add_numbers in ", combined)
        self.assertIn(" ms", combined)

    def test_preserves_wrapped_function_metadata(self):
        @log_execution
        def sample_operation():
            """Sample backend docstring."""
            return "ok"

        self.assertEqual(sample_operation.__name__, "sample_operation")
        self.assertEqual(sample_operation.__doc__, "Sample backend docstring.")

    def test_logs_error_type_and_reraises_original_exception(self):
        @log_execution
        def failing_operation(url, headers=None):
            raise ValueError("secret_token=DO_NOT_LOG_THIS")

        with self.assertLogs(LOGGER_NAME, level="ERROR") as captured:
            with self.assertRaises(ValueError) as ctx:
                failing_operation(
                    "https://api.example.test/v1?api_key=MY_SECRET_KEY",
                    headers={"Authorization": "Bearer TOP_SECRET"},
                )

        self.assertIn("secret_token=DO_NOT_LOG_THIS", str(ctx.exception))
        combined = "\n".join(captured.output)
        self.assertIn("Error in failing_operation (ValueError)", combined)
        self.assertNotIn("MY_SECRET_KEY", combined)
        self.assertNotIn("TOP_SECRET", combined)
        self.assertNotIn("DO_NOT_LOG_THIS", combined)
        self.assertNotIn("api.example.test", combined)

    def test_never_logs_sensitive_arguments_on_success(self):
        @log_execution
        def fetch_with_secrets(url, token="", password=""):
            return {"status": "ok"}

        with self.assertLogs(LOGGER_NAME, level="INFO") as captured:
            res = fetch_with_secrets(
                "https://api.example.test/private?token=SECRET_QUERY_VAL",
                token="SECRET_TOKEN_123",
                password="SECRET_PASSWORD_456",
            )

        self.assertEqual(res, {"status": "ok"})
        combined = "\n".join(captured.output)
        self.assertIn("Completed fetch_with_secrets", combined)
        for secret in ("SECRET_QUERY_VAL", "SECRET_TOKEN_123", "SECRET_PASSWORD_456", "api.example.test"):
            self.assertNotIn(secret, combined)


if __name__ == "__main__":
    unittest.main()
