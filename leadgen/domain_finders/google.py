"""Google Places domain finder implementation."""

import json
import requests
from typing import Dict, Optional, Any
from leadgen.utils.logging import logger
from leadgen.models.company import Company
from leadgen.utils.proxy import CustomHttpError, ProxyError, ProxyManager
from .base import BaseDomainFinder, DomainFinderError


class GooglePlacesDomainFinder(BaseDomainFinder):
    """Google Places API domain discovery service."""

    DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

    @property
    def name(self) -> str:
        return "google_places_domain"

    def find(
        self, company: Company, proxy: Optional[Dict[str, str]] = None
    ) -> str | Dict[str, Any]:
        """
        Try to resolve a company's website/domain using Google Places API.
        Returns a string (domain) or dict with details.
        """

        params = {
            "place_id": company.id,  # Google Places ID (from search provider)
            "fields": "website,formatted_phone_number",
            "key": self.api_key,
        }

        try:
            response = ProxyManager().safe_request(
                "get", self.DETAILS_URL, params=params, proxies=proxy, timeout=10
            )

            if response is None:
                raise DomainFinderError("No response from Google Places API")

            if response.status_code != 200:
                raise DomainFinderError(
                    f"Google Places API request failed with status code {response.status_code}: {response.text}"
                )

            data = response.json()

            if "error_message" in data:
                error_msg = data.get("error_message", "Unknown error")
                logger.error(f"Google Places API error: {error_msg}")
                raise CustomHttpError(f"Google Places API error: {error_msg}")

            result = data.get("result", {})

            website = result.get("website", "")

            if not website:
                logger.warning(f"No website found for {company.name}")
                return domain

            # Extract just the domain from website
            domain = website.split("//")[-1].split("/")[0]

            return domain

        except ProxyError as e:
            raise DomainFinderError(f"Google Places proxy error: {e}")
        except requests.RequestException as e:
            if e.response is not None and e.response.status_code >= 400:
                try:
                    data = json.loads(e.response.content)
                    logger.error(
                        f"Google Places Domain Finder HTTP {e.response.status_code}: {data}"
                    )
                    raise CustomHttpError(
                        f"Google Places Domain Finder error {e.response.status_code}: {data.get('error_message', str(e))}"
                    )
                except ValueError:
                    raise CustomHttpError(
                        f"Google Places Domain Finder error {e.response.status_code}: {e.response.text}"
                    )
            raise DomainFinderError(f"Network error contacting Google Places: {e}")
        except Exception as e:
            raise DomainFinderError(
                f"Unexpected error in Google Places domain finder: {e}"
            )
