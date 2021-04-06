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

# **Step 1:** Load the required packages

# In[ ]:


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


# **Step 2:** Input the date range and the parent URL's as a list

# In[ ]:


startdate="2021-01-07"
enddate="2021-01-07"
newspaperlistchild=[
#        "https://www.pressreader.com/australia/the-west-australian/",
        "https://www.pressreader.com/australia/the-guardian-australia/",
#        "https://www.pressreader.com/australia/cockburn-gazette/"
        ]


# **Step 3:** Set up the web driver and log in to Press Reader. Note: you don't need to touch anything from here on out

# In[ ]:


start = datetime.datetime.strptime(startdate, "%Y-%m-%d")
end = datetime.datetime.strptime(enddate, "%Y-%m-%d")
date_generated = [start + datetime.timedelta(days=x) for x in range(0, (end-start).days+1)]

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
chromePath = r"K:\Technology Team\Python\Web Scraping\ChromeDrivers\v89\chromedriver.exe"
driver=webdriver.Chrome(chromePath, chrome_options=options)
driver.get('https://www.pressreader.com/')

time.sleep(random.uniform(15,20))
driver.find_element_by_link_text('Sign in').click()
time.sleep(random.uniform(2,4))
driver.find_element_by_id('SignInEmailAddress').send_keys('alison.gaskell@uk.initiative.com')
driver.find_element_by_xpath('//input[contains(@data-bind, "signIn.password")]').send_keys('FtrsSprt')
time.sleep(random.uniform(1,1.7))
driver.find_element_by_xpath('//button[normalize-space()="Sign in"]').click()
time.sleep(10)


# **Step 4:** Create the empty lists, and cycle through each newspaper date combination to generate the data

# In[ ]:


##Set up NewspaperFullPageImages dataframe
finalpaper=[]
finaldateadd=[]
finalfrontback=[]
finalpagelinks=[]
finalnewspaperpageid=[]

##Set up NewspaperContent dataframe
finalarticleid=[]
finalheadline=[]
finalauthor=[]
finaltext=[]
finaljoinpagelinks=[]
finalfromnewspaperpageid=[]
finalarticleguid=[]

##Set up NewspaperArticleImages	dataframe
finalmultiarticleid=[]
finalarticleimageurl=[]
finalfromarticleguid=[]

