# ==========================================
# FINAL CODE
# ==========================================

import json
import os
import tempfile
import unittest

from functions.test_catalogue import (
    CATALOGUE_FILE,
    extract_attribution_info,
    extract_rate_limit_info,
    format_example_endpoint,
    group_apis_by_category,
    load_verified_free_apis,
)


class TestCatalogueFunctions(unittest.TestCase):
    """Unit tests for verified free API catalogue loading and metadata helpers."""

    def test_loads_verified_no_auth_catalogue(self):
        apis = load_verified_free_apis(CATALOGUE_FILE)
        self.assertEqual(len(apis), 15)
        for entry in apis:
            self.assertEqual(str(entry.get("authentication")).upper(), "NONE")

    def test_filters_out_authenticated_and_non_dict_entries(self):
        sample = {
            "apis": [
                {
                    "api_name": "Free Sample API",
                    "category": "Open Data",
                    "base_url": "https://api.example.test",
                    "working_get_endpoint": "/v1/items",
                    "authentication": "NONE",
                },
                {
                    "api_name": "Keyed API",
                    "category": "Finance",
                    "base_url": "https://keyed.example.test",
                    "working_get_endpoint": "/v1/rates",
                    "authentication": "API_KEY",
                },
                "not-a-dict",
            ]
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "cat.json")
            with open(path, "w", encoding="utf-8") as file:
                json.dump(sample, file)

            loaded = load_verified_free_apis(path)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["api_name"], "Free Sample API")

    def test_handles_missing_and_invalid_json_catalogue(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertEqual(load_verified_free_apis(os.path.join(tmpdir, "missing.json")), [])

            bad_path = os.path.join(tmpdir, "bad.json")
            with open(bad_path, "w", encoding="utf-8") as file:
                file.write("{not valid json")
            self.assertEqual(load_verified_free_apis(bad_path), [])

    def test_groups_apis_alphabetically_with_default_category(self):
        apis = [
            {"api_name": "Weather API", "category": "Weather"},
            {"api_name": "Finance API", "category": "Finance"},
            {"api_name": "Uncategorized API", "category": ""},
        ]
        grouped = group_apis_by_category(apis)
        self.assertEqual(list(grouped.keys()), ["Finance", "Other", "Weather"])
        self.assertEqual(len(grouped["Other"]), 1)

    def test_formats_example_endpoint_with_and_without_params(self):
        with_params = {
            "working_get_endpoint": "/latest",
            "example_query_parameters": {"base": "EUR", "symbols": "USD"},
        }
        without_params = {"working_get_endpoint": "/metrics.json", "example_query_parameters": {}}

        self.assertEqual(format_example_endpoint(with_params), "/latest?base=EUR&symbols=USD")
        self.assertEqual(format_example_endpoint(without_params), "/metrics.json")

    def test_extracts_attribution_and_rate_limit_notes(self):
        entry = {
            "free_access_evidence": (
                "Official docs confirm free non-commercial access up to 10,000 calls/day "
                "under CC BY 4.0 license with a descriptive User-Agent header."
            )
        }
        attribution = extract_attribution_info(entry)
        rate_limits = extract_rate_limit_info(entry)

        self.assertIn("CC BY 4.0", attribution)
        self.assertIn("10,000 calls/day", rate_limits)
        self.assertIn("User-Agent", rate_limits)


if __name__ == "__main__":
    unittest.main()
