import unittest

from functions.api_directory import search_apis
from functions.catalogue import format_example_endpoint
from functions.validators import is_valid_url


class TestCoreFunctions(unittest.TestCase):
    def test_is_valid_url(self):
        self.assertTrue(is_valid_url("https://api.open-meteo.com/v1/forecast"))
        self.assertFalse(is_valid_url("not-a-valid-url"))

    def test_format_example_endpoint(self):
        sample_api = {
            "working_get_endpoint": "/latest",
            "example_query_parameters": {"base": "EUR", "symbols": "USD"},
        }
        result = format_example_endpoint(sample_api)
        self.assertEqual(result, "/latest?base=EUR&symbols=USD")

    def test_search_apis(self):
        apis = [
            {"name": "Open-Meteo Weather API", "provider": "open-meteo.com"},
            {"name": "GitHub REST API", "provider": "github.com"},
        ]
        results = search_apis("github", apis)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "GitHub REST API")


if __name__ == "__main__":
    unittest.main()
