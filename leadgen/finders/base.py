"""Base finder interface for email discovery services."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from ..models.email_result import EmailResult


class BaseFinder(ABC):
    """Abstract base class for all email finders."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    @abstractmethod
    def find_email(self, domain: str, proxy: Optional[Dict[str, str]] = None) -> EmailResult:
        """
        Find emails for a domain and return structured result.
        
        Args:
            domain: Domain name to search for emails
            proxy: Optional proxy configuration dict
            
        Returns:
            EmailResult object with emails found and metadata
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the finder name."""
        pass


class FinderError(Exception):
    """Raised when a finder encounters an error."""
    pass