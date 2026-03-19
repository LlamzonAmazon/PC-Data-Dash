from .scorers import (
    SimpleDirectionalScorer, RatioThresholdScorer, 
    InverseRatioScorer, RatioGoalInverseScorer, 
    DensityScorer, GoalRatioScorer
)

class IndicatorScorerFactory:
    def __init__(self) -> None:
        self._scorers = {
            # --- SECTOR 1: HEALTH ---
            "SH_ACS_UNHC_25": SimpleDirectionalScorer(),             # 3.8.1
            "SH_TBS_INCD": RatioThresholdScorer(threshold=40.0, global_average=40.0),  # 3.3.2
            "SH_STA_MALR": RatioThresholdScorer(threshold=10.0, global_average=10.0),  # 3.3.3
            "SH_STA_MORT": RatioThresholdScorer(threshold=70.0, global_average=70.0),  # 3.1.1
            "SH_DYN_MORT": RatioThresholdScorer(threshold=25.0, global_average=25.0),  # 3.2.1
            "SH_STA_STNT": RatioThresholdScorer(threshold=12.0, global_average=12.0),  # 2.2.1
            "SN_STA_OVWGT": RatioThresholdScorer(threshold=2.5, global_average=2.5),  # 2.2.2
            "SH_STA_ANEM": RatioThresholdScorer(threshold=25.0, global_average=25.0),  # 2.2.3
            "SH_FPL_MTMM": InverseRatioScorer(global_avg_val=11.5),  # 3.7.1
            "SP_DYN_ADKL": RatioThresholdScorer(threshold=20.0),     # 3.7.2
            "SH_IHR_CAPS": SimpleDirectionalScorer(),                # 3.d.1
            
            # --- SECTOR 2: AGRICULTURE ---
            "AG_PRD_FIESMS": RatioThresholdScorer(threshold=20.0, global_average=20.0),  # 2.1.2
            "AG_LND_SUST": RatioGoalInverseScorer(goal_transformed=0.04), # 2.4.1
            "DC_TOF_AGRL": GoalRatioScorer(goal=0.02),               # 2.a.2
            
            # --- SECTOR 3: SOCIAL INFRASTRUCTURE ---
            "SH_H2O_SAFE": InverseRatioScorer(global_avg_val=27.1),  # 6.1.1
            "SH_SAN_SAFE": InverseRatioScorer(global_avg_val=43.0),  # 6.2.1
            "SH_STA_WASHARI": RatioThresholdScorer(threshold=10.0, global_average=10.0),  # 3.9.2
            "EG_ACS_ELEC": InverseRatioScorer(global_avg_val=9.8),   # 7.1.1
            "EG_EGY_CLEAN": InverseRatioScorer(global_avg_val=30.4), # 7.1.2
            "EG_FEC_RNEW": InverseRatioScorer(global_avg_val=20.0),  # 7.2.1
            "FB_BNK_ACCSS": InverseRatioScorer(global_avg_val=45.0), # 8.10.2

            # --- CROSS-CUTTING & CONTEXT ---
            "GII_INDEX": RatioThresholdScorer(threshold=0.32),       # Gender Inequality
            "ND_GAIN_VULN": RatioThresholdScorer(threshold=0.46),    # Climate
            "POP_DENSITY": DensityScorer(),                          # Population Density
            "SI_POV_NAHC": RatioThresholdScorer(threshold=10.0, global_average=10.0),  # 1.2.1
            "MPI_INDEX": RatioThresholdScorer(threshold=0.089),      # MPI
        }

    def for_series(self, series_code: str):
        return self._scorers.get(series_code, SimpleDirectionalScorer())