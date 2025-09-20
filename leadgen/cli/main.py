"""Simple CLI interface for lead generation."""
import sys
import argparse
from pathlib import Path
from leadgen.utils.proxy import ProxyManager
from ..config.loader import ConfigLoader, ConfigurationError
from ..orchestrator import LeadOrchestrator
from ..utils.logging import logger
from ..io.storage import OutputManager


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Lead generation CLI tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--config-dir",
        default="config",
        help="Configuration directory (default: config)"
    )
    
    parser.add_argument(
        "--location",
        default="United States",
        help="Location of this business, including address, city, state, zip code and country."
    )
    parser.add_argument(
        "--hunter-department",
        default="United States",
        help="Get only email addresses for people working in the selected department(s"
    )
    
    parser.add_argument(
        "--output-dir", 
        default="output",
        help="Output directory (default: output)"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        help="Override finder delay in seconds"
    )
    
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration and exit"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser


def validate_config_command(config_dir: str) -> bool:
    """Validate configuration and show status."""
    try:
        loader = ConfigLoader(config_dir)
        config = loader.load_config()
        
        logger.success("Configuration is valid")
        logger.info(f"Providers: {list(config.providers.keys())}")
        logger.info(f"Email finders: {list(config.email_finders.keys())}")
        logger.info(f"Queries: {len(config.queries)} configured")
        logger.info(f"Proxies: {len(config.proxies)} configured")
        
        return True
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.level = "DEBUG"
    
    # Validate config if requested
    if args.validate_config:
        success = validate_config_command(args.config_dir)
        sys.exit(0 if success else 1)
        
   
     
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        loader = ConfigLoader(args.config_dir)
        config = loader.load_config()
        
         #NOTE: check if the old output files contants data, show warning as to not to loose last run
         
        # if config.output_dir:
        #     pass
            # walk the output dir here
            # show prompt ask to delete files
    
        
        # Override delay if specified
        if args.delay is not None:
            config.delays.finder_delay = args.delay
            config.delays.domain_delay = args.delay
            logger.info(f"Using custom finder and domain delay: {args.delay}s")
        
        # Update output directory
        config.output.directory = args.output_dir
        
        if location := args.location:
            config.location = location
            logger.info(f"Using custom location: {location}")
            
        if hunter_department := args.hunter_department:
            config.hunter_department = hunter_department
            logger.info(f"Using custom hunter_department: {hunter_department}")
        
        
        # Create orchestrator and run
        orchestrator = LeadOrchestrator(config)
        orchestrator.run_full_pipeline()
        
        
        
        # Save results
        logger.info("Saving results...")
        output_manager = OutputManager(config.output)
        output_manager.save_results(
            companies=orchestrator.companies,
            email_results=orchestrator.email_results,
            filtered_domains=orchestrator.domains  # Pass the filtered domains
        )
        
        logger.success("Lead generation completed successfully")
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Run with --validate-config to check your configuration")
        sys.exit(1)
        
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()