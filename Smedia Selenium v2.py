from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from datetime import datetime, timedelta
from urllib.parse import quote
from time import sleep
from bs4 import BeautifulSoup as BS
import pandas as pd
from MyFunctions import (
    create_insert_query,
    run_sql_command,
    get_df_from_sqlQuery
)

def build_url(
    url,
    params
):
    url_to_return = url + "?"
    for k,v in params.items():
        url_to_return += f"{quote(k,safe='')}={quote(v,safe='')}&"
    return url_to_return[:-1]

driver = webdriver.Chrome(r"K:\Technology Team\Python\Web Scraping\ChromeDrivers\v91\chromedriver.exe")

## Login to Herald stuff
driver.get("https://www.heraldsun.com.au/login")
WebDriverWait(
    driver,
    20
).until(
    EC.presence_of_element_located(
            (
                By.XPATH,
                "//input[@name='email']"
            )
    )
)
sleep(3)
driver.find_element_by_xpath("//input[@name='email']").send_keys('kevin.alavy@futuressport.com')
driver.find_element_by_xpath("//input[@name='password']").send_keys('L1verpool')
driver.find_element_by_xpath("//button[@name='submit']").click()
sleep(7)
driver.find_element_by_xpath("//p[@class='readnow']").click()
sleep(3)

## Login to Age stuff
#driver.get("https://www.theage.com.au/login")
#WebDriverWait(
#    driver,
#    20
#).until(
#    EC.presence_of_element_located(
#            (
#                By.XPATH,
#                "//input[@name='emailAddress']"
#            )
#    )
#)
#sleep(3)
#driver.find_element_by_xpath("//input[@name='emailAddress']").send_keys('futuressport@gmail.com')
#driver.find_element_by_xpath("//input[@name='password']").send_keys('Goldwing1')
#driver.find_element_by_xpath("//button[@type='submit']").click()
#sleep(7)
##driver.get('https://todayspaper.smedia.com.au/theage/default.aspx')
#driver.get('https://www.theage.com.au/todays-newspaper')
#driver.find_element_by_xpath("//p[@class='readnow']").click()

apr_15_2021 = datetime(year=2021,month=4,day=15)
jun_14_2021 = datetime(year=2021,month=6,day=14)
feb_1_2021 = datetime(year=2021,month=2,day=1)

publicationIDs = {     
#    'SMH' : ['Sydney Morning Herald','smh',feb_1_2021,jun_14_2021],
    'NCAUS' : ['The Australian','theaustralian',apr_15_2021,jun_14_2021],
#    'NCTELE' : ['The Daily Telegraph (Sydney)','dailytelegraph',apr_15_2021,jun_14_2021],
#    'AGE' : ['The Age','theage',feb_1_2021,jun_14_2021],
#    'NCCM'  : ['The Courier Mail','couriermail',apr_15_2021,jun_14_2021],
#    'NCADV' : ['The Advertiser','theadvertiser',apr_15_2021,jun_14_2021],
#    'NCHRS' : ['Herald Sun','heraldsun',apr_15_2021,jun_14_2021],
}

#pID = "NCADV"
for pID in publicationIDs.keys():
    
    pub_name,pub_name_lc,pub_date_start,pub_date_end = publicationIDs[pID]

    age_pID = pID in ['AGE','SMH']

    if age_pID:
#        driver.get(f"https://{pub_name_lc}.digitaleditions.com.au/index.php?silentlogin=1")
        driver.get(f"https://{pub_name_lc}.com.au/login")
        sleep(2)
        driver.find_element_by_xpath("//input[@name='emailAddress']").send_keys('futuressport@gmail.com')
#        driver.find_element_by_xpath("//input[@id='email']").send_keys('futuressport@gmail.com')
        driver.find_element_by_xpath("//input[@name='password']").send_keys('Goldwing1')
#        driver.find_element_by_xpath("//input[@id='password']").send_keys('Goldwing1')
        if pID == 'AGE':
            driver.find_element_by_xpath("//input[@name='btnLogin']").click()
        else:
