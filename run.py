"""Click to run the Arcaea Speed Tool.

Make sure songs/ and config.toml are in this folder before running.
"""

import os
import sys

# Ensure the script runs from its own directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()
