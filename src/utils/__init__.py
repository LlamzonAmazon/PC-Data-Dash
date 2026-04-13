"""
Shared project-wide utilities.

Modules:
  helpers        — project_root(), setup_logger(), ensure_dir()
  country_names  — canonical country display names and continent/region mapping
  collision_check — UN SDG duplicate detection
  csv_check      — interim CSV analysis tool
"""

from src.utils.helpers import project_root, setup_logger, ensure_dir
from src.utils.country_names import (
    COUNTRY_NAMES,
    COUNTRY_REGIONS,
    REGION_NAMES,
    get_canonical_name,
    get_region,
    get_region_name,
)

__all__ = [
    "project_root",
    "setup_logger",
    "ensure_dir",
    "COUNTRY_NAMES",
    "COUNTRY_REGIONS",
    "REGION_NAMES",
    "get_canonical_name",
    "get_region",
    "get_region_name",
]
