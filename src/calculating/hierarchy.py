from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class IndicatorMeta:
    indicator_id: str
    series_code: str
    name: str
    domain_id: str
    sector_id: str
    subsector_id: str


# Core hierarchy for indicators that exist in the UN SDG interim file and
# have explicit scoring rules in the scoring README.
INDICATORS: Dict[str, IndicatorMeta] = {
    # Domain 1 - Impact
    # Sector 1.1 - Healthcare
    # 1.1.1 Resilient primary healthcare systems
    "SH_ACS_UNHC_25": IndicatorMeta(
        indicator_id="3.8.1",
        series_code="SH_ACS_UNHC_25",
        name="Universal health coverage (UHC) service coverage index",
        domain_id="1",
        sector_id="1.1",
        subsector_id="1.1.1",
    ),
    # 1.1.2 Infectious disease control
    "SH_TBS_INCD": IndicatorMeta(
        indicator_id="3.3.2",
        series_code="SH_TBS_INCD",
        name="Tuberculosis incidence",
        domain_id="1",
        sector_id="1.1",
        subsector_id="1.1.2",
    ),
    "SH_STA_MALR": IndicatorMeta(
        indicator_id="3.3.3",
        series_code="SH_STA_MALR",
        name="Malaria incidence per 1,000 population at risk",
        domain_id="1",
        sector_id="1.1",
        subsector_id="1.1.2",
    ),
    # 1.1.3 Maternal, newborn, and child health
    "SH_STA_MORT": IndicatorMeta(
        indicator_id="3.1.1",
        series_code="SH_STA_MORT",
        name="Maternal mortality ratio",
        domain_id="1",
        sector_id="1.1",
        subsector_id="1.1.3",
    ),
    "SH_DYN_MORT": IndicatorMeta(
        indicator_id="3.2.1",
        series_code="SH_DYN_MORT",
        name="Under-five mortality rate",
        domain_id="1",
        sector_id="1.1",
        subsector_id="1.1.3",
    ),
    # 1.1.4 Nutrition
    "SH_STA_STNT": IndicatorMeta(
        indicator_id="2.2.1",
        series_code="SH_STA_STNT",
        name="Prevalence of stunting among children under 5",
        domain_id="1",
        sector_id="1.1",
        subsector_id="1.1.4",
    ),
    "SN_STA_OVWGT": IndicatorMeta(
        indicator_id="2.2.2",
        series_code="SN_STA_OVWGT",
        name="Prevalence of overweight among children under 5",
        domain_id="1",
        sector_id="1.1",
        subsector_id="1.1.4",
    ),
    "SH_STA_ANEM": IndicatorMeta(
        indicator_id="2.2.3",
        series_code="SH_STA_ANEM",
        name="Prevalence of anaemia in women (15-49 years)",
        domain_id="1",
        sector_id="1.1",
        subsector_id="1.1.4",
    ),
    # 1.1.5 Reproductive health and family planning
    "SH_FPL_MTMM": IndicatorMeta(
        indicator_id="3.7.1",
        series_code="SH_FPL_MTMM",
        name="Need for family planning satisfied with modern methods",
        domain_id="1",
        sector_id="1.1",
        subsector_id="1.1.5",
    ),
    "SP_DYN_ADKL": IndicatorMeta(
        indicator_id="3.7.2",
        series_code="SP_DYN_ADKL",
        name="Adolescent birth rate (15-19 years)",
        domain_id="1",
        sector_id="1.1",
        subsector_id="1.1.5",
    ),
    # 1.1.6 Health risk reduction and management
    "SH_IHR_CAPS": IndicatorMeta(
        indicator_id="3.d.1",
        series_code="SH_IHR_CAPS",
        name="International Health Regulations (IHR) capacity",
        domain_id="1",
        sector_id="1.1",
        subsector_id="1.1.6",
    ),
    # Sector 1.2 - Agriculture
    # 1.2.1 Food security
    "AG_PRD_FIESMS": IndicatorMeta(
        indicator_id="2.1.2",
        series_code="AG_PRD_FIESMS",
        name="Prevalence of moderate or severe food insecurity (FIES)",
        domain_id="1",
        sector_id="1.2",
        subsector_id="1.2.1",
    ),
    "AG_LND_SUST": IndicatorMeta(
        indicator_id="2.4.1",
        series_code="AG_LND_SUST",
        name="Sustainable agriculture proportion",
        domain_id="1",
        sector_id="1.2",
        subsector_id="1.2.1",
    ),
    # 1.2.2 Agricultural systems and value chain strengthening
    "DC_TOF_AGRL": IndicatorMeta(
        indicator_id="2.a.2",
        series_code="DC_TOF_AGRL",
        name="Total official flows for agriculture",
        domain_id="1",
        sector_id="1.2",
        subsector_id="1.2.2",
    ),
    # Sector 1.3 - Social Infrastructure
    # 1.3.1 Water, sanitation, and hygiene (WASH)
    "SH_H2O_SAFE": IndicatorMeta(
        indicator_id="6.1.1",
        series_code="SH_H2O_SAFE",
        name="Safely managed drinking water services",
        domain_id="1",
        sector_id="1.3",
        subsector_id="1.3.1",
    ),
    "SH_SAN_SAFE": IndicatorMeta(
        indicator_id="6.2.1",
        series_code="SH_SAN_SAFE",
        name="Safely managed sanitation services",
        domain_id="1",
        sector_id="1.3",
        subsector_id="1.3.1",
    ),
    "SH_STA_WASHARI": IndicatorMeta(
        indicator_id="3.9.2",
        series_code="SH_STA_WASHARI",
        name="WASH-attributed mortality rate",
        domain_id="1",
        sector_id="1.3",
        subsector_id="1.3.1",
    ),
    # 1.3.2 Off-grid power
    "EG_ACS_ELEC": IndicatorMeta(
        indicator_id="7.1.1",
        series_code="EG_ACS_ELEC",
        name="Access to electricity",
        domain_id="1",
        sector_id="1.3",
        subsector_id="1.3.2",
    ),
    "EG_EGY_CLEAN": IndicatorMeta(
        indicator_id="7.1.2",
        series_code="EG_EGY_CLEAN",
        name="Reliance on clean fuels and technology",
        domain_id="1",
        sector_id="1.3",
        subsector_id="1.3.2",
    ),
    "EG_FEC_RNEW": IndicatorMeta(
        indicator_id="7.2.1",
        series_code="EG_FEC_RNEW",
        name="Renewable energy share in consumption",
        domain_id="1",
        sector_id="1.3",
        subsector_id="1.3.2",
    ),
    # 1.3.3 Digital financial inclusion
    "FB_BNK_ACCSS": IndicatorMeta(
        indicator_id="8.10.2",
        series_code="FB_BNK_ACCSS",
        name="Digital financial inclusion (15+ years)",
        domain_id="1",
        sector_id="1.3",
        subsector_id="1.3.3",
    ),
    # Sector 1.5 - Additional Country Considerations
    "SI_POV_NAHC": IndicatorMeta(
        indicator_id="1.2.1",
        series_code="SI_POV_NAHC",
        name="Population living below national poverty line",
        domain_id="1",
        sector_id="1.5",
        subsector_id="1.5.1",
    ),
}


