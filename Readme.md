# Email Finder Application

## Overview
This is a Python-based email finder application that searches for companies using various providers (Yelp, Google) and then finds email addresses for those companies using email discovery services (Hunter, Snov). The application is designed to help with lead generation and business intelligence.

## Recent Changes
- **September 20, 2025**: Fresh GitHub import setup in Replit environment
  - Installed Python 3.11 and all required dependencies via pip
  - Created config directory with template configuration files
  - Set up "Email Finder CLI" workflow for console-based execution
  - Validated application structure and core functionality
  - Application ready for use with valid API keys

## Project Architecture

### Main Components
- **main.py**: Entry point and orchestration logic
- **config_loader.py**: Handles loading configuration from text files
- **providers/**: Search providers that find companies (Yelp, Google)
- **finders/**: Email discovery services (Hunter, Snov)
- **config/**: Configuration files for API keys, queries, and settings
- **output/**: Generated results files

### Configuration Files
- `config/providers.txt`: API keys for search providers (format: provider=API_KEY)
- `config/email_finders.txt`: API keys for email finders (format: finder=API_KEY)
- `config/queries.txt`: Search queries, one per line
- `config/proxies.txt`: Proxy configurations (currently disabled)

### Workflow
1. Load configuration from text files
2. Run search providers to find companies based on queries
3. Extract domains from company URLs
4. Use email finders to discover emails for those domains
5. Save results to output files

### Current Status
- ✅ Python 3.11 environment configured in Replit
- ✅ All dependencies installed via pip
- ✅ Console workflow "Email Finder CLI" configured and tested
- ✅ Configuration files created with placeholder API keys
- ✅ Application structure validated and ready for use
- ⚠️ Requires valid API keys for Yelp and Hunter services to function

### Known Limitations
- SOCKS proxy support disabled (requires additional dependencies)
- Google provider requires valid API key and custom search engine ID
- Some type annotation warnings remain but don't affect functionality

## Setup Instructions
1. **Add API Keys**: Edit the configuration files to add your real API keys:
   - `config/providers.txt`: Replace `test_yelp_key_placeholder` with your Yelp API key
   - `config/email_finders.txt`: Replace `test_hunter_key_placeholder` with your Hunter API key

2. **Customize Search Queries**: Edit `config/queries.txt` to add your own search terms

3. **Run the Application**: The "Email Finder CLI" workflow will automatically execute the pipeline

## Usage
The application runs via the "Email Finder CLI" workflow. Results are saved in the `output/` directory:
- `companies.txt`: Found company information
- `domains.txt`: Extracted domain names  
- `emails.txt`: Discovered email addresses

## User Preferences
- Console-based application (no frontend required)
- Extensible provider and finder architecture
- Configuration via text files for easy management


## Issues and To-Dos
- check if the old output files contants data, show warning as to not to loose last run
- Remove the existing companies from the old data
- should be stateful. when you run the cli again, should remeber last run, so you dont process same company, domain twice if alrady in output.dir
- Proxy not rotating, proxy should be rotatating per http request not per provider
- when a provider,domain_finder, or email_finder dies, doesnt move to the next one. some popular error message for when hunter api_limit issue it returns status 429. when either yelp, or hunter gets api issues, should move to the next one inline