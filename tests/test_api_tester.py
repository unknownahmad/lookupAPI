# ==========================================
# FINAL CODE
# ==========================================

import unittest
from unittest.mock import MagicMock, patch

import requests

from functions.api_tester import (
    DEFAULT_USER_AGENT,
    build_default_request,
    format_response_body,
    send_api_request,
    send_get_request,
    validate_json_body,
    validate_request_headers,
    validate_request_url,
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
    """Offline unit tests for HTTP request building, validation, formatting, and error handling."""

    def test_build_default_request_populates_url_params_and_headers(self):
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
        self.assertNotIn("@", DEFAULT_USER_AGENT)

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
        ):
            valid, message = validate_request_url(bad_url)
            self.assertFalse(valid, f"Expected invalid URL: {bad_url!r}")
            self.assertTrue(bool(message))

    def test_rejects_invalid_headers_and_timeouts_without_network_calls(self):
        ok_hdr, clean_hdr, err_hdr = validate_request_headers({"Accept": "application/json", " ": "ignored"})
        self.assertTrue(ok_hdr)
        self.assertEqual(clean_hdr, {"Accept": "application/json"})
        self.assertEqual(err_hdr, "")

        bad_hdr_ok, _, bad_hdr_err = validate_request_headers({"X-Test": "value\r\nInjected: bad"})
        self.assertFalse(bad_hdr_ok)
        self.assertIn("newline", bad_hdr_err.lower())

        self.assertEqual(build_default_request(None)["url"], "")

        with patch("functions.api_tester.requests.request") as mock_req:
            res_hdr = send_api_request("GET", "https://api.example.test/v1", headers={"X-Bad": "a\nb"})
            self.assertFalse(res_hdr["ok"])
            self.assertEqual(res_hdr["reason"], "Invalid Header")

            for bad_timeout in (0, -3, True, "10"):
                res_to = send_api_request("GET", "https://api.example.test/v1", timeout=bad_timeout)
                self.assertFalse(res_to["ok"])
                self.assertEqual(res_to["reason"], "Invalid Timeout")

            mock_req.assert_not_called()

    def test_validate_json_body_handles_empty_valid_and_invalid_json(self):
        self.assertEqual(validate_json_body(None), (True, None, ""))
        self.assertEqual(validate_json_body("   "), (True, None, ""))

        ok, parsed, err = validate_json_body('{"name": "LOOKUPAPI", "count": 3}')
        self.assertTrue(ok)
        self.assertEqual(parsed, {"name": "LOOKUPAPI", "count": 3})
        self.assertEqual(err, "")

        ok_bad, parsed_bad, err_bad = validate_json_body('{"broken": [1, 2')
        self.assertFalse(ok_bad)
        self.assertIsNone(parsed_bad)
        self.assertIn("Invalid JSON body", err_bad)

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

    def test_send_api_request_methods_and_validation_mocked(self):
        with patch("functions.api_tester.requests.request") as mock_req:
            mock_req.return_value = make_mock_response(200, "OK", text='{"ok": true}')
            res_get = send_get_request("https://api.example.test/v1", params={"q": "test"})
            self.assertTrue(res_get["ok"])
            self.assertEqual(res_get["status_code"], 200)
            self.assertEqual(res_get["method"], "GET")

            mock_req.return_value = make_mock_response(201, "Created", text='{"id": 1}')
            res_post = send_api_request("POST", "https://api.example.test/items", json_body='{"name": "a"}')
            self.assertTrue(res_post["ok"])
            self.assertEqual(res_post["status_code"], 201)
            self.assertEqual(mock_req.call_args.kwargs["json"], {"name": "a"})

            mock_req.return_value = make_mock_response(200, "OK", text='{"updated": true}')
            res_put = send_api_request("PUT", "https://api.example.test/items/1", json_body='{"name": "b"}')
            self.assertTrue(res_put["ok"])
            self.assertEqual(mock_req.call_args.kwargs["json"], {"name": "b"})

            mock_req.return_value = make_mock_response(204, "No Content", content_type="", text="")
            res_del = send_api_request("DELETE", "https://api.example.test/items/1")
            self.assertTrue(res_del["ok"])
            self.assertEqual(res_del["status_code"], 204)
            self.assertIsNone(mock_req.call_args.kwargs["json"])

            mock_req.reset_mock()
            res_bad_method = send_api_request("TRACE", "https://api.example.test/v1")
            self.assertFalse(res_bad_method["ok"])
            self.assertEqual(res_bad_method["reason"], "Unsupported Method")

            res_bad_json = send_api_request("POST", "https://api.example.test/items", json_body="{bad")
            self.assertFalse(res_bad_json["ok"])
            self.assertEqual(res_bad_json["reason"], "Invalid JSON")
            mock_req.assert_not_called()

    def test_send_api_request_network_and_http_errors_mocked(self):
        with patch("functions.api_tester.requests.request", side_effect=requests.exceptions.Timeout("timeout")):
            res_to = send_api_request("GET", "https://api.example.test/slow", timeout=5)
            self.assertFalse(res_to["ok"])
            self.assertEqual(res_to["reason"], "Timeout")
            self.assertIn("timed out after 5 seconds", res_to["error"])

        with patch("functions.api_tester.requests.request", side_effect=requests.exceptions.ConnectionError("refused")):
            res_conn = send_api_request("GET", "https://api.example.test/down")
            self.assertFalse(res_conn["ok"])
            self.assertEqual(res_conn["reason"], "Connection Error")

        with patch("functions.api_tester.requests.request", return_value=make_mock_response(404, "Not Found", text='{"error":"missing"}')):
            res_404 = send_api_request("GET", "https://api.example.test/missing")
            self.assertFalse(res_404["ok"])
            self.assertEqual(res_404["status_code"], 404)

        mock_429 = make_mock_response(429, "Too Many Requests", text='{"error":"slow down"}', headers={"Retry-After": "30"})
        with patch("functions.api_tester.requests.request", return_value=mock_429) as m_req:
            res_429 = send_api_request("GET", "https://api.example.test/limit")
            self.assertFalse(res_429["ok"])
            self.assertTrue(res_429["rate_limited"])
            self.assertIn("Retry after 30s", res_429["error"])
            self.assertEqual(m_req.call_count, 1)


if __name__ == "__main__":
    unittest.main()
