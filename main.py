import random
import os
from config_loader import Config
from providers.yelp_provider import YelpProvider
from providers.google_provider import GoogleProvider
from finders.hunter_finder import HunterFinder
from finders.snov_finder import SnovFinder

class Main:
    def __init__(self):
        cfg = Config()
        self.providers = cfg.load_providers("./config/providers.txt")
        self.email_finders = cfg.load_email_finders("./config/email_finders.txt")
        self.proxies = cfg.load_proxies("./config/proxies.txt")
        self.queries = cfg.load_queries("./config/queries.txt")

        # Mapping: extendable
        self.provider_map = {
            "yelp": YelpProvider,
            "google": GoogleProvider,
        }
        self.finder_map = {
            "hunter": HunterFinder,
            "snov": SnovFinder,
        }

        # Results
        self.collected_companies = []
        self.collected_domains = set()

    def get_provider_instance(self, name, api_key):
        if name.lower() not in self.provider_map:
            raise ValueError(f"Unknown provider: {name}")
        return self.provider_map[name.lower()](api_key)

    def get_finder_instance(self, name, api_key):
        if name.lower() not in self.finder_map:
            raise ValueError(f"Unknown email finder: {name}")
        return self.finder_map[name.lower()](api_key)

    def rotate_proxy(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    def run_providers(self):
        for name, api_key in self.providers.items():
            try:
                provider = self.get_provider_instance(name, api_key)

                for query in self.queries:
                    proxy = self.rotate_proxy()
                    print(f"[{name.upper()}] Searching '{query}' with proxy {proxy}")

                    results = provider.search(query, proxy=proxy)
                    for r in results:
                        self.collected_companies.append(r)
                        if "url" in r and r["url"]:
                            domain = self.extract_domain(r["url"])
                            if domain:
                                self.collected_domains.add(domain)

            except Exception as e:
                print(f"[PROVIDER ERROR] {name}: {e}")
                continue

        self.save_results("companies.txt", [str(c) for c in self.collected_companies])
        self.save_results("domains.txt", list(self.collected_domains))

    def run_email_finders(self):
        for name, api_key in self.email_finders.items():
            try:
                finder = self.get_finder_instance(name, api_key)

                for domain in self.collected_domains:
                    proxy = self.rotate_proxy()
                    print(f"[{name.upper()}] Finding emails for '{domain}' with proxy {proxy}")
                    emails = finder.find(domain, proxy=proxy)
                    if emails:
                        self.save_results("emails.txt", [f"{domain}: {','.join(emails)}"])

            except Exception as e:
                print(f"[FINDER ERROR] {name}: {e}")
                continue



    @staticmethod
    def extract_domain(url):
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return None

    @staticmethod
    def save_results(filename, lines):
        os.makedirs("output", exist_ok=True)
        path = os.path.join("output", filename)
        with open(path, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

    def run(self):
        print(f"providers: {self.providers}")
        print(f"email_finders: {self.email_finders}")
        print(f"proxies: {self.proxies}")
        print(f"queries: {self.queries}")

        print("\n=== Running Providers ===")
        self.run_providers()

        print("\n=== Running Email Finders ===")
        self.run_email_finders()


if __name__ == "__main__":
    Main().run()
