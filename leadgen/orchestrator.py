"""Main orchestrator for the lead generation process."""
import sys
import time
import random
from typing import Dict, List, Set, Optional
from leadgen.utils.proxy import  ProxyManager
from .config.loader import ConfigLoader, ConfigurationError
from .config.models import AppConfig
from .models.company import Company
from .models.email_result import EmailResult
from .providers.base import BaseProvider, ProviderError
from .providers.yelp import YelpProvider
from .finders.base import BaseFinder, FinderError
from .finders.hunter import HunterFinder
from .utils.logging import logger
from .utils.domain import DomainResolver
from leadgen.domain_finders.base import BaseDomainFinder
from leadgen.domain_finders.hunter import HunterDomainFinder
from leadgen.models.email_result import Contact
from leadgen.domain_finders.hunter import HunterDomainFinder, DomainFinderError
class LeadOrchestrator:
    """Orchestrates the lead generation process."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.providers: Dict[str, BaseProvider] = {}
        self.finders: Dict[str, BaseFinder] = {}
        self.domain_finders :Dict[str, BaseDomainFinder] ={}
        # Results storage
        self.companies: List[Company] = []
        self.domains: Set[str] = set()
        self.email_results: List[EmailResult] = []
        self.proxy_index = 0
        

        self._initialize_providers()
        self._initialize_domain_finders()
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
                            "location": self.config.location,
                            "limit": self.config.yelp_limit
                        }

                    provider = provider_map[name.lower()](api_key,
                                                          provider_config)
                    self.providers[name] = provider
                    logger.info(f"Initialized {name} provider")

                except Exception as e:
                    logger.error(f"Failed to initialize {name} provider: {e}")
            else:
                logger.warning(f"Unknown provider: {name}")

    def _initialize_domain_finders(self):
        """Initialize email finders."""
        domain_finder_map = {
            #  "apollo": ApolloDomainFinder,
             "hunter": HunterDomainFinder
        }
        
        domain_finders = ConfigLoader()._load_providers('domain_finders.txt')
        for name, api_key in domain_finders.items():
            if name.lower() in domain_finder_map:
                try:
                    finder = domain_finder_map[name.lower()](api_key)
                    self.domain_finders[name] = finder
                    logger.info(f"Initialized {name} domain finder")

                except Exception as e:
                    logger.error(f"Failed to initialize {name} finder: {e}")
            else:
                logger.warning(f"Unknown domain finder: {name}")

    
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


    def run_provider_search(self):
        """Run the provider search phase."""
        if not self.providers:
            logger.warning("No providers configured, skipping search phase")
            return

        if not self.config.queries:
            logger.warning("No queries configured, skipping search phase")
            return

        logger.info("Starting provider search phase")
        logger.info(
            f"Searching with {len(self.providers)} providers for {len(self.config.queries)} queries"
        )
        all_companies =[]
        for provider_name, provider in self.providers.items():
            logger.info(f"Running {provider_name} provider")

            for query in self.config.queries:
                try:
                    proxy = ProxyManager()._get_proxy()
                    proxy_info = f"proxy {proxy}" if proxy else "no proxy"
                    logger.info(
                        f"[{provider_name.upper()}] Searching '{query}' with {proxy_info}"
                    )

                    companies = provider.search(query, proxy)

                    logger.success(
                        f"Found {len(companies)} companies for '{query}'")

                    
                    all_companies.extend(companies)
                    # Rate limiting between requests
                    if self.config.delays.request_delay > 0:
                        time.sleep(self.config.delays.request_delay)

                except ProviderError as e:
                    logger.error(
                        f"[{provider_name.upper()}] Provider error for '{query}': {e}"
                    )
                    continue
                except Exception as e:
                    logger.error(
                        f"[{provider_name.upper()}] Unexpected error for '{query}': {e}"
                    )
                    continue
            
            # Delay between providers
            if self.config.delays.provider_delay > 0:
                logger.info(
                    f"Waiting {self.config.delays.provider_delay}s before next provider"
                )
                time.sleep(self.config.delays.provider_delay)
                
        
        #NOTE: Remove the existing companies from the old data
        old_companies = ConfigLoader()._load_companies(f"companies.txt")
        filered_companies = [company for company in all_companies if company.name not in old_companies]
        
        logger.info(f"Found {len(filered_companies)} new companies")
        
        self.companies = filered_companies
        logger.success(
            f"Search phase complete: {len(filered_companies)} companies"
        )

    def run_email_discovery(self):
        """Run the email discovery phase."""
        if not self.finders:
            logger.warning(
                "No email finders configured, skipping email discovery")
            return

        if not self.domains:
            logger.warning("No domains found, skipping email discovery")
            return

        # Wait before starting email discovery
        if self.config.delays.finder_delay > 0:
            logger.info(
                f"Waiting {self.config.delays.finder_delay}s before starting email discovery"
            )
            time.sleep(self.config.delays.finder_delay)

        logger.info("Starting email discovery phase")
        logger.info(
            f"Searching emails for {len(self.domains)} domains using {len(self.finders)} finders"
        )
        


        for finder_name, finder in self.finders.items():
            logger.info(f"Running {finder_name} email finder")

            for domain in self.domains:
                try:
                    proxy = ProxyManager()._get_proxy()
                    proxy_info = f"proxy {proxy}" if proxy else "no proxy"
                    logger.info(
                        f"[{finder_name.upper()}] Finding emails for '{domain}' with {proxy_info}"
                    )

                    result = finder.find_email(domain, proxy)
                    self.email_results.append(result)

                    if result.success and result.emails:
                        logger.success(
                            f"Found {len(result.emails)} emails for '{domain}'"
                        )
                    elif result.success:
                        logger.info(f"No emails found for '{domain}'")
                    else:
                        logger.warning(
                            f"Failed to find emails for '{domain}': {result.error}"
                        )

                    # Rate limiting between requests
                    if self.config.delays.request_delay > 0:
                        time.sleep(self.config.delays.request_delay)

                except Exception as e:
                    logger.error(
                        f"[{finder_name.upper()}] Unexpected error for '{domain}': {e}"
                    )
                    # Create failed result
                    failed_result = EmailResult(domain=domain,
                                                emails=[],
                                                finder=finder_name,
                                                success=False,
                                                error=str(e))
                    self.email_results.append(failed_result)
                    continue

        successful_results = [
            r for r in self.email_results if r.success and r.emails
        ]
        logger.success(
            f"Email discovery complete: {len(successful_results)} domains with emails found"
        )


    def run_domain_discovery(self):
        """
        Extract business domain from Yelp business page.
        """
        logger.info("Starting domain discovery phase")
        resolver = DomainResolver()
        
        for company in self.companies:
            company_name = getattr(company, "name", "UNKNOWN")
            
            # This flag ensures we stop searching once a valid result is found for a single company
            found_result = False
            
            if self.domain_finders:
                finders_iter = self.domain_finders.items() if isinstance(self.domain_finders, dict) else self.domain_finders
                
                for name, domain_finder in finders_iter:
                    if found_result:
                        break  # Move to the next company if we already found a result
                    
                    try:
                        proxy = ProxyManager()._get_proxy()
                        proxy_info = f"proxy {proxy}" if proxy else "no proxy"
                        logger.info(
                            f"[{name.upper()}] Finding emails for '{company_name}' with {proxy_info}"
                        )
                        res = domain_finder.find(company, proxy=proxy) #hwhere safe_request is called
                       
                        if res and isinstance(res, str):
                            # Domain found
                            domain = resolver._clean_and_extract_domain(res)
                            if domain and resolver._is_valid_business_domain(domain):
                                company.domain = domain
                                self.domains.add(domain)  # Correctly store the domain
                                logger.info(f"Found domain {domain} for {company_name}")
                                found_result = True
                                
                        else:
                            # For hunter domain finder that retruns emails instead of domains
                            domain = res["data"]["domain"]
                            contacts = domain_finder._parse_email_data(res)
                            # Emails found
                            result = EmailResult(
                                domain=domain, 
                                emails=contacts, 
                                finder=name, 
                                success=True
                                )
                            
                            self.domains.add(domain)
                            self.email_results.append(result)  # Correctly store the EmailResult object
                            logger.info(f"Found {len(res['data']['emails'])} emails for {company_name}")
                            found_result = True
                            
                    except Exception as e:
                        logger.error(f"Error for {company_name} with finder {[name.upper()]}: {e}")
                        # You can log the error but continue to the next finder
                        continue
   
        logger.success(
            f"Domain discovery complete: {len(self.domains)} valid domains found and {len(self.email_results)} email results collected"
        )



    def run_full_pipeline(self):
        """Run the complete lead generation pipeline."""
        logger.info("Starting lead generation pipeline")
        
        try:
            if self.config.run_email_finder_alone:
                self.run_email_discovery()
            else:
                self.run_provider_search()
                self.run_domain_discovery()
                
                #only run this if the email_results is empty after processing domain discovery
                if not self.email_results:
                    self.run_email_discovery()
                logger.success("Lead generation pipeline completed successfully")

        except KeyboardInterrupt:
            logger.warning("Pipeline interrupted by user")
        except Exception as e:
            logger.error(f"Pipeline failed with unexpected error: {e}")
            raise
