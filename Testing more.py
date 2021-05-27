from time import sleep
from datetime import datetime
import random
import requests
import pandas as pd

publicationCID = "9a63"
date = "2021-02-13"
publicationName = "The West Australian"
sleepSecs = [x/1000 for x in range(2000)]

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

#def scrape_PressReader(
#    publicationCID,
#    date,
#    publicationName,
#    sleepSecs
#):
dateStr = datetime.strptime(
    date,
    "%Y-%m-%d"
).strftime("%Y%m%d")
print(f"publicationCID: {publicationCID}")
print(f"Publication Name: {publicationName}")
print(f"date: {dateStr}")
#accessToken = os.getenv("PressReader_AccessToken")
accessToken = "LpyrD0kdN70fR5eb_UjeVWPz6FFuWH-1leMi3b81tcVYceXmMl1G2UGOgwQb9KlfmaOHb0EHJueEnxarYQdSkA!!"


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
print(issueMetaReq.url)
issueMetaJS = issueMetaReq.json()
## Skip to next date if there was no issue on this date
em = f"The issue for cid {publicationCID} and issueDate {dateStr} is not found"
if "message" in issueMetaJS:
    if issueMetaJS["message"] == em:
        print(em)
#        return False
        raise ValueError("finished")
totalPages = issueMetaJS['Pages']
issueID = issueMetaJS['Issue']['Issue']
print(f"totalPages: {totalPages}")
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
    # print(articleIDsReq.url)
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
    # print(articleIDsReq.url)
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