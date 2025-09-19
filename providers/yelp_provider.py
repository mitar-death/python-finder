from providers.base_provider import BaseProvider
import requests



class YelpProvider(BaseProvider):
    BASE_URL = "https://api.yelp.com/v3/businesses/search"
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def search(self, query, provider, proxy):
        parms = {
            "term": query,
            "location": provider["location"],
            "limit": provider["limit"],
        
        }
        
        response = requests.get(self.BASE_URL, headers=self.headers, params=parms, proxies=proxy)
        
        if response.status_code != 200:
            raise Exception(f"Yelp API request failed with status code {response.status_code}")
        
        results = []
        for b in businesses: 
            results.append({
                "name": b["name"],
                "url": b["url"],
                "domain": b["url"].split("/")[2],
                "address": ", ".join(b["location"]["display_address"]),
                "phone": b["phone"]
            })
        

        businesses = response.json().get("businesses", [])