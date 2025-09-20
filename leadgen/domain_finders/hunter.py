"""Hunter.io email finder implementation."""
import requests
from typing import List, Dict, Optional, Any
from leadgen.utils.logging import logger
from leadgen.models.company import Company
from leadgen.models.email_result import Contact
from leadgen.utils.proxy import ProxyError, ProxyManager
from leadgen.config.loader import ConfigLoader
from leadgen.config.models import AppConfig
from .base import BaseDomainFinder, DomainFinderError

class HunterDomainFinder(BaseDomainFinder):
    """Hunter.io domain discovery service."""
    
    BASE_URL = "https://api.hunter.io/v2/domain-search"
    
    @property
    def name(self) -> str:
        return "hunter"
    
    def find(self, company: Company, proxy: Optional[Dict[str, str]] = None)->str|Dict[str, Any]:
        """Find emails for a company using Hunter.io API.
        Returns 
            can be str or contacts
        """
        config: AppConfig = ConfigLoader().load_config()
        params = {
            "company": company.name, 
            "api_key": self.api_key, 
            "department": config.hunter_department or"executive",
            "limit": config.email_finder_limit or 10
        }
        
        try:
            response = ProxyManager().safe_request("get",
                self.BASE_URL,
                params=params,
                proxies=proxy,
                timeout=10
            )
            
            response.raise_for_status()
            
            if response is None:
                raise DomainFinderError("No response from Hunter.io")

            data = response.json()
            
            # Extract emails from Hunter.io response
            return data
        
        except ProxyError as e:
            raise DomainFinderError(f"Hunter.io proxy error: {e}")
        except requests.HTTPError as e:
            raise DomainFinderError(f"Hunter.io API error: {e}")
        except requests.RequestException as e:
           raise DomainFinderError(f"Network error contacting Hunter.io: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error in Hunter search: {e}")


     
    def _parse_email_data(self, data: dict) -> List[Contact]:
        """
        Parse Hunter.io / email finder JSON and return Contact objects
        """
        contacts = []
    
        company_name = data["data"]["organization"] or "Unknown"
        email_data = data.get("data", {})

        emails_list = email_data.get("emails", [])
        

        for email_entry in emails_list:
            first_name = email_entry["first_name"] # remove trailing comma
            last_name = email_entry["last_name"]
            contact = Contact(
                name=f"{first_name} {last_name}".strip(),
                email=email_entry["value"],
                company_name=company_name,
                position=email_entry["position"] or email_entry["seniority"]
            )
            contacts.append(contact)

        # logger.info(f"Parsed {len(contacts)} contacts from response data")
        return contacts