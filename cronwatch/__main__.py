"""Allow running cronwatch as a module: python -m cronwatch."""

import sys
from cronwatch.cli import main

if __name__ == "__main__":
    sys.exit(main())
