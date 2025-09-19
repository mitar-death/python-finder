from typing import List, Optional,Dict, Any
from leadgen.config.loader import ConfigLoader
    
class Proxy:
    def __init__(self):
        self.config = ConfigLoader()
        self.proxy_index = 0
        self.proxies = Dict[str, Any]

    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy in rotation or None if no proxies."""
        self.proxies = self.config.load_config().proxies
        if not self.proxies:
            return None

        proxy_url = self.proxies[self.proxy_index %
                                        len(self.proxies)]
        self.proxy_index += 1
        return {"http": proxy_url, "https": proxy_url}
