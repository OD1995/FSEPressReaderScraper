import logging
from bs4 import BeautifulSoup as BS
from selenium import webdriver
import azure.functions as func
import pyodbc
from azure.storage.blob import BlockBlobService
import uuid

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


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    ## Create the driver with options
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome("/usr/local/bin/chromedriver", chrome_options=chrome_options)
    logging.info("Driver created")
    ## Go to time.is and get the time
    driver.get("https://time.is/")
    logging.info("site navigated to")
    soup = BS(driver.page_source,'html.parser')
    logging.info("soup retrieved")
    clock0_bg = soup.find("div",{"id" : "clock0_bg"})
    currentTime = "".join([
        x.text
        for x in clock0_bg.find_all("span")
        ])
    ## Take screenshot and save it
    cs = "DefaultEndpointsProtocol=https;AccountName=fsecustomvisionimages;AccountKey=0gbOTBrl68MCGXlu6vHRK6DyQOIjRI5HRgTmfReCDW2cTmUnkCITP7DBRme9zI2yRsdWOrPxkDdz3v8Ti5Q3Zw==;EndpointSuffix=core.windows.net"
    block_blob_service.create_blob_from_bytes(
        container_name="test",
        blob_name=str(uuid.uuid4()) + ".png",
        blob=driver.get_screenshot_as_png()
    )
    ## Send to SQL
    Q = f"""INSERT INTO DockerTesting ([Value]) VALUES ('{currentTime}')"""
    logging.info(f"Q: {Q}")
    run_sql_command(
        sqlQuery=Q,
        database="TestDb"
    )
    ## This is a tiny and pointless change
    logging.info("command run")
    return func.HttpResponse(
             currentTime,
             status_code=200
    )
    driver.quit()
