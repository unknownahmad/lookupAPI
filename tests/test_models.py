# ==========================================
# FINAL CODE
# ==========================================

import json
import unittest

from functions.api_tester import build_default_request
from functions.models import APIResource, CatalogAPI, SavedAPI
from functions.test_catalogue import CATALOGUE_FILE, is_valid_catalogue_entry


class TestAPIModels(unittest.TestCase):
    """Unit tests for APIResource, CatalogAPI, and SavedAPI models."""

    def test_inheritance_and_repr(self):
        base = APIResource(
            name="Example API",
            category="Open Data",
            endpoint_url="https://api.example.test/v1",
            description="Sample base resource.",
        )
        catalog = CatalogAPI(
            name="Weather API",
            category="Weather",
            endpoint_url="https://api.weather.example/v1",
            description="Forecast service.",
        )
        saved = SavedAPI(
            name="GitHub API",
            category="General",
            endpoint_url="https://api.github.com",
            api_id=16,
        )

        self.assertTrue(issubclass(CatalogAPI, APIResource))
        self.assertTrue(issubclass(SavedAPI, APIResource))
        self.assertIsInstance(base, APIResource)
        self.assertIsInstance(catalog, CatalogAPI)
        self.assertIsInstance(catalog, APIResource)
        self.assertIsInstance(saved, SavedAPI)
        self.assertIsInstance(saved, APIResource)
        self.assertNotIsInstance(catalog, SavedAPI)
        self.assertNotIsInstance(saved, CatalogAPI)

        self.assertIn("APIResource", repr(base))
        self.assertIn("Example API", repr(base))
        self.assertIn("CatalogAPI", repr(catalog))
        self.assertIn("SavedAPI", repr(saved))

    def test_url_validation_accepts_valid_and_rejects_malformed_urls(self):
        valid_urls = [
            "https://api.open-meteo.com/v1",
            "http://127.0.0.1:8000/items",
            "http://localhost:3000/health",
            "https://api.example.test:443/v2/items?limit=2#top",
            "HTTPS://API.EXAMPLE.TEST/v1",
            "https://api.example.test:65535/ok",
        ]
        for url in valid_urls:
            self.assertTrue(APIResource.validate_url(url), f"Expected valid URL: {url!r}")
            resource = APIResource(name="Valid", endpoint_url=url)
            self.assertTrue(resource.has_valid_url())

        invalid_urls = [
            "",
            "   ",
            None,
            "not-a-url",
            "ftp://example.test/file",
            "https://",
            "https://:8080/missing-host",
            "https://bad url.test/v1",
            "https://api.example.test:notaport/v1",
            "https://api.example.test:0/v1",
            "https://api.example.test:65536/v1",
            "https://api.example.test:70000/v1",
            "https://api.example.test:-1/v1",
            "https://api.example.test:/v1",
        ]
        for bad_url in invalid_urls:
            self.assertFalse(APIResource.validate_url(bad_url), f"Expected invalid URL: {bad_url!r}")
            resource = APIResource(name="Invalid", endpoint_url=bad_url or "")
            self.assertFalse(resource.has_valid_url())

    def test_catalog_api_round_trip(self):
        sample = {
            "name": "Demo Public API",
            "category": "Science",
            "endpoint_url": "https://api.science.test/v1",
            "description": "Returns scientific constants.",
            "https": True,
            "auth": "NONE",
            "cors": "yes",
            "sample_endpoint": "/constants",
            "docs_url": "https://docs.science.test",
            "status_code": 200,
            "provider": "Science Org",
            "example_query_parameters": {"limit": "2"},
            "free_access_evidence": "Public domain dataset.",
            "response_time_seconds": 0.25,
            "date_tested": "2026-11-22",
        }
        first = CatalogAPI.from_dict(sample)
        exported = first.to_dict()
        reloaded = CatalogAPI.from_dict(exported)

        self.assertEqual(reloaded.to_dict(), exported)
        self.assertEqual(reloaded.name, "Demo Public API")
        self.assertEqual(reloaded.endpoint_url, "https://api.science.test/v1")
        self.assertTrue(reloaded.https)
        self.assertEqual(reloaded.auth, "NONE")
        self.assertEqual(reloaded.cors, "yes")
        self.assertEqual(reloaded.sample_endpoint, "/constants")
        self.assertEqual(reloaded.docs_url, "https://docs.science.test")
        self.assertEqual(reloaded.status_code, 200)

    def test_catalog_api_compatibility_with_real_catalogue_entries(self):
        with open(CATALOGUE_FILE, "r", encoding="utf-8") as file:
            payload = json.load(file)

        raw_entries = payload["apis"]
        self.assertEqual(len(raw_entries), 15)

        for entry in raw_entries:
            model = CatalogAPI.from_dict(entry)
            self.assertIsInstance(model, APIResource)
            self.assertTrue(model.has_valid_url(), f"Invalid base_url in {model.name}")
            self.assertTrue(model.https)
            self.assertEqual(model.auth, "NONE")
            self.assertEqual(model.status_code, 200)
            self.assertEqual(model.name, entry["api_name"])
            self.assertEqual(model.endpoint_url, entry["base_url"])
            self.assertEqual(model.sample_endpoint, entry["working_get_endpoint"])
            self.assertEqual(model.docs_url, entry["documentation_url"])

            exported = model.to_dict()
            self.assertTrue(is_valid_catalogue_entry(exported))
            for original_key, original_val in entry.items():
                self.assertEqual(exported[original_key], original_val)

            req = build_default_request(exported)
            self.assertTrue(req["url"].startswith(entry["base_url"].rstrip("/")))

    def test_saved_api_mysql_and_discover_compatibility_and_round_trip(self):
        mysql_row = {
            "api_id": 16,
            "name": "GitHub v3 REST API",
            "category": "General",
            "description": "GitHub's v3 REST API.",
            "endpoint_url": "https://api.github.com",
            "documentation_url": "https://docs.github.com/rest",
            "http_method": "GET",
            "requires_auth": 0,
        }
        saved = SavedAPI.from_dict(mysql_row)
        exported = saved.to_dict()
        reloaded = SavedAPI.from_dict(exported)

        self.assertEqual(reloaded.to_dict(), exported)
        self.assertEqual(saved.api_id, 16)
        self.assertIsNone(saved.saved_at)
        self.assertIs(saved.requires_auth, False)
        self.assertTrue(saved.has_valid_url())

        required_db_fields = (
            "name",
            "category",
            "description",
            "endpoint_url",
            "documentation_url",
            "http_method",
            "requires_auth",
        )
        for field in required_db_fields:
            self.assertIn(field, exported)

        discover_dict = {
            "name": "ODWeather",
            "base_url": "https://api.oceandrivers.com/",
            "documentation_url": "https://api.oceandrivers.com/static/docs.html",
            "saved_at": "2026-11-24 09:00:00",
        }
        from_discover = SavedAPI.from_dict(discover_dict)
        self.assertEqual(from_discover.endpoint_url, "https://api.oceandrivers.com/")
        self.assertEqual(from_discover.category, "General")
        self.assertEqual(from_discover.description, "No description available")
        self.assertEqual(from_discover.http_method, "GET")
        self.assertIs(from_discover.requires_auth, False)
        self.assertIsNone(from_discover.api_id)
        self.assertEqual(from_discover.saved_at, "2026-11-24 09:00:00")

    def test_missing_optional_fields_defaults_and_invalid_inputs(self):
        minimal_base = APIResource(name="Minimal")
        self.assertEqual(minimal_base.category, "General")
        self.assertEqual(minimal_base.endpoint_url, "")
        self.assertEqual(minimal_base.description, "")
        self.assertFalse(minimal_base.has_valid_url())

        minimal_catalog = CatalogAPI.from_dict({"api_name": "Bare Catalogue API"})
        self.assertEqual(minimal_catalog.category, "Other")
        self.assertFalse(minimal_catalog.https)
        self.assertEqual(minimal_catalog.auth, "NONE")
        self.assertEqual(minimal_catalog.cors, "unknown")
        self.assertEqual(minimal_catalog.sample_endpoint, "")
        self.assertEqual(minimal_catalog.docs_url, "")
        self.assertIsNone(minimal_catalog.status_code)
        self.assertEqual(minimal_catalog.example_query_parameters, {})

        bad_numbers = CatalogAPI.from_dict(
            {"api_name": "Weird Numbers", "http_status": True, "response_time_seconds": "bad"}
        )
        self.assertIsNone(bad_numbers.status_code)
        self.assertIsNone(bad_numbers.response_time_seconds)

        minimal_saved = SavedAPI.from_dict({"name": "Bare Saved API", "api_id": True})
        self.assertEqual(minimal_saved.category, "General")
        self.assertEqual(minimal_saved.description, "No description available")
        self.assertEqual(minimal_saved.http_method, "GET")
        self.assertIs(minimal_saved.requires_auth, False)
        self.assertIsNone(minimal_saved.api_id)
        self.assertIsNone(minimal_saved.saved_at)

        with self.assertRaises(TypeError):
            CatalogAPI.from_dict("not-a-dict")
        with self.assertRaises(TypeError):
            SavedAPI.from_dict(None)


if __name__ == "__main__":
    unittest.main()
