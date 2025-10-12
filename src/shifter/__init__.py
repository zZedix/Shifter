"""Shifter – network tunnel orchestration toolkit."""

from __future__ import annotations

from importlib import metadata

__all__ = ["__version__"]

try:
    __version__ = metadata.version("shifter")
except metadata.PackageNotFoundError:  # pragma: no cover - during local dev
    __version__ = "0.0.0"
