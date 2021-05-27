import requests
from time import sleep
import random
import pandas as pd
from datetime import datetime, timedelta
import uuid
import pyodbc
import os
import logging

def get_df_from_sqlQuery(
    sqlQuery,
    database
):
    ## Create connection string
    connectionString = get_connection_string(database)
    logging.info(f'Connection string created: {connectionString}')
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


def get_connection_string(database):
    username = 'matt.shepherd'
    password = "4rsenal!PG01"
    driver = '{ODBC Driver 17 for SQL Server}'
    # driver = 'SQL Server Native Client 11.0'
    server = "fse-inf-live-uk.database.windows.net"
    # database = 'AzureCognitive'
    ## Create connection string
    connectionString = f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}'
    return connectionString

def scrape_PressReader(
    publicationCID,
    date,
    publicationName,
    sleepSecs
):
    dateStr = datetime.strptime(
        date,
        "%Y-%m-%d"
    ).strftime("%Y%m%d")
    logging.info(f"publicationCID: {publicationCID}")
    logging.info(f"Publication Name: {publicationName}")
    logging.info(f"date: {dateStr}")
    accessToken = os.getenv("PressReader_AccessToken")
    # accessToken = "LpyrD0kdN70fR5eb_UjeVWPz6FFuWH-1leMi3b81tcVYceXmMl1G2UGOgwQb9KlfmaOHb0EHJueEnxarYQdSkA!!"


    PressReaderPublicationPages_rows = []
    PressReaderArticles_rows = []
    PressReaderImages_rows = []

    
    # myIssueID = (publicationCID,date)
    
    sleep(random.choice(sleepSecs))
    issueMetaReq = requests.get(
                    url="https://www.pressreader.com/api/IssueInfo/GetIssueInfoByCid",
                    params={
                            "accessToken" : accessToken
                            ,"cid" : publicationCID
                            ,"issueDate" : dateStr
                            })
    logging.info(issueMetaReq.url)
    issueMetaJS = issueMetaReq.json()
    ## Skip to next date if there was no issue on this date
    em = f"The issue for cid {publicationCID} and issueDate {dateStr} is not found"
    if "message" in issueMetaJS:
        if issueMetaJS["message"] == em:
            logging.info(em)
            return False
    totalPages = issueMetaJS['Pages']
    issueID = issueMetaJS['Issue']['Issue']
    logging.info(f"totalPages: {totalPages}")
    pageScales = {
        pageInfo['PageNumber'] : pageInfo['MaxUnrestrictedScale']
        for pageInfo in issueMetaJS['PagesInfo']
    }
    
    ## For every page in the publication, 
    for pgNumber in range(1,totalPages+1):
        ## tba1 -> PressReaderPublicationPages
        tba1 = {}
        ## Create an ID for each publication page
        tba1['PublicationPageID'] = f"{issueID}-{pgNumber}"
        scale = pageScales[pgNumber]
        if scale == 0:
            scale = max(pageScales.values())
        checkurl = f"https://t.prcdn.co/img?file={issueID}&page={pgNumber}&scale={scale}"
        tba1['PageImageURL'] = checkurl
        tba1['PublicationName'] = publicationName
        tba1['Date'] = date
        tba1['PageNumber'] = pgNumber
        if pgNumber == 1: 
            tba1['IsFrontPage'] = True
            tba1['IsBackPage'] = False
        elif pgNumber == totalPages:
            tba1['IsFrontPage'] = False
            tba1['IsBackPage'] = True
        else:
            tba1['IsFrontPage'] = False
            tba1['IsBackPage'] = False
        PressReaderPublicationPages_rows.append(tba1)
        
        ## Get articles on the page
        sleep(random.choice(sleepSecs))
        articleIDsReq = requests.get(
                url="https://www.pressreader.com/api/pagesMetadata",
                params={
                        "accessToken" : accessToken
                        ,"issue" : issueID
                        ,"pageNumbers" : pgNumber
                        }
            )
        # logging.info(articleIDsReq.url)
        articleIDsJS = articleIDsReq.json()
        pageArticleIDs = [str(x['ArticleId'])
                            for x in articleIDsJS[0]['Articles']]
        ## Get article information
        sleep(random.choice(sleepSecs))
        articleInfoReq = requests.get(
                url="https://www.pressreader.com/api/articles/GetItems",
                params={
                        "accessToken" : accessToken
                        ,"articles" : ",".join(pageArticleIDs)
                        ,"options" : 1
                        }
            )
        # logging.info(articleIDsReq.url)
        articleInfoJS = articleInfoReq.json()
        ## Loop through the articles
        for articleJS in articleInfoJS['Articles']:
            ## tba2 -> PressReaderArticles
            tba2 = {}
            tba2['PublicationPageID'] = tba1['PublicationPageID']
            tba2['PressReaderArticleID'] = articleJS['Id']
            tba2['Title'] = articleJS['Title']
            tba2['Subtitle'] = get_subtitle(articleJS['Subtitle'])
            tba2['Text'] = get_text(articleJS)
            if articleJS['Authors'] is None:
                tba2['Author'] = None
            else:
                raise ValueError("author")
            PressReaderArticles_rows.append(tba2)
            if articleJS['Images'] is not None:
                for imageJS in articleJS['Images']:
                    ## tba3 -> PressReaderImages
                    tba3 = {}
                    tba3['PublicationPageID'] = tba1['PublicationPageID']
                    tba3['PressReaderImageID'] = imageJS['Id']
                    tba3['PressReaderAssociatedArticleID'] = articleJS['Id']
                    tba3['ImageURL'] = imageJS['Url']
                    PressReaderImages_rows.append(tba3)
            
    PressReaderPublicationPages = pd.DataFrame(PressReaderPublicationPages_rows)
    PressReaderArticles = pd.DataFrame(PressReaderArticles_rows)
    PressReaderImages = pd.DataFrame(PressReaderImages_rows)

    upload_to_sql(
        df=PressReaderPublicationPages,
        sqlName="PressReaderPublicationPages"
    )
    logging.info("PressReaderPublicationPages in SQL")
    upload_to_sql(
        df=PressReaderArticles,
        sqlName="PressReaderArticles"
    )
    logging.info("PressReaderArticles in SQL")
    upload_to_sql(
        df=PressReaderImages,
        sqlName="PressReaderImages"
    )
    logging.info("PressReaderImages in SQL")

