"""Configuration models."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import os


@dataclass
class DelayConfig:
    """Configuration for delays between operations."""
    provider_delay: float = 0.0  # seconds between provider requests
    finder_delay: float = 1.0   # seconds before starting email finding
    domain_delay: float = 5.0    # seconds between domain requests
    request_delay: float = 1.0   # seconds between individual requests
    
    
@dataclass 
class ProxyConfig:
    """Configuration for proxy settings."""
    enabled: bool = True
    rotation: str = "round_robin"  # round_robin, random
    timeout: float = 10.0


@dataclass
class OutputConfig:
    """Configuration for output settings."""
    format: str = "jsonl"  # jsonl, csv, txt
    directory: str = "output"
    companies_file: str = "companies"
    domains_file: str = "domains" 
    emails_file: str = "emails"

@dataclass
class AppConfig:
    """Main application configuration."""
    providers: Dict[str, str] = field(default_factory=dict)
    email_finders: Dict[str, str] = field(default_factory=dict)
    proxies: List[str] = field(default_factory=list)
    queries: List[str] = field(default_factory=list)
    run_email_finder_alone: bool = True
    
    # Sub-configurations
    delays: DelayConfig = field(default_factory=DelayConfig)
    proxy_config: ProxyConfig = field(default_factory=ProxyConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # Provider-specific settings
    yelp_location: str = "United States"
    yelp_limit: int = 5
    google_cx: str = ""
    google_limit: int = 5
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create config with environment variable overrides."""
        config = cls()
        
        # Override with environment variables if present
        if hunter_key := os.getenv("HUNTER_API_KEY"):
            config.email_finders["hunter"] = hunter_key
        if snov_key := os.getenv("SNOV_API_KEY"):
            config.email_finders["snov"] = snov_key
        if yelp_key := os.getenv("YELP_API_KEY"):
            config.providers["yelp"] = yelp_key
        if google_key := os.getenv("GOOGLE_API_KEY"):
            config.providers["google"] = google_key
        if google_cx := os.getenv("GOOGLE_CX"):
            config.google_cx = google_cx
            
        return config