# ==========================================
# FINAL CODE
# ==========================================

import csv
import json
import logging
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from functions.logger import LOGGER_NAME, configure_logger
from scripts.api_scanner import (
    analyze_security,
    collect_get_candidates,
    evaluate_response,
    extract_base_url,
    format_auth_summary,
    is_valid_public_url,
    save_reports,
    scan_single_api,
)


def _mock_http_response(status_code=200, content_type="application/json", text='{"ok": true}', json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"Content-Type": content_type}
    resp.text = text
    resp.content = text.encode("utf-8")
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = lambda: json.loads(text)
    return resp


class TestApiScannerModules(unittest.TestCase):
    """Offline unit tests verifying split API scanner modules and backward-compatible imports."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._log_file = os.path.join(self._tmpdir.name, "test_scanner.log")
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

    def test_extract_base_url_and_public_url_validation(self):
        spec_v3 = {
            "servers": [
                {
                    "url": "https://{env}.example.org/v1/",
                    "variables": {"env": {"default": "api"}},
                }
            ]
        }
        self.assertEqual(extract_base_url(spec_v3, {}), "https://api.example.org/v1")
        self.assertTrue(is_valid_public_url("https://api.example.org/v1"))
        self.assertFalse(is_valid_public_url("http://localhost:8000/v1"))
        self.assertFalse(is_valid_public_url("https://api.example.org/{tenant}"))
        self.assertFalse(is_valid_public_url("https://api.example.org:70000/v1"))

        spec_v2 = {"host": "data.example.org", "schemes": ["https"], "basePath": "v2"}
        self.assertEqual(extract_base_url(spec_v2, {}), "https://data.example.org/v2")

    def test_analyze_security_and_collect_get_candidates(self):
        spec = {
            "components": {"securitySchemes": {"apiKey": {"type": "apiKey"}}},
            "security": [{"apiKey": []}],
            "paths": {
                "/login": {"get": {}},
                "/public/status": {"get": {"security": []}},
                "/items/{kind}": {
                    "get": {
                        "security": [],
                        "parameters": [
                            {"name": "kind", "in": "path", "required": True, "default": "books"}
                        ],
                    }
                },
            },
        }
        sec_info = analyze_security(spec)
        self.assertTrue(sec_info["global_required"])

        candidates = collect_get_candidates(spec, sec_info)
        self.assertEqual([c["resolved_path"] for c in candidates], ["/public/status", "/items/books"])
        summary = format_auth_summary(spec, sec_info, candidates)
        self.assertIn("Global security declared", summary)
        self.assertIn("unauthenticated access", summary)

    def test_evaluate_response_classifications(self):
        self.assertEqual(evaluate_response(_mock_http_response(200, text='{"items": [1]}'))[0], "WORKING_NO_AUTH")
        self.assertEqual(evaluate_response(_mock_http_response(401, text='{"error": "nope"}'))[0], "AUTH_REQUIRED")
        self.assertEqual(evaluate_response(_mock_http_response(429, text='{"error": "slow"}'))[0], "RATE_LIMITED")
        self.assertEqual(
            evaluate_response(_mock_http_response(200, text='{"error": "API key required"}'))[0],
            "AUTH_REQUIRED",
        )
        self.assertEqual(
            evaluate_response(_mock_http_response(200, content_type="text/html", text="<html>Please sign in</html>"))[0],
            "AUTH_REQUIRED",
        )

    def test_scan_single_api_and_save_reports_mocked(self):
        api_entry = {
            "name": "Demo Public API",
            "provider": "demo.org",
            "category": "open_data",
            "documentation_url": "https://demo.org/docs",
            "specification_url": "https://demo.org/openapi.json",
        }
        spec_payload = {
            "servers": [{"url": "https://api.demo.org/v1"}],
            "paths": {"/health": {"get": {}}},
        }
        spec_resp = _mock_http_response(200, json_data=spec_payload)
        probe_resp = _mock_http_response(200, text='{"status": "ok"}')

        with patch("scripts.scanner_eval.requests.get", side_effect=[spec_resp, probe_resp]):
            result = scan_single_api(api_entry, 1, 1)

        self.assertEqual(result["classification"], "WORKING_NO_AUTH")
        self.assertEqual(result["tested_endpoint"], "/health")
        self.assertEqual(result["http_status_code"], 200)

        json_path = os.path.join(self._tmpdir.name, "report.json")
        csv_path = os.path.join(self._tmpdir.name, "report.csv")
        self.assertTrue(save_reports([result], 1, json_path=json_path, csv_path=csv_path))

        with open(json_path, "r", encoding="utf-8") as jf:
            saved_json = json.load(jf)
        self.assertEqual(saved_json["summary"]["WORKING_NO_AUTH"], 1)

        with open(csv_path, "r", encoding="utf-8", newline="") as cf:
            rows = list(csv.DictReader(cf))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["api_name"], "Demo Public API")


if __name__ == "__main__":
    unittest.main()
