"""Hunter.io email finder implementation."""

import requests
from typing import Optional, Dict
from leadgen.utils.logging import logger
from leadgen.models.company import Company
from .base import BaseDomainFinder, DomainFinderError


class ApolloDomainFinder(BaseDomainFinder):
    """apollo.io domain discovery service."""

    BASE_URL = "https://api.apollo.io/api/v1/mixed_companies/search"

    def __init__(self, api_key):
        super().__init__(api_key=api_key)
        if not self.api_key:
            raise DomainFinderError("No Hunter.io API key provided")
        self.headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key,
            "accept": "application/json",
        }

    @property
    def name(self) -> str:
        return "hunter"

    def find(self, company: Company, proxy: Optional[Dict[str, str]] = None) -> str:
        """Find emails for a domain using Hunter.io API."""
        if not company.domain:
            logger.info(f"Company {company.name} has no domain, skipping")
            return None
        params = {"q_organization_name": company.domain}

        try:
            logger.info(f"Searching apllo.io for {company.name}")
            response = requests.post(
                self.BASE_URL,
                params=params,
                proxies=proxy,
                timeout=10,
                headers=self.headers,
            )

            response.raise_for_status()
            logger.info(f"Apollo.io returns {response} for email {company.domain}")
            data = response.json()

            # Extract emails from Hunter.io response
            email_data = data.get("data", {})
            emails = [
                email.get("value", "")
                for email in email_data.get("emails", [])
                if email.get("value")
            ]

            return emails

        except requests.HTTPError as e:
            error_msg = f"Apollo.io API error: {e}"
            return e
        except requests.RequestException as e:
            error_msg = f"Network error contacting apollo.io: {e}"
            return e
        except Exception as e:
            error_msg = f"Unexpected error in Apollo search: {e}"
            return e
