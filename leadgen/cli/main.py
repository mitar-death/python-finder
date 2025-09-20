"""Simple CLI interface for lead generation."""
import sys
import argparse
from pathlib import Path
from typing import List, Tuple
from leadgen.utils.proxy import ProxyManager
from ..config.loader import ConfigLoader, ConfigurationError
from ..orchestrator import LeadOrchestrator
from ..utils.logging import logger
from ..io.storage import OutputManager
from ..utils.state import StateStore


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
    
    # Mode selection - mutually exclusive
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume from previous run (default - skips already processed data)"
    )
    mode_group.add_argument(
        "--fresh",
        action="store_true",
        help="Start fresh run (clears existing output data after confirmation)"
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


def check_output_safety(output_dir: str, output_config) -> Tuple[bool, List[str]]:
    """Check if output files exist and return file info."""
    output_path = Path(output_dir)
    existing_files = []
    
    if not output_path.exists():
        return True, []
    
    # Check for existing output files
    file_extensions = ["txt", "csv", "jsonl", "json", "xlsx"]
    file_bases = [output_config.companies_file, output_config.domains_file, output_config.emails_file]
    
    for base in file_bases:
        for ext in file_extensions:
            file_path = output_path / f"{base}.{ext}"
            if file_path.exists() and file_path.stat().st_size > 0:
                file_size = file_path.stat().st_size
                size_str = f"{file_size:,} bytes"
                if file_size > 1024:
                    size_str = f"{file_size/1024:.1f} KB"
                if file_size > 1024*1024:
                    size_str = f"{file_size/(1024*1024):.1f} MB"
                    
                existing_files.append(f"{file_path.name} ({size_str})")
                
    return len(existing_files) == 0, existing_files


def confirm_fresh_run(existing_files: List[str]) -> bool:
    """Ask user confirmation for fresh run that will clear data."""
    logger.warning("⚠️  EXISTING OUTPUT FILES DETECTED:")
    for file_info in existing_files:
        logger.warning(f"   📄 {file_info}")
        
    logger.warning("\n🔥 Running with --fresh will PERMANENTLY DELETE this data!")
    logger.info("\nOptions:")
    logger.info("  • Continue with --fresh (DELETE existing data)")
    logger.info("  • Cancel and run with --resume (PRESERVE existing data)")
    
    while True:
        try:
            response = input("\nContinue with fresh run? [y/N]: ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['', 'n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
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
        
        # Check for existing output files and handle mode selection
        is_safe, existing_files = check_output_safety(args.output_dir, config.output)
        
        if not is_safe and existing_files:
            if args.fresh:
                # Fresh mode - ask for confirmation before deleting
                if not confirm_fresh_run(existing_files):
                    logger.info("Operation cancelled by user")
                    sys.exit(0)
                logger.info("🔥 Starting fresh run - existing data will be cleared")
            else:
                # Resume mode (default) - show info about existing data
                logger.info("📁 Existing output files detected - running in RESUME mode:")
                for file_info in existing_files:
                    logger.info(f"   📄 {file_info}")
                logger.info("   ℹ️  Already processed data will be skipped")
                logger.info("   💡 Use --fresh to start over or --resume to continue")
        
        # Initialize StateStore
        state_store = StateStore(args.output_dir, config.output)
        
        if args.fresh and existing_files:
            # Clear existing state and files
            state_store.clear_state()
            # Remove existing output files
            output_path = Path(args.output_dir)
            file_extensions = ["txt", "csv", "jsonl", "json", "xlsx"]
            file_bases = [config.output.companies_file, config.output.domains_file, config.output.emails_file]
            
            # Delete specific output files
            for base in file_bases:
                for ext in file_extensions:
                    file_path = output_path / f"{base}.{ext}"
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"🗑️  Deleted {file_path.name}")
            
            # Also clear .state directory
            state_dir = output_path / ".state"
            if state_dir.exists():
                import shutil
                shutil.rmtree(state_dir)
                logger.info("🗑️  Cleared state cache")
            
            logger.info("🗑️  Fresh run: all existing output data cleared")
        else:
            # Load existing state for resume mode
            logger.info("📖 Loading existing state for resume...")
            state_store.load_from_output()
            stats = state_store.get_stats()
            if any(stats.values()):
                logger.info(f"   📊 Found: {stats['companies']} companies, {stats['domains']} domains, {stats['emails']} emails")
        
        # Create orchestrator and run with state store
        orchestrator = LeadOrchestrator(config, state_store)
        orchestrator.run_full_pipeline()
        
        # Save results
        logger.info("Saving results...")
        output_manager = OutputManager(config.output)
        output_manager.save_results(
            companies=orchestrator.companies,
            email_results=orchestrator.email_results,
            filtered_domains=orchestrator.domains  # Pass the filtered domains
        )
        
        # Final state save
        if state_store:
            state_store.save_state()
            logger.info("💾 State saved successfully")
        
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