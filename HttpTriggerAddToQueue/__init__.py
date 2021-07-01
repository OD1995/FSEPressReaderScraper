import logging
from datetime import datetime, timedelta
import azure.functions as func
import pandas as pd
from ..MyFunctions import (
    create_insert_query,
    run_sql_command,
    remove_duplicates
)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    ## Get list from the request
    listOfPubInfo = req.get_json()
    ## Loop through list
    for pubInfo in listOfPubInfo:
        ## Each element contains three items:
        ##    publicationCID
        ##    startDate (%Y-%m-%d)
        ##    endDate (%Y-%m-%d)
        logging.info(f"pubInfo: {pubInfo}")
        publicationCID = pubInfo['publicationCID']
        startDate = pubInfo['startDate']
        endDate = pubInfo['endDate']
        ## Create list from startDate to endDate
        start = datetime.strptime(startDate, "%Y-%m-%d")
        end = datetime.strptime(endDate, "%Y-%m-%d")
        dates = [
            (start + timedelta(days=x)).date()
            for x in range(0, (end-start).days+1)
            ]
        ## Create insert command
        insertCommand = create_insert_query(
            df=pd.DataFrame(
                {
                    "PublicationCID" : [publicationCID] * len(dates),
                    "PublishedDate" : dates
                }
            ),
            columnDict={
                "PublicationCID" : "str",
                "PublishedDate" : "Date"
            },
            sqlTableName="PressReaderScrapeQueue"
        )
        ## Run command
        run_sql_command(
            sqlQuery=insertCommand,
            database="PhotoTextTrack"
        )

    remove_duplicates(
        columnList=[
            "PublicationCID",
            "PublishedDate"
        ],
        sqlTableName="PressReaderScrapeQueue",
        primaryKeyColName="RowID"
    )

    return "done"
