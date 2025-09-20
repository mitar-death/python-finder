"""Company data model."""
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


@dataclass
class Company:
    """Represents a company found by a search provider."""
    id: str
    name: str
    url: Optional[str] = None
    domain: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None

    def __post_init__(self):
        """Extract domain from URL if not provided and it's not a provider URL."""
        if self.url and self.domain is None:
            try:
                parsed = urlparse(self.url)
                extracted_domain = parsed.netloc

                # Only use extracted domain if it's not a provider domain
                from ..utils.domain import DomainResolver
                resolver = DomainResolver()
                if resolver._is_valid_business_domain(extracted_domain):
                    self.domain = extracted_domain
                # If it's a provider domain, leave domain as None
            except Exception:
                self.domain = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "domain": self.domain,
            "address": self.address,
            "phone": self.phone,
        }
