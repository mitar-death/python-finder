from providers.base_provider import BaseProvider
import requests

class GoogleProvider(BaseProvider):
    BASE_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
 
    def __init__(self, api_key:str):
        super().__init__(api_key)
        
        
    def search(self,query,providers, proxies):
        params = {
            "query": query,
            "key": self.api_key,
            "limit": providers["limit"],
        }

        response = requests.get(self.BASE_URL, params=params, proxies=proxies, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Google API request failed with status code {response.status_code}")
    
        places = response.json().get("results", [])
        results = []
        for p in places: 
            results.append({
                "name": p["name"],
                "url": None,
                "domain": p["name"].split()[0].lower(),
                "address": p["formatted_address"],
                "phone": None
            })
            
        return results
