"""Hunter.io email finder implementation."""

import json
import requests
from typing import List, Dict, Optional, Any
from leadgen.utils.logging import logger
from leadgen.models.company import Company
from leadgen.models.email_result import Contact
from leadgen.utils.proxy import CustomHttpError, ProxyError, ProxyManager
from leadgen.config.loader import ConfigLoader
from leadgen.config.models import AppConfig
from .base import BaseDomainFinder, DomainFinderError


class HunterDomainFinder(BaseDomainFinder):
    """Hunter.io domain discovery service."""

    BASE_URL = "https://api.hunter.io/v2/domain-search"

    @property
    def name(self) -> str:
        return "hunter"

    def find(
        self, company: Company, proxy: Optional[Dict[str, str]] = None
    ) -> str | Dict[str, Any]:
        """Find emails for a company using Hunter.io API.
        Returns
            can be str or contacts
        """
        config: AppConfig = ConfigLoader().load_config()
        params = {
            "company": company.name,
            "api_key": self.api_key,
            "department": config.hunter_department or "executive",
            "limit": config.email_finder_limit or 10,
        }

        try:
            response = ProxyManager().safe_request(
                "get", self.BASE_URL, params=params, proxies=proxy, timeout=10
            )

            if response.status_code == 429:
                logger.debug(f"Hunter.io API rate limit exceeded")
                raise DomainFinderError("Hunter.io API rate limit exceeded")
            if response is None:
                raise DomainFinderError("No response from Hunter.io")

            data = response.json()

            # Debug logging for problematic responses
            logger.debug(f"Hunter domain finder response for {company.name}: {data}")

            # Extract emails from Hunter.io response
            return data

        except ProxyError as e:
            logger.debug("Hunter Proxy Execption called")
            raise DomainFinderError(f"Hunter.io proxy error: {e}")
        except requests.RequestException as e:
            logger.debug("Hunter Request Execption called")
            if e.response is not None and e.response.status_code >= 400:
                logger.debug(
                    f"Response content : {json.loads(e.response.content)} on code {e.response.status_code}"
                )

                try:
                    data = json.loads(e.response.content)
                    if "errors" in data and len(data["errors"]) > 0:
                        error = data["errors"][0]  # Take the first error
                        error_id = error.get("id", "UNKNOWN")
                        details = error.get("details", "No details provided")
                    logger.error(f"HTTP 400: {error_id} - {details}")
                    raise CustomHttpError(f"API validation error: {details} ")
                except ValueError:
                    # Response wasn't JSON
                    logger.error(f"HTTP 400 Bad Request: {e.response.text}")
                    raise CustomHttpError(f"Bad Request (400): {e.response.text}")
            raise e from e
        except Exception as e:
            logger.debug("Hunter Exception called")
            raise Exception(f"Unexpected error in Hunter search: {e}")

    def _parse_email_data(self, data: dict) -> List[Contact]:
        """
        Parse Hunter.io / email finder JSON and return Contact objects
        """
        contacts = []

        email_data = data.get("data", {})
        company_name = email_data.get("organization") or "Unknown"

        emails_list = email_data.get("emails", [])

        for email_entry in emails_list:
            first_name = email_entry.get("first_name") or ""
            last_name = email_entry.get("last_name") or ""
            contact = Contact(
                name=f"{first_name} {last_name}".strip(),
                email=email_entry.get("value", ""),
                company_name=company_name,
                position=email_entry.get("position")
                or email_entry.get("seniority")
                or "",
            )
            contacts.append(contact)

        # logger.info(f"Parsed {len(contacts)} contacts from response data")
        return contacts
