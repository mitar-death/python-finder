# Email Finder Application - Replit Project

## Overview
Lead generation CLI application that searches for companies using Yelp/Google providers and finds email addresses using Hunter/Snov services.

## Recent Changes
- **September 20, 2025**: Fresh GitHub import setup completed
  - Installed Python 3.11 and all required dependencies
  - Created config directory with template configuration files
  - Set up console workflow for CLI execution
  - Application structure validated and ready for use

## User Preferences
- Console-based CLI application (no frontend)
- Extensible provider and finder architecture 
- Configuration via text files for easy API key management
- Automated workflow execution

## Project Architecture
- **Language**: Python 3.11
- **Dependencies**: requests, typer, rich, loguru, pydantic, pyyaml, tenacity, openpyxl
- **Structure**: Modular design with providers, finders, config management
- **Workflow**: "Email Finder CLI" console application
- **Configuration**: Text-based config files in `/config` directory

## Current Status
- ✅ Environment fully configured and tested
- ✅ All dependencies installed via pip
- ✅ Console workflow configured
- ✅ Configuration template files created
- ⚠️ Requires valid API keys to function properly

## Next Steps for User
1. Add real API keys to config files (currently has placeholders)
2. Customize search queries in config/queries.txt
3. Run the workflow to execute lead generation pipeline