#!/usr/bin/env python3
"""
Initialize Development Safety MCP Server

Sets up the development environment and validates installation.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        return False
    print(f"OK: Python {sys.version.split()[0]} detected")
    return True


def check_git_installed():
    """Check if git is available"""
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        print("OK: Git is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: Git is not available - some features may not work")
        return False


def create_config_directory():
    """Create user config directory"""
    config_dir = Path.home() / ".dev-safety"
    config_dir.mkdir(exist_ok=True)
    print(f"OK: Config directory created: {config_dir}")
    return config_dir


def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("OK: Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("ERROR: Failed to install dependencies")
        return False


def run_basic_test():
    """Run a basic functionality test"""
    print("Running basic functionality test...")
    try:
        # Import the main server class
        sys.path.insert(0, 'src')
        from mcp_server import DevSafetyMCP
        
        # Try to initialize
        server = DevSafetyMCP()
        print("OK: MCP Server initialization successful")
        return True
    except Exception as e:
        print(f"ERROR: Basic test failed: {e}")
        return False


def main():
    """Main initialization routine"""
    print("Development Safety MCP Server - Initialization")
    print("=" * 60)
    
    success = True
    
    # Check requirements
    print("\nChecking Requirements:")
    success &= check_python_version()
    check_git_installed()  # Git is optional
    
    # Setup
    print("\nSetting Up Environment:")
    config_dir = create_config_directory()
    success &= install_dependencies()
    
    # Validate
    print("\nValidating Installation:")
    success &= run_basic_test()
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: Initialization completed successfully!")
        print("\nNext Steps:")
        print("1. Run example workflow: python examples/basic_workflow_example.py")
        print("2. Run tests: python -m pytest tests/")
        print("3. Start MCP server: python cli.py server")
        print("\nDocumentation: See README.md for detailed usage instructions")
    else:
        print("ERROR: Initialization failed. Please resolve the issues above.")
        sys.exit(1)


if __name__ == '__main__':
    main()