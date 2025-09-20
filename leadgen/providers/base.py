"""Base provider interface for search providers."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models.company import Company


class BaseProvider(ABC):
    """Abstract base class for all search providers."""
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.config = config or {}
    
    @abstractmethod
    def search(self, query: str, proxy: Optional[Dict[str, str]] = None) -> List[Company]:
        """
        Perform a search and return a list of Company objects.
        
        Args:
            query: Search query string
            proxy: Optional proxy configuration dict (e.g., {"http": "...", "https": "..."})
            
        Returns:
            List of Company objects found
            
        Raises:
            ProviderError: If the search fails
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass


class ProviderError(Exception):
    """Raised when a provider encounters an error."""
    pass