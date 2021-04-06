#!/usr/bin/env python
# coding: utf-8

# # **PressReader Scraping Script**

# This script cycles through all the ePress editions on PressReader for selected Newspapers and date ranges. Currently, the process is as follows:
# - Manually enter the parent newspaper URL's as a list, and input a date range between which you wish to scrape newspaper data. The URL should be in the form of, by way of example: "[https://www.pressreader.com/australia/the-guardian-australia/"](https://www.pressreader.com/australia/the-guardian-australia/&quot;)
# - The script will then cycle through each combination of newspaper and date, save an image of each page, then enter each article and scrape the title, author, text and image URL's
# - Once it has cycled through each newspaper and date combination, Python will return three dataframes:
#     - NewspaperFullPageImages will contain a row for each page in each newspaper, with information about each edition, page, and a link to each page image
#     - NewspaperContent will contain a line for each article, with all the scraped information
#     - NewspaperArticleImages will contain a link to every image within each article
# Please reach out to Alex Hadden ([alex.hadden@futuressport.com](mailto:&#97;&#108;&#x65;&#x78;&#x2e;&#104;&#97;&#x64;&#x64;&#101;&#x6e;&#x40;&#102;&#117;&#x74;&#x75;&#114;&#x65;&#x73;&#x73;&#x70;&#x6f;&#114;&#x74;&#x2e;&#x63;&#x6f;&#109;)) is there are any issues.
# **Builds still needed:**
# - ~Fix logic statements to make code shorter and run more effiiently~
# - ~Make attribute selections more robust~
# - Add tables in SQL for Python to insert the data
# - Create a table(s) in SQL with a list of papers and their corresponding parent URL. Another table could be used to list the newspapers that each account requires, therefore the client name can just be input at the start of the script
# - Make the date range more robust, whereby we set a start date and use the system date as the end date. We would then select all newspapers and dates that are not in SQL, and scrape the data for them
# - ~~Create a more robust way to join the tables. Will likely need to create a GUID in Python that can be uploaded to SQL~~

## STEP 1
## Load the required packages

accessToken = "LpyrD0kdN70fR5eb_UjeVWPz6FFuWH-1leMi3b81tcVYceXmMl1G2UGOgwQb9KlfmaOHb0EHJueEnxarYQdSkA!!"

from bs4 import BeautifulSoup
from selenium import webdriver
import requests
from selenium.webdriver.common.keys import Keys
import time
import random
import urllib
from urllib.request import urlopen, Request
import difflib
import pandas as pd
import datetime
import uuid
import urllib.parse as urlparse
from urllib.parse import parse_qs
import sys
sys.path.insert(0,r"K:\Technology Team\Python")
import sql_helper
import os
os.chdir(r"K:\Technology Team\Python\Azure\FSEPressReaderScraper")
import MyFunctions as helper

# **Step 2:** Input the date range and the parent URL's as a list

publicationCIDs = [
        "9a63",
#        "9j66",
#        "9e10"
        ]

#startdate = "2021-01-09"
#enddate = "2021-01-09"
startdate = "2021-03-25"
enddate = "2021-03-25"
newspaperlistchild = [
#        "https://www.pressreader.com/australia/the-west-australian/",
#        "https://www.pressreader.com/australia/the-guardian-australia/",
        "https://www.pressreader.com/australia/cockburn-gazette/"
                ]

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
                    if k in publicationCIDs
                    }

# **Step 3:** Set up the web driver and log in to Press Reader. Note: you don't need to touch anything from here on out

dotwDict = {
        0 : "Monday",
        1 : "Tuesday",
        2 : "Wednesday",
        3 : "Thursday",
        4 : "Friday",
        5 : "Saturday",
        6 : "Sunday"
                }

start = datetime.datetime.strptime(startdate, "%Y-%m-%d")
end = datetime.datetime.strptime(enddate, "%Y-%m-%d")
date_generated = [start + datetime.timedelta(days = x) for x in range(0, (end-start).days+1)]


driver = helper.get_driver_and_login()

# STEP 4
## Create the empty lists, and cycle through each newspaper date combination to generate the data



##Set up NewspaperFullPageImages dataframe
finalpaper = []
finaldateadd = []
finalIsFrontPage = []
finalIsBackPage = []
finalpagelinks = []
finalnewspaperpageid = []
all_NewspaperFullPageImagesRows = {}


