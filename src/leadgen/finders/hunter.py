"""Hunter.io email finder implementation."""
import requests
from typing import Optional, Dict
from .base import BaseFinder, FinderError
from ..models.email_result import EmailResult


class HunterFinder(BaseFinder):
    """Hunter.io email discovery service."""
    
    BASE_URL = "https://api.hunter.io/v2/domain-search"
    
    @property
    def name(self) -> str:
        return "hunter"
    
    def find(self, domain: str, proxy: Optional[Dict[str, str]] = None) -> EmailResult:
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
            email_data = data.get("data", {})
            emails = [
                email.get("value", "")
                for email in email_data.get("emails", [])
                if email.get("value")
            ]
            
            return EmailResult(
                domain=domain,
                emails=emails,
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