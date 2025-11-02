"""Main entry point for MacroManager application."""

from macro_manager.ui import main
import sys
from pathlib import Path

# Add src to path to enable imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


if __name__ == "__main__":
    main()
