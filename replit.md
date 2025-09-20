# Overview

This is a Python-based lead generation application that automates the process of finding businesses and their contact information. The system searches for companies using various providers (currently Yelp, with Google support planned), extracts business domains, and then discovers email addresses for those domains using email discovery services like Hunter.io. The application follows a modular pipeline architecture with separate components for search providers, domain resolution, and email discovery.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Components

The application follows a modular pipeline architecture with clearly separated concerns:

**CLI Interface**: Simple command-line interface (`leadgen/cli/main.py`) that orchestrates the entire lead generation process with configurable parameters like delay times, output directories, and location filtering.

**Orchestrator Pattern**: The `LeadOrchestrator` class manages the complete workflow, coordinating between different providers and finders while maintaining state and handling errors gracefully.

**Provider Architecture**: Pluggable search providers implement the `BaseProvider` interface to find companies. Currently supports Yelp with extensible design for additional providers like Google.

**Email Discovery System**: Modular email finders implement the `BaseFinder` interface. Currently supports Hunter.io with plans for Snov integration.

**Domain Resolution**: The `DomainResolver` utility extracts business domains from provider URLs, filtering out social media and platform domains to focus on actual business websites.

**Configuration Management**: File-based configuration system that loads API keys, search queries, and settings from text files in the `config/` directory, with environment variable overrides.

**State Management**: Persistent state tracking to enable resumable operations and avoid duplicate processing of companies, domains, and emails.

**Output Management**: Flexible output system supporting multiple formats (JSON, CSV, Excel) with structured data organization.

## Data Flow

1. **Configuration Loading**: API keys and settings loaded from config files
2. **Company Search**: Providers search for businesses based on configured queries
3. **Domain Extraction**: Business domains extracted from company URLs, excluding platform domains
4. **Email Discovery**: Email finders discover contact information for extracted domains
5. **Result Storage**: All data saved to output files with state tracking for resumability

## Error Handling & Resilience

The system implements comprehensive error handling with proxy rotation support, rate limiting awareness, and graceful degradation when services are unavailable. The state management system allows for interrupted processes to resume without losing progress.

# External Dependencies

## Search Providers

**Yelp Fusion API**: Primary business search provider requiring API key authentication. Used to discover businesses based on location and search terms.

**Google Custom Search API**: Planned integration for additional business discovery (currently commented out in codebase).

## Email Discovery Services

**Hunter.io API**: Primary email discovery service that finds email addresses associated with company domains. Requires API key and supports department filtering.

**Snov.io API**: Planned secondary email discovery service (infrastructure in place but not fully implemented).

## Data Storage

**File-based Storage**: JSON, CSV, and Excel output formats for results storage. No external database dependencies.

**State Persistence**: JSON-based state files for tracking processed companies, domains, and emails to enable resumable operations.

## HTTP Infrastructure

**Requests Library**: HTTP client for all API communications with built-in proxy support and error handling.

**Proxy Management**: Optional SOCKS5 proxy support for request routing (currently disabled due to missing dependencies).

## Development Tools

**OpenPyXL**: Excel file generation for structured output formatting.

**Standard Library**: Heavy reliance on Python standard library components (pathlib, json, csv, argparse) for core functionality.