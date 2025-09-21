"""Domain utilities for business website resolution."""

import re
from urllib.parse import urlparse
from typing import Optional, Set
import requests
from ..utils.logging import logger


class DomainResolver:
    """Resolves business domains from provider data."""

    # Provider domains to exclude from email discovery
    PROVIDER_DOMAINS = {
        "yelp.com",
        "www.yelp.com",
        "google.com",
        "www.google.com",
        "maps.google.com",
        "facebook.com",
        "www.facebook.com",
        "m.facebook.com",
        "instagram.com",
        "www.instagram.com",
        "twitter.com",
        "www.twitter.com",
        "x.com",
        "linkedin.com",
        "www.linkedin.com",
        "foursquare.com",
        "www.foursquare.com",
        "yellowpages.com",
        "www.yellowpages.com",
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def _clean_and_extract_domain(self, url: str) -> Optional[str]:
        """Clean URL and extract domain."""
        try:
            # Handle relative URLs and clean up
            if url.startswith("//"):
                url = "https:" + url
            elif url.startswith("/"):
                return None  # Skip relative URLs without base
            elif not url.startswith(("http://", "https://")):
                url = "https://" + url

            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove common prefixes
            if domain.startswith("www."):
                domain = domain[4:]

            return domain if domain else None

        except Exception:
            return None

    def _is_provider_domain(self, domain: str) -> bool:
        """Check if domain is a provider domain that should be excluded."""
        if not domain:
            return True

        domain = domain.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        return domain in self.PROVIDER_DOMAINS or any(
            provider in domain
            for provider in ["yelp", "google", "facebook", "instagram"]
        )

    def _is_valid_business_domain(self, domain: str) -> bool:
        """Validate that domain is suitable for business email discovery."""
        if isinstance(domain, str):
            return False

        if not domain or self._is_provider_domain(domain):
            return False
        logger.info(f"Validating domain: {domain}")

        # Basic domain validation
        if not re.match(
            r"^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}$", domain
        ):
            return False

        # Exclude common non-business domains
        excluded_patterns = [
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "aol.com",
            "icloud.com",
            "live.com",
            "msn.com",
        ]

        return not any(pattern in domain.lower() for pattern in excluded_patterns)

    def filter_valid_domains(self, domains: Set[str]) -> Set[str]:
        """Filter set of domains to include only valid business domains."""
        return {domain for domain in domains if self._is_valid_business_domain(domain)}
