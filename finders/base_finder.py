from abc import ABC, abstractmethod


class BaseFinder(ABC):
    def __init__(self, api_key):
        self.api_key = api_key

    @abstractmethod
    def find(self, domain: str, proxy: dict = None) -> list[str]:
        pass