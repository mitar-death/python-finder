"""Configuration loader with validation and error handling."""
import os
from pathlib import Path
from typing import Dict, List
from .models import AppConfig

from leadgen.utils.logging import logger
class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class ConfigLoader:
    """Loads and validates configuration from files."""
    
    def __init__(self, config_dir: str = "config", output_dir ="output"):
        self.config_dir = Path(config_dir)
        self.output_dir = Path(output_dir)
    
    def load_config(self) -> AppConfig:
        """Load complete application configuration."""
        config = AppConfig.from_env()
        
        # Load from files, with file values taking precedence over defaults
        # but environment variables taking precedence over file values
        file_providers = self._load_providers("providers.txt")
        file_finders = self._load_providers("email_finders.txt")
        
        # Merge with environment overrides
        for name, key in file_providers.items():
            if name not in config.providers:  # Don't override env vars
                config.providers[name] = key
                
        for name, key in file_finders.items():
            if name not in config.email_finders:  # Don't override env vars
                config.email_finders[name] = key
        
        config.proxies = self._load_proxies("proxies.txt")
        config.queries = self._load_queries("queries.txt")
        
        self._validate_config(config)
        return config
    
    def _load_providers(self, filename: str) -> Dict[str, str]:
        """Load provider configuration from file."""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            return {}
            
        providers = {}
        try:
            lines = self._read_lines(file_path)
            for line_num, line in enumerate(lines, 1):
                if "=" not in line:
                    raise ConfigurationError(
                        f"{filename}:{line_num}: Invalid format. "
                        f"Expected 'provider=API_KEY', got '{line}'"
                    )
                
                name, key = line.split("=", 1)
                name, key = name.strip(), key.strip()
                
                if not name or not key:
                    raise ConfigurationError(
                        f"{filename}:{line_num}: Empty provider name or API key"
                    )
                
                providers[name] = key
                
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Error reading {filename}: {e}")
            
        return providers
    
    def _load_proxies(self, filename: str) -> List[str]:
        """Load proxy configuration from file."""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            return []
            
        try:
            return self._read_lines(file_path)
        except Exception as e:
            raise ConfigurationError(f"Error reading {filename}: {e}")
    
    def _load_searchable_domains(self, filename):
        """Load searchable domains from file."""
        file_path = self.config_dir / filename

        if not file_path.exists():
            return []

        try:
            return self._read_lines(file_path)
        except Exception as e:
            raise ConfigurationError(f"Error reading searchable_domains.txt: {e}")
    def _load_queries(self, filename: str) -> List[str]:
        """Load search queries from file."""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            raise ConfigurationError(
                f"Required file {filename} not found. "
                f"Please create it with one search query per line."
            )
            
        try:
            queries = self._read_lines(file_path)
            if not queries:
                raise ConfigurationError(
                    f"{filename} is empty. Please add at least one search query."
                )
            return queries
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Error reading {filename}: {e}")
        
    def _load_companies(self, filename: str) -> List[str]:
        """Load companies from file."""
        file_path = self.output_dir / filename

        if not file_path.exists():
            raise ConfigurationError(
                f"Required file {filename} not found. "
                f"Please create it with one company name per line."
            )

        try:
            companies = self._read_lines(file_path)
            if not companies:
                raise ConfigurationError(
                    f"{filename} is empty. Please add at least one company name."
                )
            return companies
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Error reading {filename}: {e}")
    
    def _read_lines(self, file_path: Path) -> List[str]:
        """Read non-empty, non-comment lines from file."""
        lines = []
        
        with file_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                    
                lines.append(line)
        
        return lines
    
    def _validate_config(self, config: AppConfig) -> None:
        """Validate the loaded configuration."""
        # Check that we have at least one provider or email finder
        if not config.providers and not config.email_finders:
            raise ConfigurationError(
                "No providers or email finders configured. "
                "Please add API keys to providers.txt or email_finders.txt"
            )
        
        # Validate queries
        if not config.queries:
            raise ConfigurationError(
                "No search queries configured. "
                "Please add queries to queries.txt"
            )
            
        # Check for required Google CX if Google provider is enabled
        if "google" in config.providers and not config.google_cx:
            if not os.getenv("GOOGLE_CX"):
                print(
                    "Warning: Google provider enabled but no Custom Search Engine ID (CX) configured. "
                    "Set GOOGLE_CX environment variable or update google_cx in config."
                )