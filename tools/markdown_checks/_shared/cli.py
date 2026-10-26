"""Console behavior shared by the executable checkers."""

from __future__ import annotations

import sys


def configure_stdio() -> None:
    """Emit readable Chinese diagnostics on Windows and redirected streams."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")
