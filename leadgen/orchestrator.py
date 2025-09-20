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
from .finders.base import BaseFinder
from .finders.hunter import HunterFinder
from .utils.logging import logger
from .utils.domain import DomainResolver
from leadgen.domain_finders.base import BaseDomainFinder, BaseDomainFinder
from leadgen.domain_finders.hunter import HunterDomainFinder
class LeadOrchestrator:
    """Orchestrates the lead generation process."""

    def __init__(self, config: AppConfig, state_store=None, args=None):
        self.config = config
        self.state_store = state_store
        self.providers: Dict[str, BaseProvider] = {}
        self.finders: Dict[str, BaseFinder] = {}
        self.domain_finders :Dict[str, BaseDomainFinder] ={}
        # Results storage
        self.companies: List[Company] = []
        self.domains: Set[str] = set()
        self.email_results: List[EmailResult] = []
        self.proxy_index = 0
        self.args = args
        

        self._initialize_providers()
        self._initialize_domain_finders()
        self._initialize_finders()
        

    def _initialize_providers(self):
        """Initialize search providers."""
        provider_map = {
            "yelp": YelpProvider,
            # "google": GoogleProvider,  # Will add when dependencies are available
        }

        for name, api_keys in self.config.providers.items():
            if name.lower() in provider_map:
                for i, api_key in enumerate(api_keys):
                    try:
                        provider_config = {}
                        if name.lower() == "yelp":
                            provider_config = {
                                "location": self.config.location,
                                "limit": self.config.yelp_limit
                            }

                        provider = provider_map[name.lower()](api_key, provider_config)
                        # Use unique keys for multiple instances of same provider type
                        provider_key = f"{name}_{i+1}" if len(api_keys) > 1 else name
                        self.providers[provider_key] = provider
                        logger.info(f"Initialized {provider_key} provider")

                    except Exception as e:
                        logger.error(f"Failed to initialize {name} provider instance {i+1}: {e}")
            else:
                logger.warning(f"Unknown provider: {name}")

    def _initialize_domain_finders(self):
        """Initialize email finders."""
        domain_finder_map = {
            #  "apollo": ApolloDomainFinder,
             "hunter": HunterDomainFinder,
             
        }
        
        domain_finders = ConfigLoader()._load_providers('domain_finders.txt')
        for name, api_keys in domain_finders.items():
            if name.lower() in domain_finder_map:
                for i, api_key in enumerate(api_keys):
                    try:
                        finder = domain_finder_map[name.lower()](api_key)
                        # Use unique keys for multiple instances of same finder type
                        finder_key = f"{name}_{i+1}" if len(api_keys) > 1 else name
                        self.domain_finders[finder_key] = finder
                        logger.info(f"Initialized {finder_key} domain finder")

                    except Exception as e:
                        logger.error(f"Failed to initialize {name} domain finder instance {i+1}: {e}")
            else:
                logger.warning(f"Unknown domain finder: {name}")

    
    def _initialize_finders(self):
        """Initialize email finders."""
        finder_map = {
            "hunter": HunterFinder,
            
            # "snov": SnovFinder,  # Will add when needed
        }

        for name, api_keys in self.config.email_finders.items():
            if name.lower() in finder_map:
                for i, api_key in enumerate(api_keys):
                    try:
                        finder = finder_map[name.lower()](api_key)
                        # Use unique keys for multiple instances of same finder type
                        finder_key = f"{name}_{i+1}" if len(api_keys) > 1 else name
                        self.finders[finder_key] = finder
                        logger.info(f"Initialized {finder_key} email finder")

                    except Exception as e:
                        logger.error(f"Failed to initialize {name} email finder instance {i+1}: {e}")
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
                        f"[{provider_name.upper()}] Searching '{query}'"
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
                
        
        # Filter companies using StateStore for proper deduplication
        if self.state_store:
            new_companies = []
            skipped_count = 0
            for company in all_companies:
                if not self.state_store.is_seen_company(company):
                    new_companies.append(company)
                    self.state_store.add_seen_company(company)
                else:
                    skipped_count += 1
            
            logger.info(f"Found {len(new_companies)} new companies (skipped {skipped_count} already processed)")
            self.companies = new_companies
        else:
            # Fallback to old logic if no state store
            old_companies = ConfigLoader()._load_companies(f"companies.txt")
            filtered_companies = [company for company in all_companies if company.name not in old_companies]
            logger.info(f"Found {len(filtered_companies)} new companies")
            self.companies = filtered_companies
        logger.success(
            f"Search phase complete: {len(self.companies)} companies"
        )
        
        # Save state after company search phase
        if self.state_store:
            self.state_store.save_state()
            logger.debug("💾 State saved after company search phase")

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
        


        # Filter domains that haven't been processed yet
        domains_to_process = []
        if self.state_store:
            for domain in self.domains:
                if not self.state_store.is_seen_domain(domain):
                    domains_to_process.append(domain)
                else:
                    logger.info(f"Domain {domain} already processed for emails, skipping")
        else:
            domains_to_process = list(self.domains)
        
        logger.info(f"Processing emails for {len(domains_to_process)} new domains")

        for finder_name, finder in self.finders.items():
            logger.info(f"Running {finder_name} email finder")

            for domain in domains_to_process:
                try:
                    proxy = ProxyManager()._get_proxy()
                    proxy_info = f"proxy {proxy}" if proxy else "no proxy"
                    logger.info(
                        f"[{finder_name.upper()}] Finding emails for '{domain}'"
                    )

                    result = finder.find_email(domain, proxy)
                    self.email_results.append(result)

                    if result.success and result.emails:
                        # Mark emails as seen in StateStore
                        if self.state_store:
                            for email_obj in result.emails:
                                if hasattr(email_obj, 'email') and email_obj.email:
                                    self.state_store.add_seen_email(email_obj.email)
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
                            f"[{name.upper()}] Finding emails for '{company_name}'"
                        )
                        res = domain_finder.find(company, proxy=proxy) #hwhere safe_request is called
                       
                        if res and isinstance(res, str):
                            # Domain found
                            domain = resolver._clean_and_extract_domain(res)
                            if domain and resolver._is_valid_business_domain(domain):
                                # Check if domain already processed (StateStore integration)
                                if self.state_store and self.state_store.is_seen_domain(domain):
                                    logger.info(f"Domain {domain} already processed, skipping")
                                else:
                                    company.domain = domain
                                    self.domains.add(domain)
                                    if self.state_store:
                                        self.state_store.add_seen_domain(domain)
                                    logger.info(f"Found domain {domain} for {company_name}")
                                found_result = True
                                
                        else:
                            # For hunter domain finder that returns emails instead of domains
                            domain = res["data"]["domain"]
                            contacts = domain_finder._parse_email_data(res)
                            
                            # Check if domain already processed
                            if self.state_store and self.state_store.is_seen_domain(domain):
                                logger.info(f"Domain {domain} already processed, skipping")
                            else:
                                # Emails found
                                result = EmailResult(
                                    domain=domain, 
                                    emails=contacts, 
                                    finder=name, 
                                    success=True
                                    )
                                
                                self.domains.add(domain)
                                if self.state_store:
                                    self.state_store.add_seen_domain(domain)
                                    # Also mark emails as seen
                                    for contact in contacts:
                                        if hasattr(contact, 'email') and contact.email:
                                            self.state_store.add_seen_email(contact.email)
                            # Always mark as processed, even if we skipped it
                            if self.state_store and domain:
                                self.state_store.add_seen_domain(domain)
                                self.email_results.append(result)  # Correctly store the EmailResult object
                                logger.info(f"Found {len(res['data']['emails'])} emails for {company_name}")
                            found_result = True
                            
                    except Exception as e:
                        logger.error(type(e))
                        logger.error(f"Error for {company_name} with finder {[name.upper()]}: {e}")
                        
                        logger.info("selecting a new domain finder")
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
                # run only if args has fresh
                # if self.args.fresh:
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
