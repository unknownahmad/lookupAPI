from functions.utils import parse_optional_float, parse_optional_int
from functions.validators import URL_REGEX, is_valid_url


class APIResource:
    """Base model representing a web API resource with shared fields and URL validation."""

    URL_REGEX = URL_REGEX

    def __init__(self, name, category="General", endpoint_url="", description=""):
        self.name = str(name or "").strip()
        self.category = str(category or "General").strip() or "General"
        self.endpoint_url = str(endpoint_url or "").strip()
        self.description = str(description or "").strip()

    @staticmethod
    def validate_url(url):
        """Validate an http(s) URL using regex and urllib.parse port range checks."""
        return is_valid_url(url)

    def has_valid_url(self):
        """Return True when endpoint_url is a valid http(s) URL."""
        return self.validate_url(self.endpoint_url)

    def to_dict(self):
        """Return the base API fields as a dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "endpoint_url": self.endpoint_url,
            "description": self.description,
        }

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, category={self.category!r}, "
            f"endpoint_url={self.endpoint_url!r})"
        )


class CatalogAPI(APIResource):
    """Verified public catalogue API model compatible with data/verified_free_apis.json."""

    def __init__(
        self,
        name,
        category="Other",
        endpoint_url="",
        description="",
        https=None,
        auth="NONE",
        cors="unknown",
        sample_endpoint="",
        docs_url="",
        status_code=None,
        provider="",
        example_query_parameters=None,
        free_access_evidence="",
        response_time_seconds=None,
        date_tested="",
        example_json_response=None,
    ):
        super().__init__(
            name=name,
            category=category or "Other",
            endpoint_url=endpoint_url,
            description=description,
        )
        self.https = self.endpoint_url.lower().startswith("https://") if https is None else bool(https)
        self.auth = str(auth if auth is not None else "NONE").strip()
        self.cors = str(cors or "unknown").strip() or "unknown"
        self.sample_endpoint = str(sample_endpoint or "").strip()
        self.docs_url = str(docs_url or "").strip()
        self.status_code = parse_optional_int(status_code)
        self.provider = str(provider or "").strip()
        self.example_query_parameters = {}
        if isinstance(example_query_parameters, dict):
            for key, value in example_query_parameters.items():
                clean_key = str(key or "").strip()
                if clean_key:
                    self.example_query_parameters[clean_key] = str(value)
        self.free_access_evidence = str(free_access_evidence or "").strip()
        self.response_time_seconds = parse_optional_float(response_time_seconds)
        self.date_tested = str(date_tested or "").strip()
        self.example_json_response = example_json_response

    @classmethod
    def from_dict(cls, data):
        """Create a CatalogAPI from either a verified_free_apis.json entry or a model dict."""
        if not isinstance(data, dict):
            raise TypeError("CatalogAPI data must be a dictionary.")

        if "authentication" in data:
            auth = str(data.get("authentication") or "").strip()
        elif "auth" in data:
            auth = str(data.get("auth") or "").strip()
        else:
            auth = "NONE"

        status_val = data.get("http_status")
        if status_val is None:
            status_val = data.get("status_code")

        return cls(
            name=data.get("api_name") or data.get("name") or "",
            category=data.get("category") or "Other",
            endpoint_url=data.get("base_url") or data.get("endpoint_url") or "",
            description=data.get("description") or "",
            https=data.get("https"),
            auth=auth,
            cors=data.get("cors") or "unknown",
            sample_endpoint=data.get("working_get_endpoint") or data.get("sample_endpoint") or "",
            docs_url=data.get("documentation_url") or data.get("docs_url") or "",
            status_code=status_val,
            provider=data.get("provider") or "",
            example_query_parameters=data.get("example_query_parameters"),
            free_access_evidence=data.get("free_access_evidence") or "",
            response_time_seconds=data.get("response_time_seconds"),
            date_tested=data.get("date_tested") or "",
            example_json_response=data.get("example_json_response"),
        )

    def to_dict(self):
        """Return a dictionary compatible with APIResource and verified_free_apis.json."""
        data = super().to_dict()
        data.update(
            {
                "https": self.https,
                "auth": self.auth,
                "cors": self.cors,
                "sample_endpoint": self.sample_endpoint,
                "docs_url": self.docs_url,
                "status_code": self.status_code,
                "api_name": self.name,
                "provider": self.provider,
                "base_url": self.endpoint_url,
                "working_get_endpoint": self.sample_endpoint,
                "example_query_parameters": dict(self.example_query_parameters),
                "documentation_url": self.docs_url,
                "authentication": self.auth,
                "free_access_evidence": self.free_access_evidence,
                "http_status": self.status_code,
                "response_time_seconds": self.response_time_seconds,
                "date_tested": self.date_tested,
            }
        )
        if self.example_json_response is not None:
            data["example_json_response"] = self.example_json_response
        return data


class SavedAPI(APIResource):
    """Saved API model compatible with MySQL apis table rows and UI dictionaries."""

    def __init__(
        self,
        name,
        category="General",
        endpoint_url="",
        description="No description available",
        api_id=None,
        saved_at=None,
        documentation_url="",
        http_method="GET",
        requires_auth=False,
    ):
        super().__init__(
            name=name,
            category=category or "General",
            endpoint_url=endpoint_url,
            description=description or "No description available",
        )
        self.api_id = parse_optional_int(api_id)
        cleaned_saved_at = str(saved_at).strip() if saved_at is not None else ""
        self.saved_at = cleaned_saved_at or None
        self.documentation_url = str(documentation_url or "").strip()
        self.http_method = str(http_method or "GET").strip().upper() or "GET"
        self.requires_auth = bool(requires_auth)

    @classmethod
    def from_dict(cls, data):
        """Create a SavedAPI from a MySQL row dict or a Discover/saved API dictionary."""
        if not isinstance(data, dict):
            raise TypeError("SavedAPI data must be a dictionary.")

        return cls(
            name=data.get("name") or data.get("api_name") or "",
            category=data.get("category") or "General",
            endpoint_url=data.get("endpoint_url") or data.get("base_url") or "",
            description=data.get("description") or "No description available",
            api_id=data.get("api_id"),
            saved_at=data.get("saved_at"),
            documentation_url=data.get("documentation_url") or data.get("docs_url") or "",
            http_method=data.get("http_method") or "GET",
            requires_auth=data.get("requires_auth", False),
        )

    def to_dict(self):
        """Return a dictionary compatible with MySQL CRUD helpers and UI views."""
        data = super().to_dict()
        data.update(
            {
                "api_id": self.api_id,
                "saved_at": self.saved_at,
                "documentation_url": self.documentation_url,
                "http_method": self.http_method,
                "requires_auth": self.requires_auth,
            }
        )
        return data
