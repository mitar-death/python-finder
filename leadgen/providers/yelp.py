"""Yelp search provider implementation."""

from typing import List, Optional, Dict
import requests
from leadgen.utils.proxy import CustomHttpError, ProxyManager
from .base import BaseProvider, ProviderError
from ..models.company import Company
from ..utils.domain import DomainResolver
from ..utils.logging import logger


class YelpProvider(BaseProvider):
    """Yelp business search provider."""

    BASE_URL = "https://api.yelp.com/v3/businesses/search"

    def __init__(self, api_key: str, config: Optional[Dict] = None):
        super().__init__(api_key, config)
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.domain_resolver = DomainResolver()
        self.config = config or {}

    @property
    def name(self) -> str:
        return "yelp"

    def search(
        self, query: str, proxy: Optional[Dict[str, str]] = None
    ) -> List[Company]:
        """Search for businesses using Yelp API."""
        params = {
            "term": query,
            "location": self.config.get("location", "United States"),
            "limit": self.config.get("limit", 5),
            "is_claimed": True,
        }

        try:
            response = ProxyManager().safe_request(
                "get",
                self.BASE_URL,
                headers=self.headers,
                params=params,
                proxies=proxy,
                timeout=10,
            )

            # if response.status_code != 200:
            #     raise ProviderError(
            #         f"Yelp API request failed with status code {response.status_code}: "
            #         f"{response.text}")

            data = response.json()
            businesses = data.get("businesses", [])

            companies = []
            for business in businesses:
                id = business.get("id", "")
                name = business.get("name", "")
                yelp_url = business.get("url", "")
                address = ", ".join(
                    business.get("location", {}).get("display_address", [])
                )

                company = Company(
                    id=id,
                    name=name,
                    url=yelp_url,  # Keep Yelp URL for reference
                    address=address,
                    phone=business.get("phone", ""),
                )

                companies.append(company)
            return companies

        except requests.RequestException as e:
            # Don't disable proxy for HTTP errors - these are server-side issues
            if e.response is not None and e.response.status_code >= 400:
                logger.debug(
                    f"Response content : {e.response.content} on code {e.response.status_code}"
                )

                try:
                    error_data = e.response.json().get("error", {})
                    code = error_data.get("code", "UNKNOWN_ERROR")
                    desc = error_data.get("description", "No description provided")
                    field = error_data.get("field", "N/A")
                    logger.error(f"HTTP 400: {code} - {desc} (field: {field})")
                    raise CustomHttpError(
                        f"API validation error: {desc} (field: {field})"
                    ) from e
                except ValueError:
                    # Response wasn't JSON
                    logger.error(f"HTTP 400 Bad Request: {e.response.text}")
                    raise CustomHttpError(
                        f"Bad Request (400): {e.response.text}"
                    ) from e
            raise e from e
        except Exception as e:
            raise ProviderError(f"Unexpected error in Yelp search: {e}") from e
