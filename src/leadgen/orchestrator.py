"""Main orchestrator for the lead generation process."""
import time
import random
from typing import Dict, List, Set, Optional
from .config.loader import ConfigLoader, ConfigurationError
from .config.models import AppConfig
from .models.company import Company
from .models.email_result import EmailResult
from .providers.base import BaseProvider, ProviderError
from .providers.yelp import YelpProvider
from .finders.base import BaseFinder, FinderError
from .finders.hunter import HunterFinder
from .utils.logging import logger


class LeadOrchestrator:
    """Orchestrates the lead generation process."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.providers: Dict[str, BaseProvider] = {}
        self.finders: Dict[str, BaseFinder] = {}
        self.proxy_index = 0
        
        # Results storage
        self.companies: List[Company] = []
        self.domains: Set[str] = set()
        self.email_results: List[EmailResult] = []
        
        self._initialize_providers()
        self._initialize_finders()
    
    def _initialize_providers(self):
        """Initialize search providers."""
        provider_map = {
            "yelp": YelpProvider,
            # "google": GoogleProvider,  # Will add when dependencies are available
        }
        
        for name, api_key in self.config.providers.items():
            if name.lower() in provider_map:
                try:
                    provider_config = {}
                    if name.lower() == "yelp":
                        provider_config = {
                            "location": self.config.yelp_location,
                            "limit": self.config.yelp_limit
                        }
                    
                    provider = provider_map[name.lower()](api_key, provider_config)
                    self.providers[name] = provider
                    logger.info(f"Initialized {name} provider")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize {name} provider: {e}")
            else:
                logger.warning(f"Unknown provider: {name}")
    
    def _initialize_finders(self):
        """Initialize email finders."""
        finder_map = {
            "hunter": HunterFinder,
            # "snov": SnovFinder,  # Will add when needed
        }
        
        for name, api_key in self.config.email_finders.items():
            if name.lower() in finder_map:
                try:
                    finder = finder_map[name.lower()](api_key)
                    self.finders[name] = finder
                    logger.info(f"Initialized {name} email finder")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize {name} finder: {e}")
            else:
                logger.warning(f"Unknown email finder: {name}")
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy in rotation or None if no proxies."""
        if not self.config.proxies:
            return None
            
        proxy_url = self.config.proxies[self.proxy_index % len(self.config.proxies)]
        self.proxy_index += 1
        
        return {"http": proxy_url, "https": proxy_url}
    
    def run_provider_search(self):
        """Run the provider search phase."""
        if not self.providers:
            logger.warning("No providers configured, skipping search phase")
            return
            
        if not self.config.queries:
            logger.warning("No queries configured, skipping search phase") 
            return
        
        logger.info("Starting provider search phase")
        logger.info(f"Searching with {len(self.providers)} providers for {len(self.config.queries)} queries")
        
        for provider_name, provider in self.providers.items():
            logger.info(f"Running {provider_name} provider")
            
            for query in self.config.queries:
                try:
                    proxy = self._get_proxy()
                    proxy_info = f"proxy {proxy}" if proxy else "no proxy"
                    logger.info(f"[{provider_name.upper()}] Searching '{query}' with {proxy_info}")
                    
                    companies = provider.search(query, proxy)
                    
                    logger.success(f"Found {len(companies)} companies for '{query}'")
                    
                    # Store results and extract valid business domains
                    for company in companies:
                        self.companies.append(company)
                        if company.domain:
                            # Only add if it's a valid business domain (not provider domain)
                            from .utils.domain import DomainResolver
                            resolver = DomainResolver()
                            if resolver._is_valid_business_domain(company.domain):
                                self.domains.add(company.domain)
                            else:
                                logger.warning(f"Skipping invalid/provider domain: {company.domain}")
                    
                    # Rate limiting between requests
                    if self.config.delays.request_delay > 0:
                        time.sleep(self.config.delays.request_delay)
                        
                except ProviderError as e:
                    logger.error(f"[{provider_name.upper()}] Provider error for '{query}': {e}")
                    continue
                except Exception as e:
                    logger.error(f"[{provider_name.upper()}] Unexpected error for '{query}': {e}")
                    continue
            
            # Delay between providers
            if self.config.delays.provider_delay > 0:
                logger.info(f"Waiting {self.config.delays.provider_delay}s before next provider")
                time.sleep(self.config.delays.provider_delay)
        
        logger.success(f"Search phase complete: {len(self.companies)} companies, {len(self.domains)} unique domains")
    
    def run_email_discovery(self):
        """Run the email discovery phase."""
        if not self.finders:
            logger.warning("No email finders configured, skipping email discovery")
            return
            
        if not self.domains:
            logger.warning("No domains found, skipping email discovery")
            return
        
        # Wait before starting email discovery
        if self.config.delays.finder_delay > 0:
            logger.info(f"Waiting {self.config.delays.finder_delay}s before starting email discovery")
            time.sleep(self.config.delays.finder_delay)
        
        logger.info("Starting email discovery phase")
        logger.info(f"Searching emails for {len(self.domains)} domains using {len(self.finders)} finders")
        
        for finder_name, finder in self.finders.items():
            logger.info(f"Running {finder_name} email finder")
            
            for domain in self.domains:
                try:
                    proxy = self._get_proxy()
                    proxy_info = f"proxy {proxy}" if proxy else "no proxy"
                    logger.info(f"[{finder_name.upper()}] Finding emails for '{domain}' with {proxy_info}")
                    
                    result = finder.find(domain, proxy)
                    self.email_results.append(result)
                    
                    if result.success and result.emails:
                        logger.success(f"Found {len(result.emails)} emails for '{domain}'")
                    elif result.success:
                        logger.info(f"No emails found for '{domain}'")
                    else:
                        logger.warning(f"Failed to find emails for '{domain}': {result.error}")
                    
                    # Rate limiting between requests
                    if self.config.delays.request_delay > 0:
                        time.sleep(self.config.delays.request_delay)
                        
                except Exception as e:
                    logger.error(f"[{finder_name.upper()}] Unexpected error for '{domain}': {e}")
                    # Create failed result
                    failed_result = EmailResult(
                        domain=domain,
                        emails=[],
                        finder=finder_name,
                        success=False,
                        error=str(e)
                    )
                    self.email_results.append(failed_result)
                    continue
        
        successful_results = [r for r in self.email_results if r.success and r.emails]
        logger.success(f"Email discovery complete: {len(successful_results)} domains with emails found")
    
    def run_full_pipeline(self):
        """Run the complete lead generation pipeline."""
        logger.info("Starting lead generation pipeline")
        
        try:
            self.run_provider_search()
            self.run_email_discovery()
            logger.success("Lead generation pipeline completed successfully")
            
        except KeyboardInterrupt:
            logger.warning("Pipeline interrupted by user")
        except Exception as e:
            logger.error(f"Pipeline failed with unexpected error: {e}")
            raise