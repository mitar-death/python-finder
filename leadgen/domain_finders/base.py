from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from leadgen.models.company import Company
from leadgen.models.email_result import Contact


class BaseDomainFinder(ABC):
    """Abstract class for all domain finders"""

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.config = config or {}

    @abstractmethod
    def find(
        self, company: Company, proxy: Optional[Dict[str, str]] = None
    ) -> str | List[Contact]:
        """
        Perform a domain search and return the domain.

        Args:
            company: company object
            proxy: Optional proxy configuration dict (e.g., {"http": "...", "https": "..."})

        Returns:
            a valid Company domain

        Raises:
            DomainFinderError If the domain search fails
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the domain name."""
        pass


class DomainFinderError(Exception):
    """Raised when a domain search encounters an error."""

    pass
