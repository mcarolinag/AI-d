import pandas as pd
from fastapi.responses import JSONResponse

def get_projects(df):
    # Renamed Some columns to make it match to the Front End
    df = df.rename(columns={
        "score": "Score",
        "ProjectTitle": "Project_Title",
        "SectorName": "Sector",
        "LongDescription": "Project_Description"  
    })

    # Selected the 7 Columns we need to display in the result.html
    selected = df[[
        "Score",
        "Project_Title",
        "Project_Description",
        "Province",
        "Latitude",
        "Longitude",
        "Sector"
    ]]

    result = selected.to_dict(orient="records")
    return JSONResponse(content=result)
