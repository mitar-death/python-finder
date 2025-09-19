import requests
from .base_provider import BaseProvider

class GoogleProvider(BaseProvider):
    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: str, cx: str, config: dict = None):
        super().__init__(api_key)
        self.cx = cx
        self.config = config or {"num": 5}  # default 5 results

    def search(self, query: str, proxy: dict = None):
        params = {
            "q": query,
            "key": self.api_key,
            "cx": self.cx,
            "num": self.config.get("num", 5),
        }

        proxies = proxy if proxy else None

        response = requests.get(
            self.BASE_URL, params=params, proxies=proxies, timeout=10
        )

        if response.status_code != 200:
            raise Exception(f"Google API request failed with status code {response.status_code}")

        items = response.json().get("items", [])

        results = []
        for item in items:
            results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
                "displayLink": item.get("displayLink"),
            })

        return results
