"""Output storage management."""
import json
import os
from pathlib import Path
from typing import List
from ..models.company import Company
from ..models.email_result import EmailResult
from ..config.models import OutputConfig
from ..utils.logging import logger


class OutputManager:
    """Manages saving results to various output formats."""
    
    def __init__(self, config: OutputConfig):
        self.config = config
        self.output_dir = Path(config.directory)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_results(self, companies: List[Company], email_results: List[EmailResult], filtered_domains: set = None):
        """Save all results to configured output format."""
        logger.info(f"Saving results to {self.output_dir}")
        
        # Save companies
        if companies:
            self._save_companies(companies)
            
        # Save domains using the filtered set from orchestrator
        if filtered_domains is not None:
            self._save_domains_filtered(filtered_domains)
        else:
            self._save_domains(companies)
        
        # Save email results
        if email_results:
            self._save_emails(email_results)
        
        logger.success(f"Results saved to {self.output_dir}")
    
    def _save_companies(self, companies: List[Company]):
        """Save company data."""
        if self.config.format == "jsonl":
            self._save_companies_jsonl(companies)
        else:
            self._save_companies_txt(companies)
    
    def _save_companies_jsonl(self, companies: List[Company]):
        """Save companies as JSONL."""
        file_path = self.output_dir / f"{self.config.companies_file}.jsonl"
        
        with open(file_path, "w", encoding="utf-8") as f:
            for company in companies:
                json.dump(company.to_dict(), f, ensure_ascii=False)
                f.write("\\n")
        
        logger.info(f"Saved {len(companies)} companies to {file_path}")
    
    def _save_companies_txt(self, companies: List[Company]):
        """Save companies as text (legacy format)."""
        file_path = self.output_dir / f"{self.config.companies_file}.txt"
        
        with open(file_path, "w", encoding="utf-8") as f:
            for company in companies:
                f.write(str(company.to_dict()) + "\\n")
        
        logger.info(f"Saved {len(companies)} companies to {file_path}")
    
    def _save_domains(self, companies: List[Company]):
        """Save unique domains from orchestrator (already filtered)."""
        # Note: This should actually get domains from orchestrator.domains, not companies
        # But for now, extract only valid domains from companies
        from ..utils.domain import DomainResolver
        resolver = DomainResolver()
        
        domains = {
            company.domain for company in companies 
            if company.domain and resolver._is_valid_business_domain(company.domain)
        }
        
        file_path = self.output_dir / f"{self.config.domains_file}.txt"
        
        # Always overwrite, don't append
        if domains:
            with open(file_path, "w", encoding="utf-8") as f:
                for domain in sorted(domains):
                    f.write(domain + "\\n")
            logger.info(f"Saved {len(domains)} unique domains to {file_path}")
        else:
            # Write empty file if no domains
            with open(file_path, "w", encoding="utf-8") as f:
                pass
            logger.info(f"No valid business domains found - wrote empty domains file")
    
    def _save_domains_filtered(self, filtered_domains: set):
        """Save pre-filtered domains from orchestrator."""
        file_path = self.output_dir / f"{self.config.domains_file}.txt"
        
        # Always overwrite, don't append
        with open(file_path, "w", encoding="utf-8") as f:
            if filtered_domains:
                for domain in sorted(filtered_domains):
                    f.write(domain + "\\n")
                logger.info(f"Saved {len(filtered_domains)} filtered domains to {file_path}")
            else:
                # Empty file for no domains
                logger.info(f"No valid business domains found - wrote empty domains file")
    
    def _save_emails(self, email_results: List[EmailResult]):
        """Save email results."""
        if self.config.format == "jsonl":
            self._save_emails_jsonl(email_results)
        else:
            self._save_emails_txt(email_results)
    
    def _save_emails_jsonl(self, email_results: List[EmailResult]):
        """Save emails as JSONL."""
        file_path = self.output_dir / f"{self.config.emails_file}.jsonl"
        
        with open(file_path, "w", encoding="utf-8") as f:
            for result in email_results:
                json.dump(result.to_dict(), f, ensure_ascii=False)
                f.write("\\n")
        
        total_emails = sum(len(r.emails) for r in email_results if r.success)
        logger.info(f"Saved {len(email_results)} email results ({total_emails} total emails) to {file_path}")
    
    def _save_emails_txt(self, email_results: List[EmailResult]):
        """Save emails as text (legacy format)."""
        file_path = self.output_dir / f"{self.config.emails_file}.txt"
        
        with open(file_path, "w", encoding="utf-8") as f:
            for result in email_results:
                if result.success and result.emails:
                    emails_str = ",".join(result.emails)
                    f.write(f"{result.domain}: {emails_str}\\n")
        
        successful_results = [r for r in email_results if r.success and r.emails]
        total_emails = sum(len(r.emails) for r in successful_results)
        logger.info(f"Saved {len(successful_results)} domains with emails ({total_emails} total emails) to {file_path}")