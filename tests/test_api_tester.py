# ==========================================
# FINAL CODE
# ==========================================

import logging
import os
import tempfile
import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

import requests

from functions.api_tester import (
    DEFAULT_USER_AGENT,
    SUPPORTED_METHODS,
    build_default_request,
    format_response_body,
    send_api_request,
    send_get_request,
)
from functions.logger import LOGGER_NAME, configure_logger
from functions.models import CatalogAPI
from functions.validators import validate_request_headers, validate_request_url
from ui.response_panel import (
    handle_clear_response,
    handle_copy_response,
    update_response_card,
)


def make_mock_response(status_code=200, reason="OK", content_type="application/json", text="{}", headers=None, url="https://api.example.test/v1"):
    """Build a lightweight mock HTTP response object for offline unit tests."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.reason = reason
    resp.headers = {"Content-Type": content_type}
    if headers:
        resp.headers.update(headers)
    resp.text = text
    resp.url = url
    return resp


class TestApiTester(unittest.TestCase):
    """Offline unit tests for GET-only HTTP request validation, formatting, and error handling."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._log_file = os.path.join(self._tmpdir.name, "test_api_tester.log")
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

    def test_build_default_request_populates_get_url_params_and_headers(self):
        self.assertEqual(SUPPORTED_METHODS, ("GET",))
        entry = {
            "base_url": "https://api.example.test/v1/",
            "working_get_endpoint": "latest",
            "example_query_parameters": {"base": "EUR", "limit": 2},
            "default_headers": {"X-Custom": "Demo"},
        }
        req = build_default_request(entry)
        self.assertEqual(req["method"], "GET")
        self.assertEqual(req["url"], "https://api.example.test/v1/latest")
        self.assertEqual(req["params"], {"base": "EUR", "limit": "2"})
        self.assertEqual(req["headers"]["Accept"], "application/json")
        self.assertEqual(req["headers"]["User-Agent"], DEFAULT_USER_AGENT)
        self.assertEqual(req["headers"]["X-Custom"], "Demo")
        self.assertNotIn("body", req)
        self.assertNotIn("@", DEFAULT_USER_AGENT)

        catalog_model = CatalogAPI(
            name="Model API",
            endpoint_url="https://api.example.test/v2",
            sample_endpoint="/items",
            example_query_parameters={"limit": "3"},
        )
        model_req = build_default_request(catalog_model)
        self.assertEqual(model_req["url"], "https://api.example.test/v2/items")
        self.assertEqual(model_req["params"], {"limit": "3"})

    def test_validate_request_url_accepts_valid_and_rejects_invalid(self):
        self.assertEqual(validate_request_url("https://api.example.test/v1")[0], True)
        self.assertEqual(validate_request_url("http://127.0.0.1:8000/items")[0], True)

        for bad_url in (
            "",
            "   ",
            "not-a-url",
            "ftp://example.test/file",
            "https://bad url.test",
            "https://:8080/missing-host",
            "https://api.example.test:notaport/v1",
            "https://api.example.test:70000/v1",
            "https://api.example.test:0/v1",
        ):
            valid, message = validate_request_url(bad_url)
            self.assertFalse(valid, f"Expected invalid URL: {bad_url!r}")
            self.assertTrue(bool(message))

    def test_rejects_invalid_headers_and_timeouts_without_network_calls(self):
        ok_hdr, clean_hdr, err_hdr = validate_request_headers(
            {"Accept": "application/json", "X-Custom-1": "ok", " ": "ignored"}
        )
        self.assertTrue(ok_hdr)
        self.assertEqual(clean_hdr, {"Accept": "application/json", "X-Custom-1": "ok"})
        self.assertEqual(err_hdr, "")

        bad_hdr_ok, _, bad_hdr_err = validate_request_headers({"X-Test": "value\r\nInjected: bad"})
        self.assertFalse(bad_hdr_ok)
        self.assertIn("newline", bad_hdr_err.lower())

        for bad_name in ("Bad Header", "X-Bad:Name", "X/Invalid"):
            ok_name, _, err_name = validate_request_headers({bad_name: "value"})
            self.assertFalse(ok_name, f"Expected invalid header name: {bad_name!r}")
            self.assertIn("header name", err_name.lower())

        self.assertEqual(build_default_request(None)["url"], "")

        with patch("functions.api_tester.requests.get") as mock_get:
            res_hdr = send_api_request("GET", "https://api.example.test/v1", headers={"X-Bad": "a\nb"})
            self.assertFalse(res_hdr["ok"])
            self.assertEqual(res_hdr["reason"], "Invalid Header")

            for bad_timeout in (0, -3, True, "10"):
                res_to = send_api_request("GET", "https://api.example.test/v1", timeout=bad_timeout)
                self.assertFalse(res_to["ok"])
                self.assertEqual(res_to["reason"], "Invalid Timeout")

            mock_get.assert_not_called()

    def test_format_response_body_handles_json_raw_text_and_invalid_json(self):
        json_resp = make_mock_response(text='{"b":2,"a":1}')
        body, is_json, warning = format_response_body(json_resp)
        self.assertTrue(is_json)
        self.assertEqual(warning, "")
        self.assertIn('\n  "b": 2', body)

        txt_resp = make_mock_response(content_type="text/plain", text="plain output")
        body_txt, is_json_txt, warning_txt = format_response_body(txt_resp)
        self.assertFalse(is_json_txt)
        self.assertEqual(body_txt, "plain output")
        self.assertEqual(warning_txt, "")

        bad_json_resp = make_mock_response(content_type="application/json", text="{not json")
        body_bad, is_json_bad, warning_bad = format_response_body(bad_json_resp)
        self.assertFalse(is_json_bad)
        self.assertEqual(body_bad, "{not json")
        self.assertIn("not valid JSON", warning_bad)

    def test_send_get_request_succeeds_mocked(self):
        with patch("functions.api_tester.requests.get") as mock_get:
            mock_get.return_value = make_mock_response(200, "OK", text='{"ok": true}')
            res_helper = send_get_request(
                "https://api.example.test/v1",
                params={"q": "python"},
                headers={"Accept": "application/json"},
                timeout=10,
            )
            self.assertTrue(res_helper["ok"])
            self.assertEqual(res_helper["status_code"], 200)
            self.assertEqual(res_helper["method"], "GET")
            self.assertTrue(res_helper["is_json"])
            mock_get.assert_called_once_with(
                "https://api.example.test/v1",
                params={"q": "python"},
                headers={"Accept": "application/json"},
                timeout=10,
            )

            mock_get.reset_mock()
            mock_get.return_value = make_mock_response(200, "OK", text='{"items": [1, 2]}')
            res_direct = send_api_request("get", "https://api.example.test/items")
            self.assertTrue(res_direct["ok"])
            self.assertEqual(res_direct["method"], "GET")

    def test_rejects_unsupported_methods_without_network_calls(self):
        with patch("functions.api_tester.requests.get") as mock_get:
            for unsupported in ("POST", "PUT", "DELETE", "TRACE"):
                res = send_api_request(unsupported, "https://api.example.test/v1")
                self.assertFalse(res["ok"], f"Expected {unsupported} to be rejected")
                self.assertEqual(res["method"], unsupported)
                self.assertEqual(res["reason"], "Unsupported Method")
                self.assertIn("GET", res["error"])

            mock_get.assert_not_called()

    def test_send_api_request_never_logs_sensitive_headers_or_params(self):
        with patch("functions.api_tester.requests.get", return_value=make_mock_response(200, "OK", text="{}")), \
             self.assertLogs(LOGGER_NAME, level="INFO") as captured:
            res = send_api_request(
                "GET",
                "https://api.example.test/private?api_key=SECRET_KEY_123",
                headers={"Authorization": "Bearer TOP_SECRET_BEARER"},
            )

        self.assertTrue(res["ok"])
        combined = "\n".join(captured.output)
        self.assertNotIn("SECRET_KEY_123", combined)
        self.assertNotIn("TOP_SECRET_BEARER", combined)
        self.assertNotIn("api.example.test", combined)

    def test_send_api_request_network_and_http_errors_mocked(self):
        with patch("functions.api_tester.requests.get", side_effect=requests.exceptions.Timeout("timeout")):
            res_to = send_api_request("GET", "https://api.example.test/slow", timeout=5)
            self.assertFalse(res_to["ok"])
            self.assertEqual(res_to["reason"], "Timeout")
            self.assertIn("timed out after 5 seconds", res_to["error"])

        with patch("functions.api_tester.requests.get", side_effect=requests.exceptions.ConnectionError("refused")):
            res_conn = send_api_request("GET", "https://api.example.test/down")
            self.assertFalse(res_conn["ok"])
            self.assertEqual(res_conn["reason"], "Connection Error")

        with patch("functions.api_tester.requests.get", return_value=make_mock_response(404, "Not Found", text='{"error":"missing"}')):
            res_404 = send_api_request("GET", "https://api.example.test/missing")
            self.assertFalse(res_404["ok"])
            self.assertEqual(res_404["status_code"], 404)

        mock_429 = make_mock_response(429, "Too Many Requests", text='{"error":"slow down"}', headers={"Retry-After": "30"})
        with patch("functions.api_tester.requests.get", return_value=mock_429) as m_get:
            res_429 = send_api_request("GET", "https://api.example.test/limit")
            self.assertFalse(res_429["ok"])
            self.assertTrue(res_429["rate_limited"])
            self.assertIn("Retry after 30s", res_429["error"])
            self.assertEqual(m_get.call_count, 1)

    def test_format_response_body_truncates_oversized_responses(self):
        large_resp = make_mock_response(content_type="text/plain", text="A" * 500)
        body, is_json, warning = format_response_body(large_resp, max_chars=100)
        self.assertFalse(is_json)
        self.assertIn("Truncated", body)
        self.assertIn("truncated", warning.lower())

    def test_response_panel_states_copy_clear_and_clipboard_errors(self):
        ui_refs = {
            "send_btn": MagicMock(),
            "status_badge": MagicMock(),
            "time_label": MagicMock(),
            "format_label": MagicMock(),
            "error_label": MagicMock(),
            "response_box": MagicMock(),
            "status_label": MagicMock(),
        }
        state = {"method": "GET", "last_body": "", "last_result": None}

        update_response_card(
            {"ok": True, "method": "GET", "status_code": 200, "reason": "OK", "response_time_ms": 12.4, "is_json": False, "body": "", "error": "", "rate_limited": False},
            state,
            ui_refs,
        )
        self.assertEqual(ui_refs["format_label"].configure.call_args.kwargs["text"], "  Empty  ")
        ui_refs["error_label"].pack_forget.assert_called()
        self.assertFalse(handle_copy_response(state, ui_refs))

        update_response_card(
            {"ok": False, "method": "GET", "status_code": None, "reason": "Invalid URL", "response_time_ms": 0.0, "is_json": False, "body": "", "error": "Request URL cannot be empty.", "rate_limited": False},
            state,
            ui_refs,
        )
        self.assertEqual(ui_refs["time_label"].configure.call_args.kwargs["text"], "Time: —")
        self.assertEqual(ui_refs["status_badge"].configure.call_args.kwargs["text"], "  Invalid URL  ")
        ui_refs["error_label"].pack.assert_called()

        ui_refs["response_box"].winfo_toplevel.return_value.clipboard_clear.side_effect = tk.TclError("unavailable")
        state["last_body"] = '{"ok": true}'
        self.assertFalse(handle_copy_response(state, ui_refs))

        handle_clear_response(state, ui_refs)
        self.assertEqual(state["last_body"], "")
        self.assertEqual(ui_refs["status_badge"].configure.call_args.kwargs["text"], "  Ready  ")


if __name__ == "__main__":
    unittest.main()
