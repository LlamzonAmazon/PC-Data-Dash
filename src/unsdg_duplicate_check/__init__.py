"""
UN SDG duplicate checker: detects collision duplicates in the UN SDG interim CSV.

Collision duplicate = same dimension values (country, year, age, sex, location, nature)
but different numeric 'value', indicating mislabeled disaggregations (e.g. age 10-14
labeled as 15-49). Reporting is per indicator and series_code.
"""

from src.unsdg_duplicate_check.collision_check import (
    check_unsdg_collision_duplicates,
    run_unsdg_duplicate_check,
)

__all__ = [
    "check_unsdg_collision_duplicates",
    "run_unsdg_duplicate_check",
]
