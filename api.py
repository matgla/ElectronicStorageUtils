#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# api.py
#
# Copyright (c) 2024 Mateusz Stadnik <matgla@live.com>
#
# Distributed under the terms of the MIT License.
#

import requests
import json

headers = {}
applicationId = None


def database_load_key_from_json(filepath):
    global headers
    global applicationId
    with open(filepath, "r") as file:
        j = json.loads(file.read())
        headers["ApplicationAccessKey"] = j["ApplicationKey"]
        headers["content-type"] = "application/json"
        applicationId = j["ApplicationId"]


cache = {}


def database_get_table(table):
    api_url = (
        "https://api.appsheet.com/api/v2/apps/"
        + applicationId
        + "/tables/"
        + table
        + "/Action"
    )
    data = {"Action": "Find", "Properties": {}, "Rows": []}
    if not table in cache:
        resp = requests.post(api_url, data=json.dumps(data), headers=headers)
        if resp.status_code != 200:
            print("Can't access table: " + table + " in external database")
            return {}

        if resp.content is None or len(resp.content) == 0:
            print("Empty table returned from database for: " + table)
            return {}

        cache[table] = json.loads(resp.content)

    return cache[table]


def database_get_item(table, selector):
    table = database_get_table(table)
    for element in table:
        if selector(element):
            return element
    return None


#    api_url = (
#        "https://api.appsheet.com/api/v2/apps/"
#        + applicationId
#        + "/tables/"
#        + table
#        + "/Action"
#    )
#    data = {"Action": "Find", "Properties": {"Selector": selector}, "Rows": []}
#    entry = table + str(hash(selector))
#    if not entry in cache:
#        resp = requests.post(api_url, data=json.dumps(data), headers=headers)
#        if resp.status_code != 200:
#            print("Can't access table: " + table + " in external database")
#            return {}
#
#        if resp.content == None or len(resp.content) == 0:
#            print("Empty table returned from database for: " + table)
#            return {}
#
#        cache[entry] = json.loads(resp.content)
#
#    return cache[entry]


def database_add_entry(table, data):
    api_url = (
        "https://api.appsheet.com/api/v2/apps/"
        + applicationId
        + "/tables/"
        + table
        + "/Action"
    )
    print("Posting: ", data)
    post_data = {"Action": "Add", "Properties": {}, "Rows": data}
    resp = requests.post(api_url, data=json.dumps(post_data), headers=headers)

    if resp.status_code != 200:
        print("Adding entry in table: " + table + " failed for: ", post_data)
        print(resp)
        print(resp.content)
        return False
    print(resp)
    print(resp.content)
    
    return True


component_codes_mapping = None


def database_get_component_codes_mapping():
    global component_codes_mapping
    if component_codes_mapping is not None:
        return component_codes_mapping
    codes = database_get_table("ComponentCodes")
    config = database_get_table("ComponentConfiguration")
    component_codes_mapping = {}
    for e in codes:
        ep = [x for x in config if x["Row ID"] == e["Configuration"]]
        if len(ep) > 0:
            name = ep[0]["Name"]
            component_codes_mapping[name] = e["Code"]
    return component_codes_mapping
