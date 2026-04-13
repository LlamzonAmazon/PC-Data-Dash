"""
Shared project-wide utility helpers.

Previously located at src/pipeline/utils.py — that module now re-exports
everything from here for backward compatibility.
"""

import sys
import logging
from pathlib import Path
from typing import Union


def setup_logger(name: str = "pc-data-dash") -> logging.Logger:
    """Creates a simple logger that prints messages to the console."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def ensure_dir(path: Union[str, Path]) -> None:
    """Creates a folder (and parents) if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def project_root() -> Path:
    """
    Returns the absolute path to the project root.
    Both src/utils/ and src/pipeline/ are two levels below root,
    so parents[2] is correct from either location.
    """
    return Path(__file__).resolve().parents[2]
