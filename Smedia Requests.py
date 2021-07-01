from datetime import datetime
import requests


UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'
publicationIDs = {     
    'NCHRS' : ['Herald Sun','heraldsun']
}

pID = "NCHRS"
pub_name,pub_name_lc = publicationIDs[pID]
pub_date = datetime(year=2021,month=6,day=10)
issueID = f'{pID}-{pub_date.strftime("%Y-%m-%d")}'
href = f'{pID}/{pub_date.strftime("%Y/%m/%d")}'
base_url = f"https://metros.smedia.com.au/{pub_name_lc}/get/{issueID}"
referer = f'https://metros.smedia.com.au/{pub_name_lc}/default.aspx?publication=NCHRS'

with requests.Session() as s:
    ## Authenticate?
    auth_req = s.get(
        url='https://heraldsun.digitaleditions.com.au/edition.php',
        params={
            'code' : pID
        }
    )
    
    ## Get `ts`
    ts_req = requests.get(
        url=f"{base_url}/settings.ashx",
        headers={
            'user-agent' : UA        
        },
        params={
            "kind" : "context",
            "href" : href
        }
    )
    ts_dt = datetime.strptime(ts_req.json()['timestamp'],"%a, %d %b %Y %H:%M:%S GMT")
    ts = ts_dt.strftime("%Y%m%d%H%M%S")
    
    ## Get information about the issue
    issue_info_req = requests.get(
        url=f"{base_url}/prxml.ashx",
        headers={
            'user-agent' : UA,
            'referer' : referer
        },
        params={
            "kind" : "doc",
            "href" : href,
            "ts"   : ts
        }
    )
    issue_info_js = issue_info_req.json()
    
    ## Get list of contentIDs
    contentIDs = [
        (content_dict['id'],pg_dict['l'])
        for pg_dict in issue_info_js['pages']
        for content_dict in pg_dict['en']
    ]



#image_url = "https://metros.smedia.com.au/heraldsun/get/NCHRS-2021-06-06/image.ashx?kind=block&href=NCHRS%2F2021%2F06%2F06&id=Ar0010901&ext=.png&ts=20210605154554"
#artic_url ="https://metros.smedia.com.au/heraldsun/get/NCHRS-2021-06-06/article.ashx?href=NCHRS%2F2021%2F06%2F06&id=ar08600&search=dreamtime&ts=20210605154554"
#articleID = 'Ar00106'
#article_req = requests.get(
#    url=f"{base_url}/article.ashx",
##        headers={
##            'user-agent' : UA,
##            'referer' : referer
##        },
#    params={
#        'href' : href,
#        'id' : articleID,
#        'ts' : ts        
#    }     
#)
#print(article_req)