def upload_to_sql(
    df,
    sqlName
):
    db = "PhotoTextTrack"
    if sqlName == "PressReaderPublicationPages":
        columnDict = {
            "PublicationPageID" : "str",
            "PageImageURL" : "str",
            "PublicationName" : "str",
            "Date" : "Date",
            "PageNumber" : "int",
            "IsFrontPage" : "bit",
            "IsBackPage" : "bit"
        }
        ## Get insert commmand
        iq = create_insert_query(
            df=df,
            columnDict=columnDict,
            sqlTableName=sqlName
        )
        

    elif sqlName == "PressReaderArticles":
        columnDict = {
            "PublicationPageID" : "str",
            "PressReaderArticleID" : "str",
            "Title" : "str",
            "Subtitle" : "str",
            "Text" : "str",
            "Author" : "str"
        }
        ## Get insert commmand
        iq = create_insert_query(
            df=df,
            columnDict=columnDict,
            sqlTableName=sqlName
        )
        

    elif sqlName == "PressReaderImages":
        columnDict = {
            "PublicationPageID" : "str",
            "PressReaderImageID" : "str",
            "PressReaderAssociatedArticleID" : "str",
            "ImageURL" : "str"
        }
        ## Get insert commmand
        iq = create_insert_query(
            df=df,
            columnDict=columnDict,
            sqlTableName=sqlName
        )

    else:
        raise ValueError("Unrecognised sqlName: `{sqlName}`")

    logging.info(f"QUERY: {iq}")
    ## Run commmand
    run_sql_command(
        sqlQuery=iq,
        database=db
    )


