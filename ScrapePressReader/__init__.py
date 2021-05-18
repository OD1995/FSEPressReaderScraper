# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import logging
from ..MyFunctions import (
    update_row_status,
    scrape_PressReader,
    get_df_from_sqlQuery
)
import traceback


def main(inputDict: dict) -> str:
    ## Get publicationCID and publishedDate
    publicationCID = inputDict["publicationCID"]
    publishedDate = inputDict["publishedDate"]
    logging.info(f"publicationCID: {publicationCID}")
    logging.info(f"publishedDate: {publishedDate}")
    try:
        ## Update row status
        update_row_status(
            publicationCID,
            publishedDate,
            status="In Progress"
        )
        logging.info("row updated to `In Progress`")
        ## Get info about the publication
        pubInfoDF = get_df_from_sqlQuery(
            sqlQuery=f"""SELECT * FROM PressReaderPublications
                        WHERE [PublicationCID] = '{publicationCID}'""",
            database="PhotoTextTrack"
        ).set_index("PublicationCID")
        publicationName = pubInfoDF.loc[publicationCID,"Name"]
        logging.info(f"publicationName: {publicationName}")
        ## Start scrape
        scrape_PressReader(
            publicationCID=publicationCID,
            date=publishedDate,
            publicationName=publicationName,
            sleepSecs=[x/1000 for x in range(2000)]
        )
        ## Update row status
        update_row_status(
            publicationCID,
            publishedDate,
            status="Finished"
        )
        logging.info("row updated to `Finished`")
        return "success"

    except Exception as error:
        ## Update row status
        update_row_status(
            publicationCID,
            publishedDate,
            status="Error"
        )
        logging.info("row updated to `Error`")
        # logging.error(error)
        ## Raise error
        raise Exception("".join(traceback.TracebackException.from_exception(error).format()))