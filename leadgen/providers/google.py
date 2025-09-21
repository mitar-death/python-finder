"""Google Places business search provider implementation."""

import json
from typing import List, Optional, Dict
import requests
from leadgen.utils.logging import logger
from leadgen.models.company import Company
from leadgen.utils.proxy import CustomHttpError, ProxyError, ProxyManager
from .base import BaseProvider, ProviderError


class GooglePlacesProvider(BaseProvider):
    """Google Places API business search provider."""

    BASE_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    def __init__(self, api_key: str, config: Optional[Dict] = None):
        super().__init__(api_key, config)
        self.config = config or {}

    @property
    def name(self) -> str:
        return "google_places"

    def search(
        self, query: str, proxy: Optional[Dict[str, str]] = None
    ) -> List[Company]:
        """Search for businesses using Google Places Text Search API."""

        params = {
            "query": query,
            "key": self.api_key,
        }

        try:
            response = ProxyManager().safe_request(
                "get", self.BASE_URL, params=params, proxies=proxy, timeout=10
            )

            if response is None:
                raise ProviderError("No response from Google Places API")

            if response.status_code != 200:
                raise ProviderError(
                    f"Google Places API request failed with status code "
                    f"{response.status_code}: {response.text}"
                )

            data = response.json()

            if "error_message" in data:
                logger.error(f"Google Places API error: {data['error_message']}")
                raise CustomHttpError(
                    f"Google Places API error: {data['error_message']}"
                )

            results = data.get("results", [])
            companies: List[Company] = []

            for place in results:
                place_id = place.get("place_id")
                name = place.get("name", "")
                address = place.get("formatted_address", "")
                url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

                company = Company(id=place_id, name=name, url=url, address=address)
                companies.append(company)

            return companies

        except ProxyError as e:
            raise ProviderError(f"Google Places proxy error: {e}") from e
        except requests.RequestException as e:
            if e.response is not None and e.response.status_code >= 400:
                try:
                    data = json.loads(e.response.content)
                    logger.error(
                        f"Google Places API HTTP {e.response.status_code}: {data}"
                    )
                    raise CustomHttpError(
                        f"Google Places API error {e.response.status_code}: "
                        f"{data.get('error_message', str(e))}"
                    ) from e
                except ValueError:
                    raise CustomHttpError(
                        f"Google Places API error {e.response.status_code}: {e.response.text}"
                    ) from e
            raise ProviderError(f"Network error contacting Google Places: {e}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected error in Google Places search: {e}") from e