# Mapping from series code to canonical per-indicator CSV filename.
SERIES_CODE_TO_FILENAME: Dict[str, str] = {
    "SI_POV_NAHC": "indicator-1-2-1.csv",
    "AG_PRD_FIESMS": "indicator-2-1-2.csv",
    "SH_STA_STNT": "indicator-2-2-1.csv",
    "SN_STA_OVWGT": "indicator-2-2-2.csv",
    "SH_STA_ANEM": "indicator-2-2-3.csv",
    "AG_LND_SUST": "indicator-2-4-1.csv",
    "DC_TOF_AGRL": "indicator-2-a-2.csv",
    "SH_STA_MORT": "indicator-3-1-1.csv",
    "SH_DYN_MORT": "indicator-3-2-1.csv",
    "SH_TBS_INCD": "indicator-3-3-2.csv",
    "SH_STA_MALR": "indicator-3-3-3.csv",
    "SH_FPL_MTMM": "indicator-3-7-1.csv",
    "SP_DYN_ADKL": "indicator-3-7-2.csv",
    "SH_ACS_UNHC_25": "indicator-3-8-1.csv",
    "SH_STA_WASHARI": "indicator-3-9-2.csv",
    "SH_IHR_CAPS": "indicator-3-d-1.csv",
    "SH_H2O_SAFE": "indicator-6-1-1.csv",
    "SH_SAN_SAFE": "indicator-6-2-1.csv",
    "EG_ACS_ELEC": "indicator-7-1-1.csv",
    "EG_EGY_CLEAN": "indicator-7-1-2.csv",
    "EG_FEC_RNEW": "indicator-7-2-1.csv",
    "FB_BNK_ACCSS": "indicator-8-10-2.csv",
}


def list_indicators_for_subsector(subsector_id: str) -> List[IndicatorMeta]:
    return [
        meta
        for meta in INDICATORS.values()
        if meta.subsector_id == subsector_id
    ]


def list_subsectors_for_sector(sector_id: str) -> List[str]:
    return sorted(
        {
            meta.subsector_id
            for meta in INDICATORS.values()
            if meta.sector_id == sector_id
        }
    )


def list_sectors_for_domain(domain_id: str) -> List[str]:
    return sorted(
        {
            meta.sector_id
            for meta in INDICATORS.values()
            if meta.domain_id == domain_id
        }
    )


def get_indicator_by_series(series_code: str) -> Optional[IndicatorMeta]:
    return INDICATORS.get(series_code)

