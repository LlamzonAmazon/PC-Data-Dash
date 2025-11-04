import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

''' 
========== UN SDGs (Public APIs)========== 
API Documentation: https://unstats.un.org/SDGAPI/swagger/
Indicators Documentation: https://unstats.un.org/sdgs/indicators/indicators-list/

A goal is a broad primary outcome. Each goal has a unique code and title.
A target is a specific objective within a goal. Each target has a unique code and title.
An indicator is a specific metric used to measure progress towards a target. Each indicator has a unique code and description.
A series is a specific measurement method for an indicator. An indicator can have multiple series.
'''

# /v1/sdg/Goal/List
UN_SDG_GOAL_API_URL = "https://unstats.un.org/SDGAPI/v1/sdg/Goal/List"
# v1/sdg/Goal/{goalCode}/Target/List
UN_SDG_TARGET_PER_GOAL_API_URL = "https://unstats.un.org/SDGAPI/v1/sdg/Goal/{goalCode}/Target/List"
# v1/sdg/Goal/Data
UN_SDG_GOAL_DATA_API_URL = "https://unstats.un.org/SDGAPI/v1/sdg/Goal/Data"
# v1/sdg/Indicator/List
UN_SDG_INDICATOR_API_URL = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List"
#v1/sdg/Indicator/{indicatorCode}/Series/List
UN_SDG_INDICATOR_SERIES_API_URL = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/{indicatorCode}/Series/List"
# v1/sdg/Indicator/Data
UN_SDG_INDICATOR_DATA_API_URL = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/Data"
# v1/sdg/Indicator/PivotData
UN_SDG_INDICATOR_PIVOT_DATA_API_URL = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/PivotData"

''' ========== END ========== '''

'''
########## FETCH UN SDG DATA ##########
'''
def un_sdg_fetch_data(api_url, params):
    response = requests.get(api_url, params=params)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()

''' 
########## STRUCTURE GOALS LIST ##########
@ param goals_data: List of goals with nested targets and indicators
@ return: Three DataFrames - goals, targets, indicators
'''
def goals_list_to_dataframes(goals_data):
    goal_rows = []
    target_rows = []
    indicator_rows = []

    for goal in goals_data:
        goal_rows.append({
            "goal_code": goal["code"],
            "goal_title": goal["title"],
            "goal_description": goal.get("description", "")
        })

        for target in goal.get("targets", []):
            target_rows.append({
                "goal_code": goal["code"],
                "target_code": target["code"],
                "target_title": target["title"]
            })

            for indicator in target.get("indicators", []):
                indicator_rows.append({
                    "goal_code": goal["code"],
                    "target_code": target["code"],
                    "indicator_code": indicator["code"],
                    "indicator_description": indicator["description"]
                })

    # Convert dictionaries into DataFrames
    df_goals = pd.DataFrame(goal_rows)
    df_targets = pd.DataFrame(target_rows)
    df_indicators = pd.DataFrame(indicator_rows)

    return df_goals, df_targets, df_indicators


# Fetch & Print UN SDG Goals List
un_sdg_data = un_sdg_fetch_data(UN_SDG_GOAL_API_URL, {"includeChildren": "true"})
df_goals, df_targets, df_indicators = goals_list_to_dataframes(un_sdg_data)

# Display summaries
print(f"=== GOALS ===\n\n {df_goals.head()}\n")
print(f"=== TARGETS ===\n\n {df_targets.head()}\n")
print(f"=== INDICATORS ===\n\n {df_indicators.head()}\n")

'''
========== ND-GAIN ==========
'''

''' ========== END ========== '''

''' 
========== World Bank ========== 

'''
''' ========== END ========== '''