#            driver.find_element_by_xpath("//img[@src='images/btn-sign in.png']").click()
#            driver.find_element_by_xpath('//*[@id="loginform"]/table/tbody/tr[1]/td[6]/a/img').click()
            driver.find_element_by_xpath("//button[@type='submit']").click()
        sleep(5)
        driver.get(f'https://www.{pub_name_lc}.com.au/todays-newspaper')
    else:
        driver.get(f"https://{pub_name_lc}.digitaleditions.com.au/index.php?silentlogin=1")
        sleep(2)        
        driver.find_element_by_xpath("//p[@class='readnow']").click()
    sleep(5)
        
    ## For some reason, `dailytelegraph` is used initally then `thedailytelegraph`
    ##    same for `couriermail`
    if pub_name_lc in ['dailytelegraph','couriermail']:
        pub_name_lc = f'the{pub_name_lc}'
    
    
    pub_dates = [(pub_date_start+timedelta(days=D)).date()
                    for D in range((pub_date_end-pub_date_start).days+1)]
    
    for pub_date in pub_dates:
        ## Check it hasn't been scraped already
        sql_check_df = get_df_from_sqlQuery(
            sqlQuery="SELECT DISTINCT PublicationName,PublicationDate FROM SmediaArticles",
            database="PhotoTextTrack"
        )
        if (pub_name,pub_date) in [tuple(x) for x in sql_check_df.to_numpy()]:
            print([pub_name,pub_date], "<--- already done")
            continue
        else:
            print([pub_name,pub_date], "<--- in progress")
            
        ## The Australian doesn't run on Sundays
        if (pub_name == 'The Australian') & (pub_date.weekday() == 6):
            continue
    
        issueID = f'{pID}-{pub_date.strftime("%Y-%m-%d")}'
        href = f'{pID}/{pub_date.strftime("%Y/%m/%d")}'
        start_bit = 'todayspaper' if age_pID else 'metros'
        base_url = f"https://{start_bit}.smedia.com.au/{pub_name_lc}/get/{issueID}"
        if pID == 'NCAUS':
            base_url = f'https://{pub_name_lc}.smedia.com.au/HTML5/get/{issueID}'
#        referer = f'https://{start_bit}.smedia.com.au/{pub_name_lc}/default.aspx?publication=NCHRS'
        
        # Get `ts`
        sleep(3)
        ts_url = build_url(
            url=f"{base_url}/settings.ashx",
            params={
                "kind" : "context",
                "href" : href
            }
        )
        driver.get(ts_url)
        ts_js = json.loads(
            BS(driver.page_source,"html.parser").text
        )
        ts_dt = datetime.strptime(ts_js['timestamp'],"%a, %d %b %Y %H:%M:%S GMT")
        ts = ts_dt.strftime("%Y%m%d%H%M%S")
        
        ## Get information about the issue
        issue_info_url = build_url(
            url=f"{base_url}/prxml.ashx",
            params={
                "kind" : "doc",
                "href" : href,
                "ts"   : ts
            }
        )
        driver.get(issue_info_url)
        issue_info_js = json.loads(
            BS(driver.page_source,'html.parser').text        
        )
        
        ## Get list of contentIDs
        contentIDs = [
            (content_dict['id'],pg_dict['l'])
            if "l" in pg_dict else
            (content_dict['id'],None)
            for pg_dict in issue_info_js['pages']
            for content_dict in pg_dict['en']
        ]
        #
        row_list = []
        for contentID,page in contentIDs:
            if contentID.startswith('Ar'):
        #contentID = 'Ar00104'
                article_url = build_url(
                    url=f"{base_url}/article.ashx",
                    params={
                        'href' : href,
                        'id' : contentID.lower(),
                        'ts' : ts,
                        'search' : 'dog'
                    }     
                )
                driver.get(article_url)
                sleep(1)
                article_text = BS(driver.page_source,"html.parser").text
                row_dict = {
                    'ArticleID' : contentID,
                    'Page' : page,
                    'Text' : article_text
                }
                row_list.append(row_dict)
        #    elif contentID.startswith("Pc"):
        #        image_url = build_url(
        #            url=f"{base_url}/image.ashx",
        #            params={
        #                "kind" : "block",
        #                "href" : href,
        #                "id" : contentID,
        #                "ext" : ".png",
        #                "ts" : ts
        #            }
        #        )
        #        print(image_url)
        
        
        df = pd.DataFrame(row_list)
        df.insert(0,'PublicationDate',pub_date)
        df.insert(0,'PublicationName',pub_name)
        columnDict = {
            'PublicationName' : 'str',
            'PublicationDate' : 'Date',
            'ArticleID' : 'str',
            'Page' : 'str',
            'Text' : 'str'        
        }
        
        insert_query = create_insert_query(
            df=df,
            columnDict=columnDict,
            sqlTableName='SmediaArticles'
        )
        run_sql_command(
            sqlQuery=insert_query,
            database="PhotoTextTrack"
        )