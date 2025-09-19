import requests

from .base_finder import BaseFinder

class HunterFinder(BaseFinder):
    BASE_URL = "https://api.hunter.io/v2/domain-search"

    def find(self, domain, proxy=None):
        params = {"domain": domain, "api_key": self.api_key}
        proxies = {"http": proxy, "https": proxy} if proxy else None
        try:
            resp = requests.get(self.BASE_URL, params=params, proxies=proxies, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            emails = [e.get("value") for e in data.get("data", {}).get("emails", [])]
            return emails
        except Exception as e:
            print(f"[HUNTER ERROR] {e}")
            return []
