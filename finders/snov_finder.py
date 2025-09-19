import requests
from .base_finder import BaseFinder

class SnovFinder(BaseFinder):
    BASE_URL = "https://api.snov.io/v1/get-domain-emails-with-info"

    def find(self, domain, proxy=None):
        params = {"domain": domain, "access_token": self.api_key}
        proxies = proxy if proxy else None
        try:
            resp = requests.get(self.BASE_URL, params=params, proxies=proxies, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            emails = [e.get("email") for e in data.get("emails", [])]
            return emails
        except Exception as e:
            print(f"[SNOV ERROR] {e}")
            return []
