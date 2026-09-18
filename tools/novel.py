#!/usr/bin/env python3
"""Entry point for the novel engine. See `--help`."""
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from novelkit.cli import main  # noqa: E402

if __name__ == "__main__":
    # Play nicely with `| head` and friends.
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        pass
    raise SystemExit(main())
