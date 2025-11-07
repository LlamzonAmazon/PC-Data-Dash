"""
One-button ETL: fetch -> transform -> (optionally) model -> export
"""
from src.pipeline.utils import setup_logger
def main():
    log = setup_logger()
    log.info("Pipeline start")
    # 1) Fetch (WB/UN/ND-GAIN) -> data/raw + interim
    # 2) Transform -> data/interim -> data/processed
    # 3) (Optional) Model -> features/forecasts into processed
    # 4) Export to Power BI folder if needed
    log.info("Pipeline end")

if __name__ == "__main__":
    main()
