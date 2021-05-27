import requests
from datetime import datetime
S = datetime.now()
print(S)

#listOfCIDs = [

#'1970',
#'8587',
#'6794',
#'1968',
#'1720',
#            '1690',
#            '8992',
#            '6692',
#            '1120', # The Daily Telegraph (Sydney) doesn't work
#            '7004',
#            '9j66',
#'6733',
            #'1806', # The Sunday Telegraph (Sydney) doesn't work
#'9029',
#'1763',
#'1700',
#            '9a63',
#        ]
#r = requests.post(
#        url="https://fsepressreaderscraper.azurewebsites.net/api/HttpTrigger1",
#        json={
#                "listOfCIDs" : listOfCIDs,
#                "startDate" : "2021-02-07",
#                "endDate" : "2021-02-23"
#                })
#E = datetime.now()
#print(r)
#print(r.text)
#print(E-S)
#print(E)

CIDs = [
'1043',
'1048',
'1039',
'1069',
'1071',
'1237',
'1070',
'1259',
'1190',
'1545',
'1029',
'1054',
'9xvz',
'1702',
'1191',
'9029',
        ]

JS = [
      {
                "publicationCID" : cid,
                "startDate" : "2021-05-08",
                "endDate" : "2021-05-23"
        }
      for cid in CIDs
      
      ]

r = requests.post(
        url="https://fsepressreaderscraper.azurewebsites.net/api/HttpTriggerAddToQueue",
        json=JS)

print(r)
print(r.text)
