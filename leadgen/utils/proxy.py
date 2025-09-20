import os
import requests

from typing import Optional, Dict, List
from leadgen.config.loader import ConfigLoader 
from leadgen.utils.logging import logger
from leadgen.domain_finders.base import DomainFinderError

class ProxyError(Exception):
    """Raised when all proxies fail or a proxy request fails."""
    pass

class ProxyManager:
    def __init__(self, test_url: str = "https://api.yelp.com/v3/businesses/search", test_interval: int = 10, proxies_file="config/proxies.txt"):
        """
        Args:
            config: Config loader instance
            test_url: URL to test proxies against (default Yelp API)
            test_interval: how many times to use proxy before re-testing
        """
        self.proxy_index = 0
        self.use_counts = {}  # track usage count per proxy
        self.test_url = test_url
        self.test_interval = test_interval
        self.proxies: List[str] = ConfigLoader().load_config().proxies
        self.proxies_file = os.path.join(os.getcwd(), proxies_file)

    def _normalize_proxy(self, proxy_url: str) -> Dict[str, str]:
        """Normalize proxy into requests format."""
        if proxy_url.startswith("socks5://"):
            proxy_url = proxy_url.replace("socks5://", "socks5h://")
        return {"http": proxy_url, "https": proxy_url}

    def _test_proxy(self, proxy_url: str) -> bool:
        """Test if a proxy is alive by making a HEAD request."""
        try:
            response = requests.head(
                self.test_url,
                proxies=self._normalize_proxy(proxy_url),
                timeout=5
            )
            return response.status_code < 500
        except Exception as e:
            logger.warning(f"Proxy test failed for {proxy_url}: {e}")
            return False

    def _disable_proxy(self, proxy_url: str):
        """Comment out dead proxy in proxies.txt so it won’t be used again."""
        try:
            with open(self.proxies_file, "r") as f:
                lines = f.readlines()
            with open(self.proxies_file, "w") as f:
                for line in lines:
                    if line.strip() == proxy_url and not line.strip().startswith("#"):
                        f.write(f"# {line.strip()}  # disabled due to failure\n")
                        logger.info(f"Disabled proxy {proxy_url}")
                    else:
                        f.write(line)
        except Exception as e:
            logger.error(f"Failed to disable proxy {proxy_url}: {e}")

    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy in rotation or None if no proxies."""
        if not self.proxies:
            return None

        proxy_url = self.proxies[self.proxy_index % len(self.proxies)].strip()
        self.proxy_index += 1

        # Track usage
        self.use_counts[proxy_url] = self.use_counts.get(proxy_url, 0) + 1

        # Retest proxy after threshold
        if self.use_counts[proxy_url] >= self.test_interval:
            logger.info(f"Re-testing proxy {proxy_url}")
            if not self._test_proxy(proxy_url):
                self._disable_proxy(proxy_url)
                # remove it from rotation
                self.proxies = [p for p in self.proxies if not p.strip().startswith("#")]
                return self._get_proxy()  # try next one
            else:
                logger.info(f"Proxy {proxy_url} still working")
            self.use_counts[proxy_url] = 0  # reset counter

        return self._normalize_proxy(proxy_url)
    
    def safe_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Perform a request with proxy rotation.
        If a proxy fails, disable it and retry with next proxy.
        """
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.ProxyError as e:
            logger.error(f"Proxy {kwargs.get('proxies')} failed: {e}, disabling it")
            self._disable_proxy(kwargs.get('proxies'))
            raise ProxyError(f"Proxy failed: {kwargs.get('proxies')}") from e
        except requests.HTTPError as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"Request failed: {e}") from e