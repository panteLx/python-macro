"""Main entry point for MacroManager application."""

from macro_manager.ui import main
import sys
import os
from pathlib import Path

# Get the absolute path to the script's directory
# This ensures the app works correctly even when run as administrator
script_dir = Path(__file__).resolve().parent

# Change working directory to script directory
os.chdir(script_dir)

# Add src to path to enable imports
src_path = script_dir / "src"
sys.path.insert(0, str(src_path))


if __name__ == "__main__":
    main()
