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

## Login
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

publicationIDs = {     
    'NCHRS' : ['Herald Sun','heraldsun']
}

pID = "NCHRS"
pub_name,pub_name_lc = publicationIDs[pID]

pub_date_start = datetime(year=2021,month=4,day=15)
pub_date_end = datetime(year=2021,month=6,day=14)

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

    issueID = f'{pID}-{pub_date.strftime("%Y-%m-%d")}'
    href = f'{pID}/{pub_date.strftime("%Y/%m/%d")}'
    base_url = f"https://metros.smedia.com.au/{pub_name_lc}/get/{issueID}"
    referer = f'https://metros.smedia.com.au/{pub_name_lc}/default.aspx?publication=NCHRS'
    
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