##Set up NewspaperContent dataframe
finalarticleid = []
finalheadline = []
finalauthor = []
finaltext = []
finaljoinpagelinks = []
finalfromnewspaperpageid = []
finalarticleguid = []

##Set up NewspaperArticleImages	dataframe
finalmultiarticleid = []
finalarticleimageurl = []
finalfromarticleguid = []

for publicationCID,otherInfo in publicationsDict.items():
    news = otherInfo['Name']
    countrySlug = otherInfo['CountrySlug']
    slug = otherInfo['Slug']
    print(f"news: {news}")
    
    for dateformat in date_generated:
        print(f"dateformat: {dateformat}")
        myIssueID = (publicationCID,dateformat)
        
        ## Make sure the paper is published on this day of the week
        if not publishDaysDict[publicationCID][dotwDict[dateformat.weekday()]]:
            print(f"not published on a {dotwDict[dateformat.weekday()]}, skipping")
            continue
        ##Set up NewspaperFullPageImages dataframe
        issue_NewspaperFullPageImagesRows = []
#        paper = []
#        date = []
#        isFrontPages = []
#        isBackPages = []
#        pagelinks = []
#        newspaperpageid = []

        ##Set up NewspaperContent dataframe
        articleid = []
        headline = []
        author = []
        text = []
        joinpagelinks = []
        fromnewspaperpageid = []
        articleguid = []

        ##Set up NewspaperArticleImages	dataframe
        multiarticleid = []
        articleimageurl = []
        fromarticleguid = []
        
        finaldate = dateformat.strftime('%Y%m%d')
        issueMetaJS = requests.get(
                        url="https://www.pressreader.com/api/IssueInfo/GetIssueInfoByCid",
                        params={
                                "accessToken" : accessToken
                                ,"cid" : publicationCID
                                ,"issueDate" : finaldate
                                }).json()
        numpages = issueMetaJS['Pages']
        ## Create issueID
#        issueID = f"{publicationCID}{finaldate}00000000001001"
        issueID = issueMetaJS['Issue']['Issue']
        ## Navigate to the website of the paper
        url = f"https://www.pressreader.com/{countrySlug}/{slug}/{finaldate}"
        driver.get(url)
        time.sleep(15)
        content = driver.page_source
        soup = BeautifulSoup(content, 'html.parser')
        titlepagehtml = soup.find_all("div",
                                      attrs={"class": "page page-cover zoom-off"}
                                      )[0].find_all("img")[1]
        ## Grab the url for the cover page image 
        titlepage = titlepagehtml['src'] 
        
        ##Scrape elements from first and last page of paper
#        driver.find_element_by_tag_name('body').send_keys(Keys.LEFT)
#        time.sleep(2)
#        content = driver.page_source
#        soup = BeautifulSoup(content, 'html.parser')
#        ## Get all the available img tags
#        pageNumbers = []
#        imgSrcs = [x['src']
#                   for x in soup.find_all('img')
#                   if ("gif" not in x['src']) & ("page=" in x['src'])]
#        for imgSrc in imgSrcs:
#            parsedURL = urlparse.urlparse(imgSrc)
#            pageNumbers.append(
#                    int(parse_qs(parsedURL.query)['page'][0])
#                            )
#        numpages = max(pageNumbers)
        print(f"numpages: {numpages}")
        
        driver.find_element_by_tag_name('body').send_keys(Keys.RIGHT)
        
        baselink = [] #Used for locating which page to scrape from. More explained in row 145
        
        ## For every page in the publication, 
        for pgNumber in range(1,numpages+1):
            tba1 = {}
            checkurl = "https://t.prcdn.co/img?file={issueID}&page={pgNumber}&scale=54"
            #Adding to column in NewspaperFullPageImages
            tba1['PublicationPageID'] = checkurl
#            pagelinks.append(checkurl) 
#            baselink.append(checkurl.split("&scale")[0])
            #Adding to column in NewspaperFullPageImages
#            paper.append(news)
            tba1['PublicationName'] = news
            #Adding to column in NewspaperFullPageImages
#            date.append(dateformat.strftime('%Y-%m-%d'))
            tba1['Date'] = dateformat.strftime('%Y-%m-%d')
            #Adding a unique identifier column for each row in NewspaperFullPageImages
#            newspaperpageid.append(str(uuid.uuid4()))
            tba1['PublicationPageID'] = str(uuid.uuid4())
            tba1['PageNumber'] = pgNumber
            #Adding if page is the front or back page
            if pgNumber == 1: 
