"""Config loader to load all configs"""
from pathlib import Path
import os


class Config:
    def __init__(self):
        self.providers = self.load_providers("./config/providers.txt") 
        self.email_finders = self.load_email_finders("./config/email_finders.txt") 
        self.proxies = self.load_proxies("./config/proxies.txt") 
        self.queries = self.load_queries("./config/queries.txt") 

        
    def load_proxies(self, file_path:str):
        """
        Load proxies from a txt file.
        Format: one proxy per line.
        Example:
            http://user:pass@ip:port
            socks5://127.0.0.1:9050
        """
        return self.__read_lines(file_path)
    
    def load_email_finders(self, file_path):
        """
        Load email finder accounts from a txt file.
        Format: finder_name=API_KEY
        Example:
            hunter=HUNTER_API_KEY_1
            snov=SNOV_API_KEY_1
        """
        return self.load_providers(file_path)
        
    def load_queries(self, file_path:str):
        """
        Load search queries from a txt file.
        Format: one query per line.
        Example:
            coffee shops new york
            law firms in los angeles
        """
        return self.__read_lines(file_path)
    
    def load_providers(self,file_path: str):
        """
        Load search/email providers from a txt file.
        Format: provider_name=API_KEY
        Example:
            yelp=YOUR_YELP_API_KEY
            google=YOUR_GOOGLE_API_KEY
        Returns:
            dict like {"yelp": "API_KEY", "google": "API_KEY"}
        """
        
        providers = {}
        for line in self.__read_lines(file_path):
            if "=" not in line:
                raise ValueError(f"Invalid provider line: {line}")
            name, key = line.split("=")
            providers[name.strip()] = key.strip()

        return providers
        
    def __read_lines(self,file_path:str) :
        """
        Read a .txt file, strip whitespace, ignore empty lines and comments (#).
        """
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        with path.open("r", encoding="utf-8") as f:
            lines = [ ]
            for line in f.readlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                lines.append(line)
            return lines
        
        
    if __name__ == "__main__":
        # Example usage (for debugging)
        base = "config"

        print("Providers:", load_providers(os.path.join(base, "providers.txt")))
        print("Email Finders:", load_email_finders(os.path.join(base, "email_finders.txt")))
        print("Proxies:", load_proxies(os.path.join(base, "proxies.txt")))
        print("Queries:", load_queries(os.path.join(base, "queries.txt")))