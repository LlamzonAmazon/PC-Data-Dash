"""
Backward-compatible re-export shim.

The canonical implementation now lives in src/utils/collision_check.py.
All existing imports from this module continue to work without changes.
"""

from src.utils.collision_check import (  # noqa: F401
    load_unsdg_csv,
    get_configured_indicators,
    check_unsdg_collision_duplicates,
    run_unsdg_duplicate_check,
    VALUE_COL,
    SERIES_COL,
)

__all__ = [
    "load_unsdg_csv",
    "get_configured_indicators",
    "check_unsdg_collision_duplicates",
    "run_unsdg_duplicate_check",
    "VALUE_COL",
    "SERIES_COL",
]

if __name__ == "__main__":
    run_unsdg_duplicate_check()
