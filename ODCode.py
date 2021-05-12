#from bs4 import BeautifulSoup
#from selenium import webdriver
import requests
#from selenium.webdriver.common.keys import Keys
from time import sleep
import random
#import urllib
#from urllib.request import urlopen, Request
#import difflib
import pandas as pd
from datetime import datetime, timedelta
import uuid
#import urllib.parse as urlparse
#from urllib.parse import parse_qs
import sys
sys.path.insert(0,r"K:\Technology Team\Python")
import sql_helper
import os
os.chdir(r"K:\Technology Team\Python\Azure\FSEPressReaderScraper")
import MyFunctions as helper

START = datetime.now()

accessToken = "LpyrD0kdN70fR5eb_UjeVWPz6FFuWH-1leMi3b81tcVYceXmMl1G2UGOgwQb9KlfmaOHb0EHJueEnxarYQdSkA!!"


#publicationCIDs = [
#        "9a63",
#        "9j66",
#        "9e10"
#        ]

#startdate = "2021-01-09"
#enddate = "2021-01-09"
startdate = "2021-02-07"
enddate = "2021-02-23"
#newspaperlistchild = [
##        "https://www.pressreader.com/australia/the-west-australian/",
##        "https://www.pressreader.com/australia/the-guardian-australia/",
#        "https://www.pressreader.com/australia/cockburn-gazette/"
#                ]

publishDaysDF = sql_helper.fromSQL(
            servername="inf",
            database="PhotoTextTrack",
            SQLtablename="PressReaderPublishDays"
    ).set_index('PublicationCID')
publishDaysDict = publishDaysDF.to_dict('index')

publicationsDF = sql_helper.fromSQL(
            servername="inf",
            database="PhotoTextTrack",
            SQLtablename="PressReaderPublications"
    ).set_index('PublicationCID')
publicationsDict = {
                    k:v
                    for k,v in publicationsDF.to_dict('index').items()
                    if k in publishDaysDict
                    }

dotwDict = {
        0 : "Monday",
        1 : "Tuesday",
        2 : "Wednesday",
        3 : "Thursday",
        4 : "Friday",
        5 : "Saturday",
        6 : "Sunday"
                }

start = datetime.strptime(startdate, "%Y-%m-%d")
end = datetime.strptime(enddate, "%Y-%m-%d")
dates = [(start + timedelta(days=x)).date()
            for x in range(0, (end-start).days+1)]

sleepSecs = [1 + (x/1000) for x in range(2000)]

PressReaderPublicationPages_rows = []
PressReaderArticles_rows = []
PressReaderImages_rows = []

for publicationCID,otherInfo in publicationsDict.items():
    news = otherInfo['Name']
    countrySlug = otherInfo['CountrySlug']
    slug = otherInfo['Slug']
    print(f"news: {news}")
    
    for date in dates:
        print(f"date: {date}")
        myIssueID = (publicationCID,date)
        
        ## Make sure the paper is published on this day of the week
        if not publishDaysDict[publicationCID][dotwDict[date.weekday()]]:
            print(f"not published on a {dotwDict[date.weekday()]}, skipping")
            continue
        
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
                print(em)
                continue
        totalPages = issueMetaJS['Pages']
        issueID = issueMetaJS['Issue']['Issue']
        print(f"totalPages: {totalPages}")
        
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
                tba2['Subtitle'] = helper.get_subtitle(articleJS['Subtitle'])
                tba2['Text'] = helper.get_text(articleJS)
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
        
#P = r"C:\Users\oli.dernie\Documents\Automation tests\Aus\PressReader"
#PressReaderPublicationPages.to_excel(fr"{P}\PressReaderPublicationPages.xlsx",index=False)
#PressReaderArticles.to_excel(fr"{P}\PressReaderArticles.xlsx",index=False)
#PressReaderImages.to_excel(fr"{P}\PressReaderImages.xlsx",index=False)
        
END = datetime.now()
print(END - START)    