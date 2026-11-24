import logging
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pymysql

from functions.database import (
    add_API,
    collect_all_APIs,
    connect_database,
    get_saved_APIs,
    get_saved_api_models,
    remove_API,
    remove_saved_API,
    save_API,
)
from functions.logger import LOGGER_NAME, configure_logger
from functions.models import APIResource, SavedAPI
from functions.utils import get_activity, save_activity


class TestSavedAPIsBackend(unittest.TestCase):
    """Offline unit tests for SavedAPI, activity file error handling, and database helpers."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._log_file = os.path.join(self._tmpdir.name, "test_saved_apis.log")
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

    def test_save_api_converts_discover_dict_via_saved_api_model(self):
        discover_entry = {
            "name": "GitHub v3 REST API",
            "base_url": "https://api.github.com",
            "documentation_url": "https://docs.github.com/rest",
            "description": "GitHub REST API",
        }
        with patch("functions.database.add_API", return_value=True) as mock_add, \
             patch("functions.database.save_activity") as mock_activity:
            saved = save_API(discover_entry)

        self.assertTrue(saved)
        mock_add.assert_called_once()
        payload = mock_add.call_args[0][0]
        self.assertEqual(payload["name"], "GitHub v3 REST API")
        self.assertEqual(payload["endpoint_url"], "https://api.github.com")
        self.assertEqual(payload["category"], "General")
        self.assertEqual(payload["http_method"], "GET")
        self.assertIs(payload["requires_auth"], False)
        mock_activity.assert_called_once_with("GitHub v3 REST API", "Saved", "N/A")

    def test_save_api_accepts_saved_api_model_directly(self):
        model = SavedAPI(
            name="Open-Meteo",
            category="Weather",
            endpoint_url="https://api.open-meteo.com/v1",
            description="Forecast API",
            documentation_url="https://open-meteo.com/en/docs",
        )
        with patch("functions.database.add_API", return_value=True) as mock_add, \
             patch("functions.database.save_activity") as mock_activity:
            self.assertTrue(save_API(model))

        self.assertEqual(mock_add.call_args[0][0]["endpoint_url"], "https://api.open-meteo.com/v1")
        mock_activity.assert_called_once_with("Open-Meteo", "Saved", "N/A")

    def test_save_api_rejects_invalid_and_nameless_inputs(self):
        with patch("functions.database.add_API") as mock_add, \
             patch("functions.database.save_activity") as mock_activity:
            self.assertFalse(save_API("not-a-dict"))
            self.assertFalse(save_API(None))
            self.assertFalse(save_API({"name": "   ", "base_url": "https://api.example.test"}))

        mock_add.assert_not_called()
        mock_activity.assert_not_called()

    def test_get_saved_api_models_and_dicts_preserve_mysql_columns(self):
        mysql_rows = [
            {
                "api_id": 16,
                "name": "GitHub v3 REST API",
                "category": "General",
                "description": "GitHub REST API",
                "endpoint_url": "https://api.github.com",
                "documentation_url": "https://docs.github.com/rest",
                "http_method": "GET",
                "requires_auth": 0,
            }
        ]
        with patch("functions.database.collect_all_APIs", return_value=mysql_rows):
            models = get_saved_api_models()
            dicts = get_saved_APIs()

        self.assertEqual(len(models), 1)
        self.assertIsInstance(models[0], SavedAPI)
        self.assertIsInstance(models[0], APIResource)
        self.assertEqual(models[0].api_id, 16)
        self.assertEqual(dicts[0]["api_id"], 16)
        self.assertEqual(dicts[0]["endpoint_url"], "https://api.github.com")
        self.assertIs(dicts[0]["requires_auth"], False)

    def test_remove_saved_api_logs_activity_only_on_success(self):
        mysql_rows = [{"api_id": 21, "name": "ODWeather", "endpoint_url": "https://api.oceandrivers.com/"}]
        with patch("functions.database.collect_all_APIs", return_value=mysql_rows), \
             patch("functions.database.remove_API", return_value=True) as mock_remove, \
             patch("functions.database.save_activity") as mock_activity:
            self.assertTrue(remove_saved_API(21))

        mock_remove.assert_called_once_with(21)
        mock_activity.assert_called_once_with("ODWeather", "Removed", "N/A")

        with patch("functions.database.collect_all_APIs", return_value=mysql_rows), \
             patch("functions.database.remove_API", return_value=False), \
             patch("functions.database.save_activity") as mock_activity_fail:
            self.assertFalse(remove_saved_API(999))

        mock_activity_fail.assert_not_called()

    def test_activity_file_read_write_and_oserror_handling(self):
        activity_path = os.path.join(self._tmpdir.name, "activity.txt")
        self.assertEqual(get_activity(activity_path), [])
        self.assertTrue(save_activity("GitHub API", "Saved", "N/A", file_path=activity_path))

        lines = get_activity(activity_path)
        self.assertEqual(len(lines), 1)
        self.assertIn("GitHub API | Saved | N/A", lines[0])

        with patch("builtins.open", side_effect=OSError("disk read only")):
            self.assertFalse(save_activity("GitHub API", "Saved", "N/A", file_path=activity_path))
            self.assertEqual(get_activity(activity_path), [])

    def test_database_connection_error_never_logs_credentials(self):
        with patch("functions.database.load_dotenv"), \
             patch("functions.database.pymysql.connect", side_effect=pymysql.OperationalError(1045, "Access denied for SECRET_DB_USER")), \
             self.assertLogs(LOGGER_NAME, level="ERROR") as captured:
            conn = connect_database()

        self.assertIsNone(conn)
        combined = "\n".join(captured.output)
        self.assertIn("OperationalError", combined)
        self.assertNotIn("SECRET_DB_USER", combined)

    def test_list_of_apis_validation_and_db_error_handling_mocked(self):
        self.assertFalse(add_API("invalid"))
        self.assertFalse(add_API({"name": "Incomplete"}))
        self.assertFalse(remove_API(True))
        self.assertFalse(remove_API("not-an-int"))

        mock_conn = MagicMock()
        mock_conn.open = True
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        valid_payload = SavedAPI(name="Demo API", endpoint_url="https://api.example.test").to_dict()
        mock_cursor.execute.side_effect = pymysql.IntegrityError(1062, "Duplicate entry")
        with patch("functions.database.connect_database", return_value=mock_conn):
            self.assertFalse(add_API(valid_payload))
        mock_conn.rollback.assert_called_once()

        mock_cursor.execute.side_effect = pymysql.OperationalError(2006, "Server gone")
        with patch("functions.database.connect_database", return_value=mock_conn):
            self.assertEqual(collect_all_APIs(), [])

        mock_cursor.execute.side_effect = None
        mock_cursor.rowcount = 0
        with patch("functions.database.connect_database", return_value=mock_conn):
            self.assertFalse(remove_API(999))


if __name__ == "__main__":
    unittest.main()
