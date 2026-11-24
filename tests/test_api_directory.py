import unittest
from unittest.mock import MagicMock, patch

import requests

import functions.api_directory as api_directory


class TestAPIDirectory(unittest.TestCase):
    """Offline unit tests for APIs.guru discovery, search, and OpenAPI spec parsing."""

    def setUp(self):
        api_directory.cached_apis = None

    def tearDown(self):
        api_directory.cached_apis = None

    def test_get_api_directory_parses_and_caches_entries(self):
        payload = {
            "example.com": {
                "versions": {
                    "1.0": {
                        "info": {
                            "title": "Example Public API",
                            "version": "1.0",
                            "description": "Sample description",
                            "contact": {"url": "https://example.com/docs"},
                        },
                        "swaggerUrl": "https://example.com/openapi.json",
                    }
                }
            }
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = payload

        with patch("functions.api_directory.requests.get", return_value=mock_resp) as mock_get:
            first = api_directory.get_api_directory()
            second = api_directory.get_api_directory()

        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]["name"], "Example Public API")
        self.assertEqual(first[0]["provider"], "example.com")
        self.assertEqual(first[0]["documentation_url"], "https://example.com/docs")
        self.assertEqual(second, first)
        mock_get.assert_called_once()

    def test_get_api_directory_handles_network_error(self):
        with patch("functions.api_directory.requests.get", side_effect=requests.exceptions.Timeout("timed out")):
            result = api_directory.get_api_directory(force_refresh=True)
        self.assertEqual(result, [])

    def test_search_apis_filters_by_name_or_provider(self):
        sample = [
            {"name": "Weather Service", "provider": "open-meteo.com"},
            {"name": "GitHub REST", "provider": "github.com"},
        ]
        self.assertEqual(len(api_directory.search_apis("", sample)), 2)
        self.assertEqual(len(api_directory.search_apis("github", sample)), 1)
        self.assertEqual(len(api_directory.search_apis("meteo", sample)), 1)
        self.assertEqual(api_directory.search_apis("unknown", sample), [])

    def test_get_base_url_endpoints_and_api_details(self):
        spec = {
            "servers": [{"url": "https://api.example.test/v1"}],
            "externalDocs": {"url": "https://docs.example.test"},
            "info": {"title": "Spec Title", "version": "2.0", "description": "Full spec"},
            "paths": {
                "/items": {
                    "get": {"summary": "List items"},
                    "post": {"summary": "Create item"},
                    "parameters": [],
                }
            },
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = spec

        api_entry = {
            "name": "Fallback Name",
            "provider": "example.test",
            "specification_url": "https://example.test/spec.json",
        }
        with patch("functions.api_directory.requests.get", return_value=mock_resp):
            details = api_directory.get_api_details(api_entry)

        self.assertIsNotNone(details)
        self.assertEqual(details["name"], "Spec Title")
        self.assertEqual(details["base_url"], "https://api.example.test/v1")
        self.assertEqual(details["documentation_url"], "https://docs.example.test")
        self.assertEqual(len(details["endpoints"]), 2)
        self.assertIsNone(api_directory.get_api_details({"name": "Missing Spec"}))


if __name__ == "__main__":
    unittest.main()
