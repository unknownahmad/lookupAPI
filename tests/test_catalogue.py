# ==========================================
# FINAL CODE
# ==========================================

import inspect
import json
import logging
import os
import tempfile
import unittest

from functions.logger import LOGGER_NAME, configure_logger
from functions.models import APIResource, CatalogAPI
from functions.test_catalogue import (
    CATALOGUE_FILE,
    extract_attribution_info,
    extract_rate_limit_info,
    format_example_endpoint,
    group_apis_by_category,
    is_valid_catalogue_entry,
    iter_apis_by_category,
    iter_catalogue_apis,
    load_verified_free_apis,
)


class TestCatalogueFunctions(unittest.TestCase):
    """Unit tests for verified free API catalogue loading, generators, models, and helpers."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._log_file = os.path.join(self._tmpdir.name, "test_catalogue.log")
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

    def test_loads_verified_no_auth_catalogue(self):
        apis = load_verified_free_apis(CATALOGUE_FILE)
        self.assertEqual(len(apis), 15)
        for entry in apis:
            self.assertEqual(str(entry.get("authentication")).upper(), "NONE")

    def test_iter_catalogue_apis_yields_catalog_api_models(self):
        gen = iter_catalogue_apis(CATALOGUE_FILE)
        self.assertTrue(inspect.isgenerator(gen))

        models = list(gen)
        self.assertEqual(len(models), 15)
        for model in models:
            self.assertIsInstance(model, CatalogAPI)
            self.assertIsInstance(model, APIResource)
            self.assertTrue(model.has_valid_url())

    def test_iter_apis_by_category_generator_filters_models_and_dicts(self):
        models = list(iter_catalogue_apis(CATALOGUE_FILE))
        weather_gen = iter_apis_by_category(models, "weather")
        self.assertTrue(inspect.isgenerator(weather_gen))

        weather_apis = list(weather_gen)
        self.assertEqual(len(weather_apis), 2)
        for api in weather_apis:
            self.assertEqual(api.category, "Weather")

        all_apis = list(iter_apis_by_category(models, "All"))
        self.assertEqual(len(all_apis), 15)
        self.assertEqual(list(iter_apis_by_category(None, "Weather")), [])

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
        path = os.path.join(self._tmpdir.name, "cat.json")
        with open(path, "w", encoding="utf-8") as file:
            json.dump(sample, file)

        loaded = load_verified_free_apis(path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["api_name"], "Free Sample API")

    def test_handles_missing_and_invalid_json_catalogue(self):
        self.assertEqual(load_verified_free_apis(os.path.join(self._tmpdir.name, "missing.json")), [])

        bad_path = os.path.join(self._tmpdir.name, "bad.json")
        with open(bad_path, "w", encoding="utf-8") as file:
            file.write("{not valid json")
        self.assertEqual(load_verified_free_apis(bad_path), [])

    def test_groups_apis_alphabetically_and_sorts_entries_by_name(self):
        apis = [
            {"api_name": "Zeta Weather", "category": "Weather"},
            {"api_name": "Alpha Weather", "category": "Weather"},
            {"api_name": "Finance API", "category": "Finance"},
            {"api_name": "Uncategorized API", "category": ""},
        ]
        grouped = group_apis_by_category(apis)
        self.assertEqual(list(grouped.keys()), ["Finance", "Other", "Weather"])
        self.assertEqual(len(grouped["Other"]), 1)
        self.assertEqual([a["api_name"] for a in grouped["Weather"]], ["Alpha Weather", "Zeta Weather"])

    def test_formats_example_endpoint_with_and_without_params(self):
        with_params = {
            "working_get_endpoint": "/latest",
            "example_query_parameters": {"base": "EUR", "symbols": "USD"},
        }
        without_params = {"working_get_endpoint": "/metrics.json", "example_query_parameters": {}}
        model_entry = CatalogAPI.from_dict(
            {
                "api_name": "Model API",
                "base_url": "https://api.example.test",
                "working_get_endpoint": "/forecast",
                "example_query_parameters": {"lat": "52.5"},
                "authentication": "NONE",
            }
        )

        self.assertEqual(format_example_endpoint(with_params), "/latest?base=EUR&symbols=USD")
        self.assertEqual(format_example_endpoint(without_params), "/metrics.json")
        self.assertEqual(format_example_endpoint(model_entry), "/forecast?lat=52.5")

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

    def test_validates_required_fields_ports_and_deduplicates_entries(self):
        sample = {
            "apis": [
                {
                    "api_name": "Valid API",
                    "category": "Open Data",
                    "base_url": "https://api.example.test/v1",
                    "working_get_endpoint": "/items",
                    "authentication": "NONE",
                },
                {
                    "api_name": "Valid API",
                    "category": "Open Data",
                    "base_url": "https://api.example.test/v1/",
                    "working_get_endpoint": "/items",
                    "authentication": "NONE",
                },
                {
                    "api_name": "",
                    "base_url": "https://api.example.test",
                    "working_get_endpoint": "/missing-name",
                    "authentication": "NONE",
                },
                {
                    "api_name": "Bad Base URL API",
                    "base_url": "ftp://invalid.example.test",
                    "working_get_endpoint": "/items",
                    "authentication": "NONE",
                },
                {
                    "api_name": "Bad Port API",
                    "base_url": "https://api.example.test:70000",
                    "working_get_endpoint": "/items",
                    "authentication": "NONE",
                },
                {
                    "api_name": "Missing Endpoint API",
                    "base_url": "https://api.example.test",
                    "working_get_endpoint": "",
                    "authentication": "NONE",
                },
            ]
        }
        path = os.path.join(self._tmpdir.name, "validated.json")
        with open(path, "w", encoding="utf-8") as file:
            json.dump(sample, file)

        loaded = load_verified_free_apis(path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["api_name"], "Valid API")
        self.assertFalse(is_valid_catalogue_entry("bad"))

        valid_model = CatalogAPI(
            name="Valid Model",
            endpoint_url="https://api.example.test",
            sample_endpoint="/ping",
            auth="NONE",
        )
        self.assertTrue(is_valid_catalogue_entry(valid_model))

    def test_handles_malformed_helper_inputs_and_missing_endpoint(self):
        self.assertEqual(group_apis_by_category(None), {})
        self.assertEqual(group_apis_by_category(["not-a-dict", {"category": "Science"}]), {"Science": [{"category": "Science"}]})
        self.assertEqual(
            format_example_endpoint({"working_get_endpoint": "", "example_query_parameters": {"a": "1"}}),
            "Not available",
        )
        self.assertEqual(format_example_endpoint(None), "Not available")
        self.assertIn("official documentation", extract_attribution_info(None).lower())
        self.assertIn("fair-use", extract_rate_limit_info(None).lower())


if __name__ == "__main__":
    unittest.main()
