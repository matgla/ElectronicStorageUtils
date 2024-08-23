#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# csvgen.py
#
# Copyright (c) 2024 Mateusz Stadnik <matgla@live.com>
#
# Distributed under the terms of the MIT License.
#

import argparse
import pandas as pd

from sys import exit

from api import *

argparser = argparse.ArgumentParser("QRCode and text label generator, with automatically appsheet update")
argparser.add_argument("--input", "-i", help="CSV file input with | separator")
argparser.add_argument("--qrcode", "-q", help="Generate QRCode image", required=False)
argparser.add_argument("--post", "-p", help="POST CSV to database", required=False)
argparser.add_argument("--api_key", "-k", help="JSON file with API keys", required=True)

args, _ = argparser.parse_known_args()
 
def build_barcode_text(element):
    if (not type(element.Category) is str):
        print ("Element has unknown category, dropping: ", element)
        exit(-1)

    if (not type(element.Code) is str):
        print ("Element has unknown code, dropping: ", element)
        exit(-1) 

    return chr(36) + database_get_component_codes_mapping()[element.Category] + chr(36) + element.Code

def build_label_text(element):
    label = ""
    if (hasattr(element, "Label") and type(element.Label) is str):
        label = element.Label
    elif (type(element.Value) is str):
        label = element.Value
        if (type(element.Unit) is str):
            label += " " + element.Unit
    return label

database_load_key_from_json(args.api_key)

with open(args.input, "r") as file:
    print("Processing file: " + args.input)
    reader = pd.read_csv(file)
    for i in reader.itertuples():
        if i.Index == 0:
            # first row is mapping for appsheet
            continue
        print("barcode:", build_barcode_text(i)) 
        print("label:", build_label_text(i))
        print("---")
