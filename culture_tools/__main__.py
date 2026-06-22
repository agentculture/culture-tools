"""Entry point for ``python -m culture_tools``."""

from __future__ import annotations

import sys

from culture_tools.cli import main

if __name__ == "__main__":
    sys.exit(main())
