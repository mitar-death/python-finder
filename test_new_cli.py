"""Test script for the new CLI structure."""
import sys
import os

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from leadgen.cli.main import main
    print("✓ New CLI structure imported successfully")
    
    # Test with validate config flag
    sys.argv = ['test_new_cli.py', '--validate-config']
    main()
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    # Fall back to old main.py if new structure not ready
    print("Falling back to old structure...")
    import subprocess
    result = subprocess.run([sys.executable, 'main.py'], capture_output=True, text=True)
    print("Old CLI output:")
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
except Exception as e:
    print(f"✗ Error testing new CLI: {e}")
    # Fall back to old main.py
    print("Falling back to old structure...")
    import subprocess
    result = subprocess.run([sys.executable, 'main.py'], capture_output=True, text=True)
    print("Old CLI output:")
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)