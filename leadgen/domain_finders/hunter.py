"""Hunter.io email finder implementation."""
import requests
from typing import Optional, Dict
from leadgen.utils.logging import logger
from leadgen.models.company import Company
from .base import BaseDomainFinder, DomainFinderError

class HunterDomainFinder(BaseDomainFinder):
    """Hunter.io domain discovery service."""
    
    BASE_URL = "https://api.hunter.io/v2/domain-search"
    
    @property
    def name(self) -> str:
        return "hunter"
    
    def find(self, company: Company, proxy: Optional[Dict[str, str]] = None) -> str:
        """Find emails for a domain using Hunter.io API."""
        params = {"domain": company.domain, "api_key": self.api_key}
        
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
            email_data = data.get("data", {})
            logger.info(f"Hunter.io returns {email_data} for email {company.domain}")
            emails = [
                email.get("value", "")
                for email in email_data.get("emails", [])
                if email.get("value")
            ]
            
            return emails
            
        except requests.HTTPError as e:
            error_msg = f"Hunter.io API error: {e}"
            return None
        except requests.RequestException as e:
            error_msg = f"Network error contacting Hunter.io: {e}"
            return None
        except Exception as e:
            error_msg = f"Unexpected error in Hunter search: {e}"
            return None