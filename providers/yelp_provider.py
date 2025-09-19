import requests
from .base_provider import BaseProvider

class YelpProvider(BaseProvider):
    BASE_URL = "https://api.yelp.com/v3/businesses/search"
    
    def __init__(self, api_key: str, config: dict = None):
        super().__init__(api_key)
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        # store provider-specific settings (like location, limit)
        self.config = config or {"location": "United States", "limit": 5}

    def search(self, query: str, proxy: dict = None):
        params = {
            "term": query,
            "location": self.config.get("location", "United States"),
            "limit": self.config.get("limit", 5),
        }

        proxies = proxy if proxy else None

        response = requests.get(
            self.BASE_URL, headers=self.headers, params=params, proxies=proxies, timeout=10
        )

        if response.status_code != 200:
            raise Exception(f"Yelp API request failed with status code {response.status_code}")

        businesses = response.json().get("businesses", [])

        results = []
        for b in businesses: 
            results.append({
                "name": b.get("name"),
                "url": b.get("url"),
                "domain": b.get("url", "").split("/")[2] if b.get("url") else None,
                "address": ", ".join(b.get("location", {}).get("display_address", [])),
                "phone": b.get("phone"),
            })

        return results
