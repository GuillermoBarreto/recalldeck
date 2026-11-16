"""Run recalldeck as a module: python -m recalldeck ..."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
