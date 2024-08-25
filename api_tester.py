#!/usr/bin/python3

import requests
import json 

headers = {
    "ApplicationAccessKey": "V2-h5ESy-fTyv6-PQ0at-fdcIT-voQZE-0VfNa-vItTq-iEkrw",
    "content-type": "application/json"
}

def get_items(table):
    api_url = "https://api.appsheet.com/api/v2/apps/28d006e4-44c0-45e0-902f-6fb83e6f09d7/tables/" + table + "/Action"
    data = {
        "Action": "Find",
        "Properties": {},
        "Rows": []
    }
    return requests.post(api_url, data=json.dumps(data), headers=headers)



def get_item(table, selector):
    api_url = "https://api.appsheet.com/api/v2/apps/28d006e4-44c0-45e0-902f-6fb83e6f09d7/tables/" + table + "/Action"
    data = {
        "Action": "Find",
        "Properties": {
            "Selector": selector, 
        },
        "Rows": []
    }
    return requests.post(api_url, data=json.dumps(data), headers=headers)


def post_item(table, data):
    api_url = "https://api.appsheet.com/api/v2/apps/28d006e4-44c0-45e0-902f-6fb83e6f09d7/tables/" + table + "/Action"
    data = {
        "Action": "Add",
        "Properties": {},
        "Rows": data
    }
    return requests.post(api_url, data=json.dumps(data), headers=headers)
 

# r = get_items("Packages")
# print(r.status_code)
# print(r.text)
# print(r.content)
# print(r.headers)

# print ()
# print ()
# print ()

# r = get_item("Units", {"Unit": "Ω"})
# if r.status_code == 200:
#     print(r.json()[0]["Row ID"])
# r = post_item("Items", [{
#         "BarCode": "RE;S3;999;kO;Remove Me;1;",
#         "Value": "123",
#         "Unit": "Sxs2kIcGDhUXK57ekZLruJ",
#         "Amount": 1,
#         "Description": "Added from api, please remove me",
#         "Termination": "SMD",
#         "Package": "Z40VC5hP01K12UWHxVSWbq",
#         "Datasheet": "https://nohello.com",
#         "Category": "Resistor"
#     }])

# r = post_item("ApiTest", [{
#     "Enum": "TR",
#     "Name": "Test2ss2",
#     "Code": "8oOsDfQGHuDX2ayCwANRd9"
# }])

def print_resp(r):
    if r.status_code == 200:
        print (r.json())

# r = get_item("Items", "[Value] = 1")
# print_resp(r)

import csv

with open("rezystory_smd_0402.csv", newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        print(row)
