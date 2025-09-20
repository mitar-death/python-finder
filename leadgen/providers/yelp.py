"""Yelp search provider implementation."""
import requests
from typing import List, Optional, Dict
from leadgen.utils.proxy import ProxyManager
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

    def search(self,
               query: str,
               proxy: Optional[Dict[str, str]] = None) -> List[Company]:
        """Search for businesses using Yelp API."""
        params = {
            "term": query,
            "location": self.config.get("location", "United States"),
            "limit": self.config.get("limit", 5),
            "is_claimed": True,
        }

        try:
            response = ProxyManager().safe_request("get", self.BASE_URL,
                                    headers=self.headers,
                                    params=params,
                                    proxies=proxy,
                                    timeout=10)

            if response.status_code != 200:
                raise ProviderError(
                    f"Yelp API request failed with status code {response.status_code}: "
                    f"{response.text}")

            data = response.json()
            businesses = data.get("businesses", [])

            companies = []
            for business in businesses:
                id = business.get("id", "")
                name = business.get("name", "")
                yelp_url = business.get("url", "")
                address = ", ".join(
                    business.get("location", {}).get("display_address", []))

                
                company = Company(
                    id=id,
                    name=name,
                    url=yelp_url,  # Keep Yelp URL for reference
                    address=address,
                    phone=business.get("phone", ""))
                
                
                # # Try to resolve the actual business website domain
                # business_domain = None
                # if yelp_url and name:
                #     business_domain = self.domain_resolver.extract_business_domain(company)

                # # Only set domain if we found a valid business domain (not provider domain)
                # valid_domain = None
                # if business_domain and self.domain_resolver._is_valid_business_domain(
                #         business_domain):
                #     valid_domain = business_domain
                #     logger.info(f"Found valid domain: {valid_domain} with id {id}")
                    
                # # set valid domain
                # company.domain = valid_domain
                companies.append(company)
            return companies

        except requests.RequestException as e:
            raise ProviderError(f"Network error while searching Yelp: {e}")
        except Exception as e:
            raise ProviderError(f"Unexpected error in Yelp search: {e}")
