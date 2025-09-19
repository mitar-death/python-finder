from abc import ABC, abstractmethod


class BaseFinder(ABC):
    def __init__(self, api_key):
        self.api_key = api_key

    @abstractmethod
    def find(self, text: str) -> list[str]:
        pass