#                isFrontPages.append(True)
#                isBackPages.append(False)
                tba1['IsFrontPage'] = True
                tba1['IsBackPage'] = False
            elif pgNumber == numpages:
#                isFrontPages.append(False)
#                isBackPages.append(True)
                tba1['IsFrontPage'] = False
                tba1['IsBackPage'] = True
            else:
#                isFrontPages.append(False)
#                isBackPages.append(False)
                tba1['IsFrontPage'] = False
                tba1['IsBackPage'] = False
            issue_NewspaperFullPageImagesRows.append(tba1)
            
            
#        ## Loop through every page and get articles
#        for pgNumber1 in range(1,numpages+1):
#            ## Navigate to page
#            driver.get(f"{url}/page/{pgNumber1}")
#            time.sleep(1)
#            ## Get soup
#            pgSoup = BeautifulSoup(driver.page_source,'html.parser')
#            A = pgSoup.find_all(
#                    "div",
#                    {"class": "page page-cover zoom-off"}
#                )[0].find_all(
#                    "div",
#                    {"class":"block title contextmenu anim highlight"}
#                )
            ## Get articles on the page
            articleIDsJS = requests.get(
                    url="https://www.pressreader.com/api/pagesMetadata",
                    params={
                            "accessToken" : accessToken
                            ,"issue" : issueID
                            ,"pageNumbers" : pgNumber
                            }
                ).json()
            

        content = driver.page_source
        soup = BeautifulSoup(content, 'html.parser')
        #The below loops grabs all the article ID's on the page, and loops through them. Each loop takes the article ID, and clicks on that article to go to the text version of the article.
        articleIDtagsCount = len(soup.find_all("div", {"class": "page page-cover zoom-off"})[0].find_all("div", {"class":"block title contextmenu anim highlight"}))
        for i in range(articleIDtagsCount):
            content = driver.page_source
            soup = BeautifulSoup(content, 'html.parser')
            titlepagehtml = articleIDtagsCount[i]
            aid = titlepagehtml["article-id"]
            if len(soup.find_all("div", {"class": "page page-cover zoom-off"})[0].find_all("div",{"article-id":aid})) <=  3: #Only click the article if there is content.
                pass
            else:
                driver.find_element_by_id(titlepagehtml["id"]).click() #Click into the article
                time.sleep(6)
                try:
                    content = driver.page_source
                    soup = BeautifulSoup(content, 'html.parser')
                    articleid.append(aid)
                    #Append the columns in NewspaperContent. If no element exists, append the column with "N/A"
                    try:
                        headline.append(soup.find_all("article", {"aid":aid})[0].find_all("header")[0].getText().replace("\xad",""))
                    except:
                        headline.append("N/A")
                    try:
                        author.append(soup.find_all("article", {"aid":aid})[0].find_all("li", {"class":"art-author"})[0].getText().replace("\xad",""))
                    except:
                        author.append("N/A")
                    texthold = ""
                    #Loop through all text columns and append each to an empty string
                    for j in range(1,len(soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"}))):
                        texthold = texthold+soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"})[j].getText().replace("\xad","")
                    text.append(texthold)
                    imgs = soup.find_all("article", {"aid":aid})[0].find_all("img")
                    #Scrape all image URL's in the article. The entire page url is also returned, so the if statement removes these and saves them in a new column
                    for k in imgs:
                        if k["src"].find("page=") ==  -1:
                            articleimageurl.append(k["src"])
                            multiarticleid.append(aid)           
                        else:
                            joinpagelinks.append(k["src"])
                    fromnewspaperpageid.append(newspaperpageid[0])
                    time.sleep(2)
                    driver.find_element_by_css_selector("#btn_ImgMode span").click() #Return to the newspaper view mode
                    time.sleep(6)
                except:
                    driver.back()
                    time.sleep(6)
                    content = driver.page_source
                    soup = BeautifulSoup(content, 'html.parser')
            
        n = int(numpages)/2
        
        content = driver.page_source
        soup = BeautifulSoup(content, 'html.parser')
        
        for i in range(0,int(n)-1):
            driver.find_element_by_tag_name('body').send_keys(Keys.RIGHT)
            time.sleep(2)
            #The html returns roughly the ten pages to the right of the current page, so this filters out the html element that contain only the current page using string similarity
            leftpage= baselink[2*i+1]
            rightpage= baselink[2*i+2]
            content = driver.page_source
            soup = BeautifulSoup(content, 'html.parser')
            time.sleep(2)
            #left page
            for j in range(0,len(soup.find_all("div", {"class": "page page-left zoom-off"}))): #Looping through all the left pages returned in the HTML to find the current left page
                pageurlhtml = soup.find_all("div", {"class": "page page-left zoom-off"})[j]
                for ht in pageurlhtml:
                    if len(ht.find_all("img")) ==  0:
                        pass
                    else:
                        imgs = ht.find_all("img") #Extracts the image url's of all images within the looped element
                        for q in imgs:
                            img1 = q["src"]
                            if img1.find("page="+str(2*i+2)+"&") == -1: #Matches the image url's with the current page URL. If it finds a match, sets the HTML element as the one to use.
                                pass
                            else:
                                ind = j
            #The structure of the HTML changes randomly for some reason, so this if statement ensures we take the class that contains the information we require.
            #hh is the number of articles on the page
            if len(soup.find_all("div", {"class": "page page-left zoom-off"})[ind].find_all("div", {"class":"block title contextmenu anim highlight"})) ==  0:
                hh = len(soup.find_all("div", {"class": "page page-left zoom-off"})[ind].find_all("div", {"class":"block title contextmenu highlight anim"}))
            else:
                hh = len(soup.find_all("div", {"class": "page page-left zoom-off"})[ind].find_all("div", {"class":"block title contextmenu anim highlight"}))
            for k in range(0,hh): #Looping through each article
                for p in range(0,len(soup.find_all("div", {"class": "page page-left zoom-off"}))): #Getting the page image URL
                    pageurlhtml = soup.find_all("div", {"class": "page page-left zoom-off"})[p]
                    for ht in pageurlhtml:
                        if len(ht.find_all("img")) ==  0:
                            pass
                        else:
                            imgs = ht.find_all("img")
                            for q in imgs:
                                img1 = q["src"]
                                if img1.find("page="+str(2*i+2)+"&") == -1:
                                    pass
                                else:
                                    ind1 = p
                try:
                #The structure of the HTML changes randomly for some reason, so this if statement ensures we take the class that contains the information we require.
                    if len(soup.find_all("div", {"class": "page page-left zoom-off"})[ind1].find_all("div", {"class":"block title contextmenu anim highlight"})) ==  0:
                        lefthtml = soup.find_all("div", {"class": "page page-left zoom-off"})[ind1].find_all("div", {"class":"block title contextmenu highlight anim"})[k]
                    else:
                        lefthtml = soup.find_all("div", {"class": "page page-left zoom-off"})[ind1].find_all("div", {"class":"block title contextmenu anim highlight"})[k]
                    aid = lefthtml["article-id"]
                    if len(soup.find_all("div", {"class": "page page-left zoom-off"})[ind1].find_all("div",{"article-id":aid})) <=  3: #If the article contains content
                        pass
                    else:
                        driver.find_element_by_id(lefthtml["id"]).click() #Click into the text view of the article
                        time.sleep(6)
                        try:
                            content = driver.page_source
                            soup = BeautifulSoup(content, 'html.parser')
                            articleid.append(aid)
                            try:
                                headline.append(soup.find_all("article", {"aid":aid})[0].find_all("header")[0].getText().replace("\xad",""))
                            except:
                                headline.append("N/A")
                            try:
                                author.append(soup.find_all("article", {"aid":aid})[0].find_all("li", {"class":"art-author"})[0].getText().replace("\xad",""))
                            except:
                                author.append("N/A")
                            texthold = ""
                            for l in range(1,len(soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"}))):
                                texthold = texthold+soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"})[l].getText().replace("\xad","")
                            fromnewspaperpageid.append(newspaperpageid[2*i+1])
                            guid = str(uuid.uuid4())
                            articleguid.append(guid)
                            text.append(texthold)
                            imgs = soup.find_all("article", {"aid":aid})[0].find_all("img")
                            for m in imgs:
                                if m["src"].find("page=") ==  -1:
                                    articleimageurl.append(m["src"])
                                    multiarticleid.append(aid)
                                    fromarticleguid.append(guid)
                                else:
                                    joinpagelinks.append(m["src"])
                            time.sleep(2)
                            driver.find_element_by_css_selector("#btn_ImgMode span").click()
                            time.sleep(6)
                            content = driver.page_source
                            soup = BeautifulSoup(content, 'html.parser')
                        except: #Error handling - if for some reason there is an error, the code will go back to the page view and move to the next article
                            driver.back()
                            time.sleep(6)
                            content = driver.page_source
                            soup = BeautifulSoup(content, 'html.parser')
                except:
                    pass
                
        ##right page
        #This follows the exact same code as the left page
            for j in range(0,len(soup.find_all("div", {"class": "page page-right zoom-off"}))):
                pageurlhtml = soup.find_all("div", {"class": "page page-right zoom-off"})[j]
                for ht in pageurlhtml:
                    if len(ht.find_all("img")) ==  0:
                        pass
                    else:
                        imgs = ht.find_all("img")
                        for q in imgs:
                            img1 = q["src"]
                            if img1.find("page="+str(2*i+3)+"&") == -1:
                                pass
                            else:
                                ind = j
            if len(soup.find_all("div", {"class": "page page-right zoom-off"})[ind].find_all("div", {"class":"block title contextmenu anim highlight"})) ==  0:
                hh = len(soup.find_all("div", {"class": "page page-right zoom-off"})[ind].find_all("div", {"class":"block title contextmenu highlight anim"}))
            else:
                hh = len(soup.find_all("div", {"class": "page page-right zoom-off"})[ind].find_all("div", {"class":"block title contextmenu anim highlight"}))
            for k in range(0,hh):
                for p in range(0,len(soup.find_all("div", {"class": "page page-right zoom-off"}))):
                    pageurlhtml = soup.find_all("div", {"class": "page page-right zoom-off"})[p]
                    for ht in pageurlhtml:
                        if len(ht.find_all("img")) ==  0:
                            pass
                        else:
                            imgs = ht.find_all("img")
                            for q in imgs:
                                img1 = q["src"]
                                if img1.find("page="+str(2*i+3)+"&") == -1:
                                    pass
                                else:
                                    ind1 = p    
                try:
                    if len(soup.find_all("div", {"class": "page page-right zoom-off"})[ind1].find_all("div", {"class":"block title contextmenu anim highlight"})) ==  0:
                        righthtml = soup.find_all("div", {"class": "page page-right zoom-off"})[ind1].find_all("div", {"class":"block title contextmenu highlight anim"})[k]
                    else:
                        righthtml = soup.find_all("div", {"class": "page page-right zoom-off"})[ind1].find_all("div", {"class":"block title contextmenu anim highlight"})[k]
                    aid = righthtml["article-id"]
                    if len(soup.find_all("div", {"class": "page page-right zoom-off"})[ind1].find_all("div",{"article-id":aid})) <=  3:
                        pass
                    else:
                        driver.find_element_by_id(righthtml["id"]).click()
                        time.sleep(6)
                        try:
                            content = driver.page_source
                            soup = BeautifulSoup(content, 'html.parser')
                            articleid.append(aid)
                            try:
                                headline.append(soup.find_all("article", {"aid":aid})[0].find_all("header")[0].getText().replace("\xad",""))
                            except:
                                headline.append("N/A")
                            try:
                                author.append(soup.find_all("article", {"aid":aid})[0].find_all("li", {"class":"art-author"})[0].getText().replace("\xad",""))
                            except:
                                author.append("N/A")
                            texthold = ""
                            for l in range(1,len(soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"}))):
                                texthold = texthold+soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"})[l].getText().replace("\xad","")
                            text.append(texthold)
                            fromnewspaperpageid.append(newspaperpageid[2*i+2])
                            imgs = soup.find_all("article", {"aid":aid})[0].find_all("img")
                            guid = str(uuid.uuid4())
                            articleguid.append(guid)
                            for m in imgs:
                                if m["src"].find("page=") ==  -1:
                                    articleimageurl.append(m["src"])
                                    multiarticleid.append(aid)
                                    fromarticleguid.append(guid)
                                else:
                                    joinpagelinks.append(m["src"])
                            time.sleep(2)
                            driver.find_element_by_css_selector("#btn_ImgMode span").click()
                            time.sleep(6)
                            content = driver.page_source
                            soup = BeautifulSoup(content, 'html.parser')
                        except:
                            driver.back()
                            time.sleep(6)
                            content = driver.page_source
                            soup = BeautifulSoup(content, 'html.parser')
                except:
                    pass
            driver.find_element_by_tag_name('body').send_keys(Keys.RIGHT)
                  
        ##Back page
        content = driver.page_source
        soup = BeautifulSoup(content, 'html.parser')
        var1 = len(soup.find_all("div",
                                 {"class": "page page-back zoom-off"}
                                 )[0].find_all("div",
                                 {"class":"block title contextmenu anim highlight"}))
        for i in range(var1):
            content = driver.page_source
            soup = BeautifulSoup(content, 'html.parser')
            titlepagehtml = soup.find_all("div", {"class": "page page-back zoom-off"})[0].find_all("div", {"class":"block title contextmenu anim highlight"})[i]
            aid = titlepagehtml["article-id"]
            if len(soup.find_all("div", {"class": "page page-back zoom-off"})[0].find_all("div",{"article-id":aid})) <=  3:
                pass
            else:
                driver.find_element_by_id(titlepagehtml["id"]).click()
                time.sleep(6)
                try:
                    content = driver.page_source
                    soup = BeautifulSoup(content, 'html.parser')
                    articleid.append(aid)
                    fromnewspaperpageid.append(newspaperpageid[-1])
                    try:
                        headline.append(soup.find_all("article", {"aid":aid})[0].find_all("header")[0].getText().replace("\xad",""))
                    except:
                        headline.append("N/A")
                    author.append(soup.find_all("article", {"aid":aid})[0].find_all("li", {"class":"art-author"})[0].getText().replace("\xad",""))
                    texthold = ""
                    for j in range(1,len(soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"}))):
                        texthold = texthold+soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"})[j].getText().replace("\xad","")
                    text.append(texthold)
                    imgs = soup.find_all("article", {"aid":aid})[0].find_all("img")
                    guid = str(uuid.uuid4())
                    articleguid.append(guid)
                    for k in imgs:
                        if k["src"].find("page=") ==  -1:
                            articleimageurl.append(k["src"])
                            multiarticleid.append(aid)
                            fromarticleguid.append(guid)          
                        else:
                            joinpagelinks.append(k["src"])
                    time.sleep(2)
                    driver.find_element_by_css_selector("#btn_ImgMode span").click()
                    time.sleep(6)
                except:
                    driver.back()
                    time.sleep(6)
                    content = driver.page_source
                    soup = BeautifulSoup(content, 'html.parser')
        #Appending the final lists with the temporary lists just scraped
#        finalpaper.extend(paper)
#        finaldateadd.extend(date)
#        finalIsFrontPage.extend(isFrontPages)
#        findalIsBackPage.extend(isBackPages)
#        finalpagelinks.extend(pagelinks)
#        finalnewspaperpageid.extend(newspaperpageid)
        all_NewspaperFullPageImagesRows[myIssueID] = issue_NewspaperFullPageImagesRows

        finalarticleid.extend(articleid)
        finalheadline.extend(headline)
        finalauthor.extend(author)
        finaltext.extend(text)
        finaljoinpagelinks.extend(joinpagelinks)
        finalfromnewspaperpageid.extend(fromnewspaperpageid)
        finalarticleguid.extend(articleguid)

        finalmultiarticleid.extend(multiarticleid)
        finalarticleimageurl.extend(articleimageurl)
        finalfromarticleguid.extend(fromarticleguid)

#NewspaperFullPageImages = pd.DataFrame({
#    'NewspaperPageID': finalnewspaperpageid,
#    'Newspaper': finalpaper,
#    'Date': finaldateadd,
#    'IsFrontPage': finalIsFrontPage,
#    'IsBackPage' : finalIsBackPage,
#    'PageImageURL': finalpagelinks,
#    })
NewspaperFullPageImages = pd.DataFrame(
        helper.to_list(all_NewspaperFullPageImagesRows)
    )     
NewspaperContent = pd.DataFrame({
    'ArticleGUID': finalarticleguid,
    'ArticleID': finalarticleid,
    'Headline': finalheadline,
    'Author': finalauthor,
    'Text': finaltext,
    'PageImageURL': finaljoinpagelinks,
    'FromNewspaperPageID': finalfromnewspaperpageid,
    })
NewspaperArticleImages = pd.DataFrame({
    'ArticleID': finalmultiarticleid,
    'ArticleImagesURL': finalarticleimageurl,
    'FromArticleGUID': finalfromarticleguid})
    
#driver.close()