for news in newspaperlistchild:
    for dateformat in date_generated:

        ##Set up NewspaperFullPageImages dataframe
        paper=[]
        date=[]
        frontback=[]
        pagelinks=[]
        newspaperpageid=[]

        ##Set up NewspaperContent dataframe
        articleid=[]
        headline=[]
        author=[]
        text=[]
        joinpagelinks=[]
        fromnewspaperpageid=[]
        articleguid=[]

        ##Set up NewspaperArticleImages	dataframe
        multiarticleid=[]
        articleimageurl=[]
        fromarticleguid=[]
        
        finaldate=dateformat.strftime('%Y%m%d')
        
        ##Go to the website of the paper
        url=news+finaldate
        driver.get(url)
        time.sleep(15)
        content=driver.page_source
        soup = BeautifulSoup(content, 'html.parser')
        titlepagehtml = soup.find_all("div", {"class": "page page-cover zoom-off"})[0].find_all("img")[1]
        titlepage = titlepagehtml['src'] #Grabs the url for the cover page image 
        
        ##Scrape elements from first and last page of paper
        driver.find_element_by_tag_name('body').send_keys(Keys.LEFT)
        time.sleep(2)
        content=driver.page_source
        soup = BeautifulSoup(content, 'html.parser')
        backpagehtml = soup.find_all("div", {"class": "page page-back zoom-off"})[0].find_all("img")[1]
        backpage = backpagehtml['src'] #Grabs the url for the back page image
        numpages = backpage.split("page=")[1].split("&")[0] #The number of pages in the newspaper
        
        driver.find_element_by_tag_name('body').send_keys(Keys.RIGHT)
        
        baselink=[] #Used for locating which page to scrape from. More explained in row 145
        
        ##checkurl is the URL of the first page of the newspaper. Below takes the generic parts of the URL and extrapolates them across all pages to give the URL for each page and saves them to a folder.
        for i in range(1,int(numpages)+1):
            checkurl=titlepage.split("page=")[0]+"page="+str(i)+titlepage.split("page=1")[1]
            print(checkurl)
            pagelinks.append(checkurl) #Adding to column in NewspaperFullPageImages
            baselink.append(checkurl.split("&scale")[0])
            paper.append(news) #Adding to column in NewspaperFullPageImages
            date.append(dateformat.strftime('%Y-%m-%d')) #Adding to column in NewspaperFullPageImages
            if i == 1: #Adding if page is the front or back page
                frontback.append(1)
            else: 
                if i == int(numpages):
                    frontback.append(1)
                else:
                    frontback.append(0)
        raise ValueError
        
        for ll in pagelinks:
            newspaperpageid.append(str(uuid.uuid4())) #Adding a unique identifier column for each row in NewspaperFullPageImages

        content=driver.page_source
        soup = BeautifulSoup(content, 'html.parser')
        #The below loops grabs all the article ID's on the page, and loops through them. Each loop takes the article ID, and clicks on that article to go to the text version of the article.
        for i in range(0,len(soup.find_all("div", {"class": "page page-cover zoom-off"})[0].find_all("div", {"class":"block title contextmenu anim highlight"}))):
            content=driver.page_source
            soup = BeautifulSoup(content, 'html.parser')
            titlepagehtml = soup.find_all("div", {"class": "page page-cover zoom-off"})[0].find_all("div", {"class":"block title contextmenu anim highlight"})[i]
            aid = titlepagehtml["article-id"]
            if len(soup.find_all("div", {"class": "page page-cover zoom-off"})[0].find_all("div",{"article-id":aid})) <= 3: #Only click the article if there is content.
                pass
            else:
                driver.find_element_by_id(titlepagehtml["id"]).click() #Click into the article
                #time.sleep(6)
                try:
                    content=driver.page_source
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
                    texthold=""
                    #Loop through all text columns and append each to an empty string
                    for j in range(1,len(soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"}))):
                        texthold=texthold+soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"})[j].getText().replace("\xad","")
                    text.append(texthold)
                    imgs=soup.find_all("article", {"aid":aid})[0].find_all("img")
                    #Scrape all image URL's in the article. The entire page url is also returned, so the if statement removes these and saves them in a new column
                    for k in imgs:
                        if k["src"].find("page=") == -1:
                            articleimageurl.append(k["src"])
                            multiarticleid.append(aid)           
                        else:
                            joinpagelinks.append(k["src"])
                    fromnewspaperpageid.append(newspaperpageid[0])
                    #time.sleep(2)
                    driver.find_element_by_css_selector("#btn_ImgMode span").click() #Return to the newspaper view mode
                    #time.sleep(6)
                except:
                    driver.back()
                    time.sleep(6)
                    content=driver.page_source
                    soup = BeautifulSoup(content, 'html.parser')
            
        n=int(numpages)/2
        
        content=driver.page_source
        soup = BeautifulSoup(content, 'html.parser')
        
        for i in range(0,int(n)-1):
            driver.find_element_by_tag_name('body').send_keys(Keys.RIGHT)
            time.sleep(2)
            leftpage=baselink[2*i+1] #The html returns roughly the ten pages to the right of the current page, so this filters out the html element that contain only the current page using string similarity
            rightpage=baselink[2*i+2]
            content=driver.page_source
            soup = BeautifulSoup(content, 'html.parser')
            #time.sleep(2)
            #left page
            for j in range(0,len(soup.find_all("div", {"class": "page page-left zoom-off"}))): #Looping through all the left pages returned in the HTML to find the current left page
                pageurlhtml=soup.find_all("div", {"class": "page page-left zoom-off"})[j]
                for ht in pageurlhtml:
                    if len(ht.find_all("img")) == 0:
                        pass
                    else:
                        imgs=ht.find_all("img") #Extracts the image url's of all images within the looped element
                        for q in imgs:
                            img1=q["src"]
                            if img1.find("page="+str(2*i+2)+"&")==-1: #Matches the image url's with the current page URL. If it finds a match, sets the HTML element as the one to use.
                                pass
                            else:
                                ind=j
            #The structure of the HTML changes randomly for some reason, so this if statement ensures we take the class that contains the information we require.
            #hh is the number of articles on the page
            if len(soup.find_all("div", {"class": "page page-left zoom-off"})[ind].find_all("div", {"class":"block title contextmenu anim highlight"})) == 0:
                hh=len(soup.find_all("div", {"class": "page page-left zoom-off"})[ind].find_all("div", {"class":"block title contextmenu highlight anim"}))
            else:
                hh=len(soup.find_all("div", {"class": "page page-left zoom-off"})[ind].find_all("div", {"class":"block title contextmenu anim highlight"}))
            for k in range(0,hh): #Looping through each article
                for p in range(0,len(soup.find_all("div", {"class": "page page-left zoom-off"}))): #Getting the page image URL
                    pageurlhtml=soup.find_all("div", {"class": "page page-left zoom-off"})[p]
                    for ht in pageurlhtml:
                        if len(ht.find_all("img")) == 0:
                            pass
                        else:
                            imgs=ht.find_all("img")
                            for q in imgs:
                                img1=q["src"]
                                if img1.find("page="+str(2*i+2)+"&")==-1:
                                    pass
                                else:
                                    ind1=p
                try:
                #The structure of the HTML changes randomly for some reason, so this if statement ensures we take the class that contains the information we require.
                    if len(soup.find_all("div", {"class": "page page-left zoom-off"})[ind1].find_all("div", {"class":"block title contextmenu anim highlight"})) == 0:
                        lefthtml=soup.find_all("div", {"class": "page page-left zoom-off"})[ind1].find_all("div", {"class":"block title contextmenu highlight anim"})[k]
                    else:
                        lefthtml=soup.find_all("div", {"class": "page page-left zoom-off"})[ind1].find_all("div", {"class":"block title contextmenu anim highlight"})[k]
                    aid = lefthtml["article-id"]
                    if len(soup.find_all("div", {"class": "page page-left zoom-off"})[ind1].find_all("div",{"article-id":aid})) <= 3: #If the article contains content
                        pass
                    else:
                        driver.find_element_by_id(lefthtml["id"]).click() #Click into the text view of the article
                        #time.sleep(6)
                        try:
                            content=driver.page_source
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
                            texthold=""
                            for l in range(1,len(soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"}))):
                                texthold=texthold+soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"})[l].getText().replace("\xad","")
                            fromnewspaperpageid.append(newspaperpageid[2*i+1])
                            guid=str(uuid.uuid4())
                            articleguid.append(guid)
                            text.append(texthold)
                            imgs=soup.find_all("article", {"aid":aid})[0].find_all("img")
                            for m in imgs:
                                if m["src"].find("page=") == -1:
                                    articleimageurl.append(m["src"])
                                    multiarticleid.append(aid)
                                    fromarticleguid.append(guid)
                                else:
                                    joinpagelinks.append(m["src"])
                            #time.sleep(2)
                            driver.find_element_by_css_selector("#btn_ImgMode span").click()
                            #time.sleep(6)
                            content=driver.page_source
                            soup = BeautifulSoup(content, 'html.parser')
                        except: #Error handling - if for some reason there is an error, the code will go back to the page view and move to the next article
                            driver.back()
                            time.sleep(6)
                            content=driver.page_source
                            soup = BeautifulSoup(content, 'html.parser')
                except:
                    pass
                
        ##right page
        #This follows the exact same code as the left page
            for j in range(0,len(soup.find_all("div", {"class": "page page-right zoom-off"}))):
                pageurlhtml=soup.find_all("div", {"class": "page page-right zoom-off"})[j]
                for ht in pageurlhtml:
                    if len(ht.find_all("img")) == 0:
                        pass
                    else:
                        imgs=ht.find_all("img")
                        for q in imgs:
                            img1=q["src"]
                            if img1.find("page="+str(2*i+3)+"&")==-1:
                                pass
                            else:
                                ind=j
            if len(soup.find_all("div", {"class": "page page-right zoom-off"})[ind].find_all("div", {"class":"block title contextmenu anim highlight"})) == 0:
                hh=len(soup.find_all("div", {"class": "page page-right zoom-off"})[ind].find_all("div", {"class":"block title contextmenu highlight anim"}))
            else:
                hh=len(soup.find_all("div", {"class": "page page-right zoom-off"})[ind].find_all("div", {"class":"block title contextmenu anim highlight"}))
            for k in range(0,hh):
                for p in range(0,len(soup.find_all("div", {"class": "page page-right zoom-off"}))):
                    pageurlhtml=soup.find_all("div", {"class": "page page-right zoom-off"})[p]
                    for ht in pageurlhtml:
                        if len(ht.find_all("img")) == 0:
                            pass
                        else:
                            imgs=ht.find_all("img")
                            for q in imgs:
                                img1=q["src"]
                                if img1.find("page="+str(2*i+3)+"&")==-1:
                                    pass
                                else:
                                    ind1=p    
                try:
                    if len(soup.find_all("div", {"class": "page page-right zoom-off"})[ind1].find_all("div", {"class":"block title contextmenu anim highlight"})) == 0:
                        righthtml=soup.find_all("div", {"class": "page page-right zoom-off"})[ind1].find_all("div", {"class":"block title contextmenu highlight anim"})[k]
                    else:
                        righthtml=soup.find_all("div", {"class": "page page-right zoom-off"})[ind1].find_all("div", {"class":"block title contextmenu anim highlight"})[k]
                    aid = righthtml["article-id"]
                    if len(soup.find_all("div", {"class": "page page-right zoom-off"})[ind1].find_all("div",{"article-id":aid})) <= 3:
                        pass
                    else:
                        driver.find_element_by_id(righthtml["id"]).click()
                        #time.sleep(6)
                        try:
                            content=driver.page_source
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
                            texthold=""
                            for l in range(1,len(soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"}))):
                                texthold=texthold+soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"})[l].getText().replace("\xad","")
                            text.append(texthold)
                            fromnewspaperpageid.append(newspaperpageid[2*i+2])
                            imgs=soup.find_all("article", {"aid":aid})[0].find_all("img")
                            guid=str(uuid.uuid4())
                            articleguid.append(guid)
                            for m in imgs:
                                if m["src"].find("page=") == -1:
                                    articleimageurl.append(m["src"])
                                    multiarticleid.append(aid)
                                    fromarticleguid.append(guid)
                                else:
                                    joinpagelinks.append(m["src"])
                            #time.sleep(2)
                            driver.find_element_by_css_selector("#btn_ImgMode span").click()
                            #time.sleep(6)
                            content=driver.page_source
                            soup = BeautifulSoup(content, 'html.parser')
                        except:
                            driver.back()
                            time.sleep(6)
                            content=driver.page_source
                            soup = BeautifulSoup(content, 'html.parser')
                except:
                    pass
            driver.find_element_by_tag_name('body').send_keys(Keys.RIGHT)
                  
        ##Back page
        content=driver.page_source
        soup = BeautifulSoup(content, 'html.parser')
        for i in range(0,len(soup.find_all("div", {"class": "page page-back zoom-off"})[0].find_all("div", {"class":"block title contextmenu anim highlight"}))):
            content=driver.page_source
            soup = BeautifulSoup(content, 'html.parser')
            titlepagehtml = soup.find_all("div", {"class": "page page-back zoom-off"})[0].find_all("div", {"class":"block title contextmenu anim highlight"})[i]
            aid = titlepagehtml["article-id"]
            if len(soup.find_all("div", {"class": "page page-back zoom-off"})[0].find_all("div",{"article-id":aid})) <= 3:
                pass
            else:
                driver.find_element_by_id(titlepagehtml["id"]).click()
                #time.sleep(6)
                try:
                    content=driver.page_source
                    soup = BeautifulSoup(content, 'html.parser')
                    articleid.append(aid)
                    fromnewspaperpageid.append(newspaperpageid[-1])
                    try:
                        headline.append(soup.find_all("article", {"aid":aid})[0].find_all("header")[0].getText().replace("\xad",""))
                    except:
                        headline.append("N/A")
                    author.append(soup.find_all("article", {"aid":aid})[0].find_all("li", {"class":"art-author"})[0].getText().replace("\xad",""))
                    texthold=""
                    for j in range(1,len(soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"}))):
                        texthold=texthold+soup.find_all("article", {"aid":aid})[0].find_all("div", {"class":"col"})[j].getText().replace("\xad","")
                    text.append(texthold)
                    imgs=soup.find_all("article", {"aid":aid})[0].find_all("img")
                    guid=str(uuid.uuid4())
                    articleguid.append(guid)
                    for k in imgs:
                        if k["src"].find("page=") == -1:
                            articleimageurl.append(k["src"])
                            multiarticleid.append(aid)
                            fromarticleguid.append(guid)          
                        else:
                            joinpagelinks.append(k["src"])
                    #time.sleep(2)
                    driver.find_element_by_css_selector("#btn_ImgMode span").click()
                    #time.sleep(6)
                except:
                    driver.back()
                    time.sleep(6)
                    content=driver.page_source
                    soup = BeautifulSoup(content, 'html.parser')
        #Appending the final lists with the temporary lists just scraped
        finalpaper.extend(paper)
        finaldateadd.extend(date)
        finalfrontback.extend(frontback)
        finalpagelinks.extend(pagelinks)
        finalnewspaperpageid.extend(newspaperpageid)

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

NewspaperFullPageImages = pd.DataFrame ({'NewspaperPageID':finalnewspaperpageid,'Newspaper':finalpaper,'Date':finaldateadd,'FrontBack':finalfrontback,'PageImageURL':finalpagelinks})
NewspaperContent = pd.DataFrame ({'ArticleGUID':finalarticleguid,'ArticleID':finalarticleid,'Headline':finalheadline,'Author':finalauthor,'Text':finaltext,'PageImageURL':finaljoinpagelinks,'FromNewspaperPageID':finalfromnewspaperpageid})
NewspaperArticleImages = pd.DataFrame ({'ArticleID':finalmultiarticleid,'ArticleImagesURL':finalarticleimageurl,'FromArticleGUID':finalfromarticleguid})

driver.close()



root = r"C:\Users\oli.dernie\Documents\Automation tests\Aus\PressReader"
abS = [
       ("NewspaperFullPageImages",NewspaperFullPageImages),
       ("NewspaperContent",NewspaperContent),
       ("NewspaperArticleImages",NewspaperArticleImages)
       ]
for a,b in abS:
    b.to_excel(fr"{root}\{a} 9Jan21.xlsx")