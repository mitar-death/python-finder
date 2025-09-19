"""Domain utilities for business website resolution."""
import re
import requests
from urllib.parse import urlparse, urljoin
from typing import Optional, Set
from ..utils.logging import logger


class DomainResolver:
    """Resolves business domains from provider data."""
    
    # Provider domains to exclude from email discovery
    PROVIDER_DOMAINS = {
        "yelp.com", "www.yelp.com",
        "google.com", "www.google.com", "maps.google.com",
        "facebook.com", "www.facebook.com", "m.facebook.com",
        "instagram.com", "www.instagram.com",
        "twitter.com", "www.twitter.com", "x.com",
        "linkedin.com", "www.linkedin.com",
        "foursquare.com", "www.foursquare.com",
        "yellowpages.com", "www.yellowpages.com"
    }
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_business_domain(self, company_name: str, yelp_url: str, address: str = "") -> Optional[str]:
        """
        Extract business domain from Yelp business page.
        
        Args:
            company_name: Name of the business
            yelp_url: Yelp business page URL
            address: Business address for validation
            
        Returns:
            Business domain if found, None otherwise
        """
        try:
            # First try to extract website from Yelp page
            domain = self._extract_website_from_yelp_page(yelp_url)
            
            if domain and self._is_valid_business_domain(domain):
                logger.debug(f"Found business domain {domain} from Yelp page for {company_name}")
                return domain
            
            # If no website found on Yelp page, try basic search approach
            # This is a simplified approach - in production you'd use proper APIs
            domain = self._search_business_website(company_name, address)
            
            if domain and self._is_valid_business_domain(domain):
                logger.debug(f"Found business domain {domain} via search for {company_name}")
                return domain
                
            logger.warning(f"Could not find business website for {company_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error resolving domain for {company_name}: {e}")
            return None
    
    def _extract_website_from_yelp_page(self, yelp_url: str) -> Optional[str]:
        """Extract business website from Yelp business page."""
        try:
            response = self.session.get(yelp_url, timeout=self.timeout)
            response.raise_for_status()
            
            # Look for business website link patterns in the HTML
            # This is a simplified approach - Yelp's actual structure may vary
            website_patterns = [
                r'href="([^"]*)"[^>]*>(?:Website|Visit Website|Business Website)',
                r'"businessUrl":"([^"]*)"',
                r'"website":{"url":"([^"]*)"',
                r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*website[^"]*"'
            ]
            
            content = response.text
            for pattern in website_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    domain = self._clean_and_extract_domain(match)
                    if domain and not self._is_provider_domain(domain):
                        return domain
                        
            return None
            
        except Exception as e:
            logger.debug(f"Could not extract website from Yelp page {yelp_url}: {e}")
            return None
    
    def _search_business_website(self, company_name: str, address: str) -> Optional[str]:
        """
        Basic business website search using company name and address.
        Note: This is a simplified implementation. In production, you'd use:
        - Google Custom Search API
        - Business data APIs (Clearbit, FullContact, etc.)
        - Domain intelligence services
        """
        # For now, return None as we don't have search API setup
        # This would be implemented with proper search APIs in production
        logger.debug(f"Business website search not implemented for {company_name}")
        return None
    
    def _clean_and_extract_domain(self, url: str) -> Optional[str]:
        """Clean URL and extract domain."""
        try:
            # Handle relative URLs and clean up
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                return None  # Skip relative URLs without base
            elif not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove common prefixes
            if domain.startswith('www.'):
                domain = domain[4:]
                
            return domain if domain else None
            
        except Exception:
            return None
    
    def _is_provider_domain(self, domain: str) -> bool:
        """Check if domain is a provider domain that should be excluded."""
        if not domain:
            return True
            
        domain = domain.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain in self.PROVIDER_DOMAINS or any(
            provider in domain for provider in ['yelp', 'google', 'facebook', 'instagram']
        )
    
    def _is_valid_business_domain(self, domain: str) -> bool:
        """Validate that domain is suitable for business email discovery."""
        if not domain or self._is_provider_domain(domain):
            return False
            
        # Basic domain validation
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}$', domain):
            return False
            
        # Exclude common non-business domains
        excluded_patterns = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'live.com', 'msn.com'
        ]
        
        return not any(pattern in domain.lower() for pattern in excluded_patterns)
    
    def filter_valid_domains(self, domains: Set[str]) -> Set[str]:
        """Filter set of domains to include only valid business domains."""
        return {domain for domain in domains if self._is_valid_business_domain(domain)}