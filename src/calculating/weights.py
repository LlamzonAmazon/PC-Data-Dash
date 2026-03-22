from __future__ import annotations

from typing import Dict

from .hierarchy import INDICATORS, list_sectors_for_domain, list_subsectors_for_sector


def _equal_weights(keys) -> Dict[str, float]:
    keys = list(keys)
    if not keys:
        return {}
    w = 1.0 / len(keys)
    return {k: w for k in keys}


# Default: equal weighting at every level, derived from the hierarchy.
# These are intended to be edited by the user to override defaults, 
# Uses a dictionary to override weights for a specific domain, sector, or subsector
DOMAIN_WEIGHTS: Dict[str, Dict[str, float]] = {
    "1": _equal_weights(list_sectors_for_domain("1")),
}


SECTOR_WEIGHTS: Dict[str, Dict[str, float]] = {
    sector_id: _equal_weights(list_subsectors_for_sector(sector_id))
    for sector_id in list_sectors_for_domain("1")
}

SUBSECTOR_WEIGHTS: Dict[str, Dict[str, float]] = {}
for meta in INDICATORS.values():
    subsector_weights = SUBSECTOR_WEIGHTS.setdefault(meta.subsector_id, {})
    subsector_weights.setdefault(meta.indicator_id, 0.0)

for subsector_id, mapping in SUBSECTOR_WEIGHTS.items():
    SUBSECTOR_WEIGHTS[subsector_id] = _equal_weights(mapping.keys())


# =============================================================================
# INDICATOR-SPECIFIC COMPONENT WEIGHTS (3.d.1 / IHR)
# =============================================================================
# By default, IHR_COMPONENT_WEIGHTS is empty, which tells the function below 
# to use equal weighting (e.g., 1/13 for each of IHR01-IHR13).
IHR_COMPONENT_WEIGHTS: Dict[str, float] = {}


def get_ihr_component_weights(class_codes) -> Dict[str, float]:
    """
    Build a weight mapping for the provided `class_codes` using
    `IHR_COMPONENT_WEIGHTS` with sensible defaults.
    """
    codes = [c for c in class_codes if c is not None and str(c) != ""]
    unique_codes = list(dict.fromkeys(map(str, codes)).keys())
    if not unique_codes:
        return {}

    specified = {c: float(IHR_COMPONENT_WEIGHTS[c]) for c in unique_codes if c in IHR_COMPONENT_WEIGHTS}
    unspecified = [c for c in unique_codes if c not in specified]

    specified_sum = sum(specified.values())
    remaining = 1.0 - specified_sum

    # If remaining weight is not positive, fall back to equal weights across present codes.
    if remaining <= 0 or (specified_sum <= 0 and not unspecified):
        return _equal_weights(unique_codes)

    weights = dict(specified)
    if unspecified:
        equal_missing = remaining / len(unspecified)
        for c in unspecified:
            weights[c] = equal_missing
    else:
        # If everything is specified but does not sum to 1.0, normalize.
        total = sum(weights.values())
        if total > 0 and abs(total - 1.0) > 1e-9:
            weights = {k: v / total for k, v in weights.items()}

    return weights

# =============================================================================
# MANUAL WEIGHT OVERRIDES
# =============================================================================
# Use the examples below to prioritize specific areas. 
# Ensure that the values within a single dictionary sum to 1.0.

# EXAMPLE: Changing Sector weights within a Domain
# To make Healthcare (1.1) 70% and Agriculture (1.2) 30% of Domain 1:
# DOMAIN_WEIGHTS["1"] = {"1.1": 0.7, "1.2": 0.3}

# EXAMPLE: Changing Subsector weights within a Sector
# To prioritize Infectious Disease (1.1.2) at 50% within Healthcare (1.1):
# SECTOR_WEIGHTS["1.1"] = {
#     "1.1.1": 0.1, 
#     "1.1.2": 0.5, 
#     "1.1.3": 0.1, 
#     "1.1.4": 0.1, 
#     "1.1.5": 0.1, 
#     "1.1.6": 0.1
# }

# EXAMPLE: Changing Indicator weights within a Subsector (e.g., Nutrition 1.1.4)
# To make Stunting (2.2.1) 80% of the Nutrition score:
# SUBSECTOR_WEIGHTS["1.1.4"] = {
#     "2.2.1": 0.8, 
#     "2.2.2": 0.1, 
#     "2.2.3": 0.1
# }

# =============================================================================
# (3.d.1 / IHR) OVERRIDE WEIGHTS
# =============================================================================

# EXAMPLE: Prioritize specific IHR components for indicator 3.d.1
# Make Laboratory (IHR05) 30% of the score; others will split the remaining 70%:
# IHR_COMPONENT_WEIGHTS.update({"IHR05": 0.30})