def rows_to_strings(df,columnDict):
    
    listToReturn = []
    
    ## Loop throw the rows (as dicts)
    for row_dict in df.to_dict(orient="records"):
        ## Create list of strings formatted in the way SQL expects them
        ##    based on their SQL data type
        rowList = [sqlise(
                    _val_=row_dict[colName],
                    _format_=colType
                            )
                    for colName,colType in columnDict.items()]
        ## Create SQL ready string out of the list
        stringRow = "\n(" + ",".join(rowList) + ")"
        ## Add string to list
        listToReturn.append(stringRow)
        
    return listToReturn

            
def sqlise(_val_,_format_):
    if _val_ is None:
        return "NULL"
    elif _format_ == "str":
        return "'" + str(_val_).replace("'","''") + "'"
    elif _format_ == "DateTime":
        ## datetime gives 6 microsecond DPs, SQL only takes 3
        return "'" + _val_.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "'"
    elif _format_ == "Date":
        if isinstance(_val_,str):
            return "'" + _val_ + "'"
        else:
            return "'" + _val_.strftime("%Y-%m-%d") + "'"
    elif _format_ == "int":
        return str(_val_)
    elif _format_ == "bit":
        if _val_ == True:
            return str(1)
        elif _val_ == False:
            return str(0)
        else:
            return ValueError(f"Unacceptable value (`{_val_}`) for format (`{_format_}`)")
    else:
        raise ValueError(f"Data type `{_format_}` not expected")

    
def create_insert_query(df,columnDict,sqlTableName):
    """
    Inputs: - df - pandas.DataFrame
            - columnDict - dict - keys - column names
                                - vals - column (rough) SQL data types (as strings)
            - sqlTableName - str
    Output: - SQL insert query - str
    """
    ## Create column list string
    columnsListStr = "[" + "],[".join(columnDict.keys()) + "]"
    ## Convert df into a string of rows to upload
    stringRows = rows_to_strings(df,columnDict)
    
    
    Q = f"""
INSERT INTO {sqlTableName}
({columnsListStr})
VALUES {','.join(stringRows)}
    """
    return Q

def get_text(articleJS):
    if articleJS['Blocks'] is None:
        return None
    returnMe = ""
    for i,block in enumerate(articleJS['Blocks'],1):
        ## Text contains "soft hyphens" in the form of "\xad", remove them
        returnMe += block['Text'].replace("\xad","")
    
    return returnMe        
            
def get_subtitle(subtitle):
    if subtitle is None:
        return None
    elif subtitle == "":
        return None
    else:
        return subtitle

def update_row_status(
    publicationCID,
    publishedDate,
    status=None,
    uri=None
):
    currentDateTimeStr = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    if status is not None:
    ## Build update statement
        us = f"""
        UPDATE PressReaderScrapeQueue
        SET [Status] = '{status}', [StatusUpdatedDateTime] = '{currentDateTimeStr}'
        WHERE [PublicationCID] = '{publicationCID}' AND [PublishedDate] = '{publishedDate}'
        """
    elif uri is not None:
        us = f"""
        UPDATE PressReaderScrapeQueue
        SET [StatusQueryGetUri] = '{uri}'
        WHERE [PublicationCID] = '{publicationCID}' AND [PublishedDate] = '{publishedDate}'
        """
    else:
        raise ValueError("both `status` and `uri` are None")
    ## Run statement
    run_sql_command(
        sqlQuery=us,
        database="PhotoTextTrack"
    )

def remove_duplicates(columnList,sqlTableName,primaryKeyColName):
    
    ## Create column list string
    columnsListStr = "[" + "],[".join(columnList) + "]"
    Q = f"""
    WITH ToDelete AS (
       SELECT ROW_NUMBER() OVER
           (PARTITION BY {columnsListStr} ORDER BY {primaryKeyColName}) AS rn
       FROM {sqlTableName}
    )
    DELETE FROM ToDelete
    WHERE rn > 1
    """
    run_sql_command(
        sqlQuery=Q,
        database="PhotoTextTrack"
    )