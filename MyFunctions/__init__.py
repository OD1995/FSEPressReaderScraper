import requests
from time import sleep
import random
import pandas as pd
from datetime import datetime, timedelta
import uuid
import pyodbc
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
    otherInfo,
    sleepSecs
):
    logging.info(f"publicationCID: {publicationCID}")
    logging.info(f"date: {date}")
    accessToken = "LpyrD0kdN70fR5eb_UjeVWPz6FFuWH-1leMi3b81tcVYceXmMl1G2UGOgwQb9KlfmaOHb0EHJueEnxarYQdSkA!!"


    PressReaderPublicationPages_rows = []
    PressReaderArticles_rows = []
    PressReaderImages_rows = []

    news = otherInfo['Name']
    # countrySlug = otherInfo['CountrySlug']
    # slug = otherInfo['Slug']
    print(f"Publication Name: {news}")
    
    # myIssueID = (publicationCID,date)
    
    dateStr = date.strftime('%Y%m%d')
    sleep(random.choice(sleepSecs))
    issueMetaJS = requests.get(
                    url="https://www.pressreader.com/api/IssueInfo/GetIssueInfoByCid",
                    params={
                            "accessToken" : accessToken
                            ,"cid" : publicationCID
                            ,"issueDate" : dateStr
                            }).json()
    ## Skip to next date if there was no issue on this date
    em = f"The issue for cid {publicationCID} and issueDate {dateStr} is not found"
    if "message" in issueMetaJS:
        if issueMetaJS["message"] == em:
            logging.info(em)
            return False
    totalPages = issueMetaJS['Pages']
    issueID = issueMetaJS['Issue']['Issue']
    logging.info(f"totalPages: {totalPages}")
    
    ## For every page in the publication, 
    for pgNumber in range(1,totalPages+1):
        ## tba1 -> PressReaderPublicationPages
        tba1 = {}
        ## Create a UUID for each publication page
        tba1['PublicationPageID'] = str(uuid.uuid4())
        checkurl = f"https://t.prcdn.co/img?file={issueID}&page={pgNumber}&scale=54"
        tba1['PageImageURL'] = checkurl
        tba1['PublicationName'] = news
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
        articleIDsJS = requests.get(
                url="https://www.pressreader.com/api/pagesMetadata",
                params={
                        "accessToken" : accessToken
                        ,"issue" : issueID
                        ,"pageNumbers" : pgNumber
                        }
            ).json()
        pageArticleIDs = [str(x['ArticleId'])
                            for x in articleIDsJS[0]['Articles']]
        ## Get article information
        sleep(random.choice(sleepSecs))
        articleInfoJS = requests.get(
                url="https://www.pressreader.com/api/articles/GetItems",
                params={
                        "accessToken" : accessToken
                        ,"articles" : ",".join(pageArticleIDs)
                        ,"options" : 1
                        }
            ).json()
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
    upload_to_sql(
        df=PressReaderArticles,
        sqlName="PressReaderArticles"
    )
    upload_to_sql(
        df=PressReaderImages,
        sqlName="PressReaderImages"
    )

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
        ## Run commmand
        run_sql_command(
            sqlQuery=iq,
            database=db
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
        ## Run commmand
        run_sql_command(
            sqlQuery=iq,
            database=db
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
        ## Run commmand
        run_sql_command(
            sqlQuery=iq,
            database=db
        )

    else:
        raise ValueError("Unrecognised sqlName: `{sqlName}`")

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
        return "'" + _val_.replace("'","''") + "'"
    elif _format_ == "DateTime":
        ## datetime gives 6 microsecond DPs, SQL only takes 3
        return "'" + _val_.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "'"
    elif _format_ == "Date":
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
#        oks = ['text','annotation']
#        if (block['Role'] not in oks):# or (block['Markups'] is not None):
#            errorDict = {
#                    "ArticleID" : articleJS['Id']
#                    ,"BlockNumber" : f"{i}of{len(articleJS['Blocks'])}"
#                    ,"Publication" : articleJS['Issue']['Title']
#                    ,"Date" : articleJS['Issue']['ShortDateString']
#                    }
#            raise ValueError(errorDict)
#        else:
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