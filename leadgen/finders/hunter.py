"""Hunter.io email finder implementation."""
import requests
from typing import Optional, Dict, List
from leadgen.utils.logging import logger
from .base import BaseFinder, FinderError
from ..models.email_result import EmailResult, Contact


class HunterFinder(BaseFinder):
    """Hunter.io email discovery service."""
    
    BASE_URL = "https://api.hunter.io/v2/domain-search"
    
    @property
    def name(self) -> str:
        return "hunter"
    
    def find_email(self, domain: str, proxy: Optional[Dict[str, str]] = None) -> EmailResult:
        """Find emails for a domain using Hunter.io API."""
        params = {"domain": domain, "api_key": self.api_key}
        
        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                proxies=proxy,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract emails from Hunter.io response
            logger.info(f"Hunter.io returns {data} for email {domain}")
            
            contacts = self._parse_email_data(data)
            
            return EmailResult(
                domain=domain,
                emails=contacts,
                finder=self.name,
                success=True
            )
            
        except requests.HTTPError as e:
            error_msg = f"Hunter.io API error: {e}"
            return EmailResult(
                domain=domain,
                emails=[],
                finder=self.name,
                success=False,
                error=error_msg
            )
        except requests.RequestException as e:
            error_msg = f"Network error contacting Hunter.io: {e}"
            return EmailResult(
                domain=domain,
                emails=[],
                finder=self.name,
                success=False,
                error=error_msg
            )
        except Exception as e:
            error_msg = f"Unexpected error in Hunter search: {e}"
            return EmailResult(
                domain=domain,
                emails=[],
                finder=self.name,
                success=False,
                error=error_msg
            )
        
        
    def _parse_email_data(self, data: dict) -> List[Contact]:
        """
        Parse Hunter.io / email finder JSON and return Contact objects
        """
        contacts = []
    
        company_name = data["data"]["organization"]
        email_data = data.get("data", {})

        emails_list = email_data.get("emails", [])

        for email_entry in emails_list:
            first_name = email_entry["first_name"] # remove trailing comma
            last_name = email_entry["last_name"]
            contact = Contact(
                name=f"{first_name} {last_name}".strip(),
                email=email_entry["value"],
                company_name=company_name,
                position=email_entry["position"]
            )
            contacts.append(contact)

        logger.info(f"Parsed {len(contacts)} contacts from email data")
        return contacts