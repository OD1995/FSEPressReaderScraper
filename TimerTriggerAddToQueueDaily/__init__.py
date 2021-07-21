from datetime import datetime, timedelta
import logging
import requests
from ..MyFunctions import (
    get_df_from_sqlQuery
)
import azure.functions as func


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')
    ## Get yesterday's date
    yesterday_dt = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday_dt.strftime("%Y-%m-%d")
    ## Get requested publication IDs
    cIDs = get_df_from_sqlQuery(
        sqlQuery="SELECT DISTINCT PublicationCID FROM PressReaderDailyScrapePublications",
        database='PhotoTextTrack'
    ).PublicationCID.to_list()
    ## Get all valid publication IDs
    valid_cIDs = get_df_from_sqlQuery(
        sqlQuery="SELECT DISTINCT PublicationCID FROM PressReaderPublications",
        database='PhotoTextTrack'
    ).PublicationCID.to_list()
    ## Loop through the requested IDs, ensure they're valid and add to list
    js_list = []
    for cID in cIDs:
        if cID in valid_cIDs:
            js_list.append(
                {
                    'publicationCID' : cID,
                    'startDate' : yesterday_str,
                    'endDate' : yesterday_str
                }
            )
        else:
            logging.info(f"`{cID}` not in PressReaderPublications so not queued up")

    logging.info(f"len(js_list): {len(js_list)}")

    if len(js_list) > 0:

        logging.info(f"js_list: {js_list}")

        r = requests.post(
                url="https://fsepressreaderscraper.azurewebsites.net/api/HttpTriggerAddToQueue",
                json=js_list
            )

        logging.info(r)
        logging.info(r.text)

        logging.info('done')


    # cIDs = [
    #     '1043', #Daily Express
    #     '1048', #Daily Mail
    #     '1039', #Daily Mirror
    #     '1069', #Daily Star
    #     '1071', #Daily Star Sunday
    #     '1237', #London Evening Standard (West End Final A)
    #     '9xvz', #Metro (UK)
    #     '1070', #Sunday Express
    #     '1259', #Sunday Mirror
    #     '1190', #The Daily Telegraph
    #     '1545', #The Guardian
    #     '1029', #The Independent
    #     '1054', #The Mail on Sunday
    #     '1702', #The Observer
    #     '1191', #The Sunday Telegraph
    #     '9029', #The Sunday Times
    # ]

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
