import random
import time
from selenium import webdriver

def to_list(dicto):
    returnMe = []
    for key,value in dicto.items():
        returnMe.extend(value)
    return returnMe


def get_driver_and_login():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    chromePath = r"K:\Technology Team\Python\Web Scraping\ChromeDrivers\v89\chromedriver.exe"
    driver = webdriver.Chrome(chromePath, options=options)
    driver.get('https://www.pressreader.com/')
    
    time.sleep(random.uniform(15,20))
    driver.find_element_by_link_text('Sign in').click()
    time.sleep(random.uniform(2,4))
    driver.find_element_by_id('SignInEmailAddress').send_keys('alison.gaskell@uk.initiative.com')
    driver.find_element_by_xpath('//input[contains(@data-bind, "signIn.password")]').send_keys('FtrsSprt')
    time.sleep(random.uniform(1,1.7))
    driver.find_element_by_xpath('//button[normalize-space() = "Sign in"]').click()
    time.sleep(10)
    return driver

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