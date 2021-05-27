import requests
import time
from datetime import datetime
import pandas as pd
import pyodbc

LOCAL = True

def get_df_from_sqlQuery(
    sqlQuery,
    database
):
    ## Create connection string
    connectionString = get_connection_string(database)
#    print(f'Connection string created: {connectionString}')
    ## Execute SQL query and get results into df 
    with pyodbc.connect(connectionString) as conn:
        ## Get SQL table in pandas DataFrame
        df = pd.read_sql(sql=sqlQuery,
                            con=conn)
    return df

def run_sql_command(
    sqlQuery,
    database
):
    ## Create connection string
    connectionString = get_connection_string(database)
    ## Run query
    with pyodbc.connect(connectionString) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sqlQuery)

def update_row_status(
    publicationCID,
    publishedDate,
    status
):
    pubdat = publishedDate.strftime("%Y-%m-%d")
    us = f"""
    UPDATE PressReaderTempQ
    SET [Status] = '{status}'
    WHERE [PublicationCID] = '{publicationCID}' AND [Date] = '{pubdat}'
    """
    ## Run statement
    run_sql_command(
        sqlQuery=us,
        database="PhotoTextTrack"
    )

def get_connection_string(database):
    username = 'matt.shepherd'
    password = "4rsenal!PG01"
#    driver = '{ODBC Driver 17 for SQL Server}'
    driver = 'SQL Server Native Client 11.0'
    server = "fse-inf-live-uk.database.windows.net"
    # database = 'AzureCognitive'
    ## Create connection string
    connectionString = f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}'
    return connectionString


df = get_df_from_sqlQuery(
    sqlQuery="SELECT * FROM PressReaderTempQ",
    database="PhotoTextTrack"
)


for i in df.index:
    print(datetime.now())
    print(f"{i+1} of {len(df)}")
    infoDict = dict(df.loc[i])
    print(infoDict)
    ## Update row to say it's in progress
    update_row_status(
        publicationCID=infoDict['PublicationCID'],
        publishedDate=infoDict['Date'],
        status="In Progress"
    )
    accessToken = "0npQuisQKmRaQdZmm_A2TTWJhTqOK5-AzZKDUQptqlo7yZ7KpnlXWaP0bHXR63AVtPXT96PQUHBZ_ZkeJ3YVMg!!"
    dateStr = infoDict['Date'].strftime("%Y%m%d")
    publicationCID = infoDict['PublicationCID']
    issueMetaReq = requests.get(
                    url="https://www.pressreader.com/api/IssueInfo/GetIssueInfoByCid",
                    params={
                            "accessToken" : accessToken
                            ,"cid" : publicationCID
                            ,"issueDate" : dateStr
                            })
#    logging.info(issueMetaReq.url)
    issueMetaJS = issueMetaReq.json()
    ## Skip to next date if there was no issue on this date
    em = f"The issue for cid {publicationCID} and issueDate {dateStr} is not found"
    if "message" in issueMetaJS:
        if issueMetaJS["message"] == em:
            print(em)
#            continue
    totalPages = issueMetaJS['Pages']
    issueID = issueMetaJS['Issue']['Issue']
    print(f"totalPages: {totalPages}")
    pageScales = {
        pageInfo['PageNumber'] : pageInfo['MaxUnrestrictedScale']
        for pageInfo in issueMetaJS['PagesInfo']
    }
    for pgNumber in range(1,totalPages+1):
        ## Create an ID for each publication page
        scale = pageScales[pgNumber]
        if scale == 0:
            scale = max(pageScales.values())
        newURL = f"https://t.prcdn.co/img?file={issueID}&page={pgNumber}&scale={scale}"
        oldURL = f"https://t.prcdn.co/img?file={issueID}&page={pgNumber}&scale=54"
        ## Write update statements
        us = f"""
        UPDATE PressReaderPublicationPages
        SET PageImageURL = '{newURL}'
        WHERE PageImageURL = '{oldURL}'        
        """
        run_sql_command(
            sqlQuery=us,
            database="PhotoTextTrack"
        )

    ## Update row to say it's in done
    update_row_status(
        publicationCID=infoDict['PublicationCID'],
        publishedDate=infoDict['Date'],
        status="Finished"
    )





