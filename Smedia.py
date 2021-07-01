from datetime import datetime
import requests


UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'
publicationIDs = {     
    'NCHRS' : ['Herald Sun','heraldsun']
}

pID = "NCHRS"
pub_name,pub_name_lc = publicationIDs[pID]
pub_date = datetime(year=2021,month=6,day=6)
issueID = f'{pID}-{pub_date.strftime("%Y-%m-%d")}'
href = f'{pID}/{pub_date.strftime("%Y/%m/%d")}'
base_url = f"https://metros.smedia.com.au/{pub_name_lc}/get/{issueID}"
referer = f'https://metros.smedia.com.au/{pub_name_lc}/default.aspx?publication=NCHRS'


with requests.Session() as s:
    ## Login
    login_data = {
        "client_id":"AnudjFSZnp48OLKBaaB382z4LHeAfIS5",
        "redirect_uri":"https://www.heraldsun.com.au/remote/identity/auth/latest/login/callback.html?redirectUri=https%3A%2F%2Fwww.heraldsun.com.au%2Fdigitalprinteditions",
        "tenant":"newsprod",
        "response_type":"token id_token",
        "scope":"openid profile",
        "state":"hKFo2SBLS0NJcC12RXg5X3lRRXZnZGFsWnhYbldoWjljSTh0caFupWxvZ2luo3RpZNkgZzI0V1gySV82aU12c1dVVzkyLWlZRGVWQmZiYlZ2YV-jY2lk2SBBbnVkakZTWm5wNDhPTEtCYWFCMzgyejRMSGVBZklTNQ",
        "nonce":"AyZipVwJhPQfUOm0HPiHmEr.o8bFJTeY",
        "connection":"NewsCorp-Australia",
        "username":"kevin.alavy@futuressport.com",
        "password":"L1verpool",
        "popup_options":{},
        "sso":True,
        "_intstate":"deprecated",
        "_csrf":"ClqzmkE8-wXoWEoqs6c5YUFHHsp4VjjkUGQo",
        "audience":"newscorpaustralia",
        "site":"heraldsun",
        "auth0Client":"eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xNi4wIn0=",
        "prevent_sign_up":"true",
        "protocol":"oauth2"
    }
    login_req = s.post(
        url="https://login.newscorpaustralia.com/usernamepassword/login",
        headers={
            'user-agent' : UA
        },
        data=login_data
    )
    abc = 'https://login.newscorpaustralia.com/login?state=hKFo2SBvYzdzMWlFdFdBQTJOSGd3cUduU0k5MGdKLUQzNW5fLaFupWxvZ2luo3RpZNkgZFZnV0w3ZVpBTTdKeHpYM2prcS1ZbTJUX3ZxNzJ4ZWajY2lk2SBBbnVkakZTWm5wNDhPTEtCYWFCMzgyejRMSGVBZklTNQ&client=AnudjFSZnp48OLKBaaB382z4LHeAfIS5&protocol=oauth2&response_type=token%20id_token&scope=openid%20profile&audience=newscorpaustralia&site=heraldsun&redirect_uri=https%3A%2F%2Fwww.heraldsun.com.au%2Fremote%2Fidentity%2Fauth%2Flatest%2Flogin%2Fcallback.html%3FredirectUri%3Dhttps%253A%252F%252Fwww.heraldsun.com.au%252Fdigitalprinteditions&prevent_sign_up=true&nonce=T2a7nrPAKH4t8HB6RSrk7sEm00dCvumd&auth0Client=eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xNi4wIn0%3D'
    ## Get `ts`
    ts_req = requests.get(
        url=f"{base_url}/settings.ashx",
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
        params={
            "kind" : "doc",
            "href" : href,
            "ts"   : ts
        }
    )
    js = issue_info_req.json()
    
    
    
    image_url = "https://metros.smedia.com.au/heraldsun/get/NCHRS-2021-06-06/image.ashx?kind=block&href=NCHRS%2F2021%2F06%2F06&id=Ar0010901&ext=.png&ts=20210605154554"
    artic_url ="https://metros.smedia.com.au/heraldsun/get/NCHRS-2021-06-06/article.ashx?href=NCHRS%2F2021%2F06%2F06&id=ar08600&search=dreamtime&ts=20210605154554"
    articleID = 'Ar00106'
    article_req = requests.get(
        url=f"{base_url}/article.ashx",
#        headers={
#            'user-agent' : UA,
#            'referer' : referer
#        },
        params={
            'href' : href,
            'id' : articleID,
            'ts' : ts        
        }     
    )
    print(article_req)