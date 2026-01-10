
class WorldBankClean(DataCleaner):

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
    
    def clean_data(self, indicator_data) -> pd.DataFrame:
        pass 

    def normalize(records: List[Dict[str, Any]], alias: str) -> pd.DataFrame:
        """
        NOTE: Caroline's code; copy-pasted from world_bank_fetch.py
        TODO: IMPLEMENT SAME CLEANING LOGIC IN clean_data() above

        Conert raw API records into a tidy DataFrame.

        Args:
            records (List[Dict[str, Any]]): List of records to convert
            alias (str): User-friendly name for the indicator

        Returns:
            pd.DataFrame: Cleaned DataFrame with country, iso3, indicator, year, and value columns.
        """

        rows = []
        for rec in records or []:
            rows.append({
                "country": (rec.get("country") or {}).get("value"),
                "iso3": rec.get("countryiso3code"),
                "indicator": alias,                         # Use user-friendly name
                "year": int(rec.get("date")) if str(rec.get("date")).isdigit() else rec.get("date"),
                "value": rec.get("value")
            })

        # Build DataFrame and sort for readability
        df = pd.DataFrame(rows, columns=["country","iso3","indicator","year","value"])
        return df.sort_values(["indicator","iso3","year"], ascending=[True,True,False], na_position="last")