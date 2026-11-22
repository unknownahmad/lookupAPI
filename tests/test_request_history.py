# ==========================================
# FINAL CODE
# ==========================================

import json
import os
import tempfile
import unittest
from urllib.parse import parse_qsl, urlsplit

from functions.request_history import (
    HISTORY_FILE,
    MASK_VALUE,
    build_history_entry,
    load_request_history,
    mask_sensitive_query_params,
    save_request_history,
)
from ui.request_history_panel import format_history_status


class TestRequestHistoryMasking(unittest.TestCase):
    """Verify sensitive query parameters are masked before writing request history."""

    def test_masks_all_sensitive_params_and_preserves_ordinary_params(self):
        raw_url = (
            "https://api.example.test/v1/items"
            "?base=EUR&limit=5"
            "&api_key=sk_live_111"
            "&APIKEY=key_222"
            "&token=tok_333"
            "&access_token=acc_444"
            "&password=pwd_555"
            "&secret=sec_666"
            "&Authorization=Bearer_777"
        )
        sanitized = mask_sensitive_query_params(raw_url)
        params = dict(parse_qsl(urlsplit(sanitized).query))

        self.assertEqual(params["base"], "EUR")
        self.assertEqual(params["limit"], "5")

        for key in ("api_key", "APIKEY", "token", "access_token", "password", "secret", "Authorization"):
            self.assertEqual(params[key], MASK_VALUE)

        for secret_val in ("sk_live_111", "key_222", "tok_333", "acc_444", "pwd_555", "sec_666", "Bearer_777"):
            self.assertNotIn(secret_val, sanitized)

    def test_preserves_ordinary_url_unchanged(self):
        ordinary_url = "https://api.frankfurter.dev/v1/latest?base=EUR&symbols=USD,GBP"
        self.assertEqual(mask_sensitive_query_params(ordinary_url), ordinary_url)

        no_query_url = "https://api.weather.gov/points/38.8894,-77.0352"
        self.assertEqual(mask_sensitive_query_params(no_query_url), no_query_url)

    def test_sensitive_values_never_written_to_default_history_file(self):
        had_original = os.path.exists(HISTORY_FILE)
        original_content = None
        if had_original:
            with open(HISTORY_FILE, "r", encoding="utf-8") as file:
                original_content = file.read()

        sensitive_url = (
            "https://api.example.test/v1/search"
            "?q=python&api_key=MY_SUPER_SECRET_KEY&token=PRIVATE_TOKEN_999&password=TOP_SECRET_PWD"
        )
        try:
            saved = save_request_history(
                "Sanitization Test API",
                "GET",
                sensitive_url,
                {"ok": True, "status_code": 200, "response_time_ms": 42.5, "method": "GET"},
                file_path=HISTORY_FILE,
            )
            self.assertIsNotNone(saved)

            with open(HISTORY_FILE, "r", encoding="utf-8") as file:
                raw_disk_text = file.read()
            self.assertNotIn("MY_SUPER_SECRET_KEY", raw_disk_text)
            self.assertNotIn("PRIVATE_TOKEN_999", raw_disk_text)
            self.assertNotIn("TOP_SECRET_PWD", raw_disk_text)

            loaded = load_request_history(HISTORY_FILE)
            latest = loaded[-1]
            self.assertEqual(
                set(latest.keys()),
                {"api_name", "method", "url", "timestamp", "status_code", "response_time_ms", "success"},
            )
            latest_params = dict(parse_qsl(urlsplit(latest["url"]).query))
            self.assertEqual(latest_params["q"], "python")
            self.assertEqual(latest_params["api_key"], MASK_VALUE)
            self.assertEqual(latest_params["token"], MASK_VALUE)
            self.assertEqual(latest_params["password"], MASK_VALUE)
        finally:
            if had_original:
                with open(HISTORY_FILE, "w", encoding="utf-8") as file:
                    file.write(original_content)
            elif os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)

    def test_handles_missing_empty_and_malformed_history_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertEqual(load_request_history(os.path.join(tmpdir, "missing.json")), [])

            empty_file = os.path.join(tmpdir, "empty.json")
            with open(empty_file, "w", encoding="utf-8") as file:
                file.write("")
            self.assertEqual(load_request_history(empty_file), [])

            malformed_file = os.path.join(tmpdir, "malformed.json")
            with open(malformed_file, "w", encoding="utf-8") as file:
                file.write("{invalid json")
            self.assertEqual(load_request_history(malformed_file), [])

            mixed_file = os.path.join(tmpdir, "mixed.json")
            with open(mixed_file, "w", encoding="utf-8") as file:
                json.dump([{}, "not-a-dict", {"api_name": "Valid", "url": "https://api.example.test"}], file)
            loaded_mixed = load_request_history(mixed_file)
            self.assertEqual(len(loaded_mixed), 1)
            self.assertEqual(loaded_mixed[0]["api_name"], "Valid")

    def test_masks_hyphenated_sensitive_params_and_validates_types(self):
        url = "https://api.example.test/v1?page=1&api-key=abc123&access-token=tok999&client-secret=sec888"
        sanitized = mask_sensitive_query_params(url)
        params = dict(parse_qsl(urlsplit(sanitized).query))
        self.assertEqual(params["page"], "1")
        self.assertEqual(params["api-key"], MASK_VALUE)
        self.assertEqual(params["access-token"], MASK_VALUE)
        self.assertEqual(params["client-secret"], MASK_VALUE)

        entry = build_history_entry(
            "Type Test",
            "get",
            "https://api.example.test/v1",
            {"ok": True, "status_code": True, "response_time_ms": False},
        )
        self.assertIsNone(entry["status_code"])
        self.assertIsNone(entry["response_time_ms"])
        self.assertEqual(format_history_status({"status_code": True, "success": True})[0], "  Failed  ")
        self.assertEqual(format_history_status({"status_code": 429, "success": False})[0], "  HTTP 429  ")

    def test_history_enforces_max_entries_and_leaves_no_temp_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist_path = os.path.join(tmpdir, "bounded.json")
            for idx in range(5):
                save_request_history(
                    f"API {idx}",
                    "GET",
                    f"https://api.example.test/{idx}",
                    {"ok": True, "status_code": 200, "response_time_ms": float(idx + 10)},
                    file_path=hist_path,
                    max_entries=3,
                )

            loaded = load_request_history(hist_path)
            self.assertEqual([e["api_name"] for e in loaded], ["API 2", "API 3", "API 4"])
            self.assertEqual(os.listdir(tmpdir), ["bounded.json"])


if __name__ == "__main__":
    unittest.main()
