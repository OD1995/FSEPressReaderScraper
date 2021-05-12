import logging
import azure.functions as func
from datetime import datetime, timedelta
from MyFunctions import (
    get_df_from_sqlQuery,
    scrape_PressReader
)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    listOfCIDs = req.params.get("listOfCIDs")
    startDate = req.params.get("startDate") # yyyy-mm-dd
    endDate = req.params.get("endDate") # yyyy-mm-dd
    ## Create date range
    start = datetime.strptime(startDate, "%Y-%m-%d")
    end = datetime.strptime(endDate, "%Y-%m-%d")
    dates = [(start + timedelta(days=x)).date()
                for x in range(0, (end-start).days+1)]
    ## Prepare some data
    # publishDaysDF = get_df_from_sqlQuery(
    #     sqlQuery="SELECT * FROM PressReaderPublishDays",
    #     database="PhotoTextTrack"
    # ).set_index('PublicationCID')
    # publishDaysDict = publishDaysDF.to_dict('index')
    publicationsDF = get_df_from_sqlQuery(
        sqlQuery="SELECT * FROM PressReaderPublications",
        database="PhotoTextTrack"
    ).set_index('PublicationCID')
    publicationsDict = publicationsDF.to_dict('index').items()
    ## Get the publication-date combinations already scraped
    alreadyScraped = get_df_from_sqlQuery(
        sqlQuery="SELECT DISTINCT [PublicationName],[Date] FROM PressReaderPublicationPages",
        database="PhotoTextTrack"
    )
    alreadyScrapedList = [
        [pn,d.strptime('%Y%m%d')]
        for pn,d in zip(
            alreadyScraped.PublicationName,
            alreadyScraped.Date
        )
    ]

    sleepSecs = [1 + (x/1000) for x in range(2000)]
    ## Loop through the combinations
    for publicationCID in listOfCIDs:  
        otherInfo = publicationsDict[publicationCID]
        for date in dates:
            scrape_PressReader(
                publicationCID,
                date,
                otherInfo,
                sleepSecs
            )
