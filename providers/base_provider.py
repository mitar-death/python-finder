from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """
    Abstract base class for all search providers.
    """
    def __init__(self, api_key:str):
        self.api_key = api_key
        
    @abstractmethod
    def search(self,query, provider, proxies):
        """
        Perform a search and return a list of results.
        Each result should be a dict with keys like:
            {
                "name": str,
                "url": str,
                "domain": str,
                "address": str,
                "phone": str
            }
        """
        pass