"""Run the full lead generation pipeline with the new CLI."""
import sys
import os

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from leadgen.cli.main import main
    print("Running full lead generation pipeline...")
    
    # Set up arguments for full run
    sys.argv = ['run_leadgen.py', '--verbose', '--delay', '5']
    main()
    
except Exception as e:
    print(f"Error running new CLI: {e}")
    import traceback
    traceback.print_exc()