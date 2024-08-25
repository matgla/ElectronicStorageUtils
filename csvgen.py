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
from api import database_get_item
import pandas as pd
import matplotlib.font_manager
import json

from sys import exit

from api import *
from qr import *

from PIL import Image, ImageFont, ImageDraw
import PIL

argparser = argparse.ArgumentParser(
    "QRCode and text label generator, with automatically appsheet update"
)
argparser.add_argument("--input", "-i", help="CSV file input with | separator", required=True)
argparser.add_argument("--output", "-o", help="Output filename", required=True)
argparser.add_argument("--qrcode", "-q", action="store_true", help="Generate QRCode image", required=False)
argparser.add_argument("--post", "-p", action="store_true", help="POST CSV to database", required=False)
argparser.add_argument("--api_key", "-k", help="JSON file with API keys", required=True)
argparser.add_argument(
    "--tape_height", "-t", help="Printer type height in pixels", required=True
)
argparser.add_argument("--font", "-f", help="Text font")
argparser.add_argument("--font_size", "-fs", type=int, default=12, help="Text font size")
argparser.add_argument("--font_weight", "-fw", default="Regular", help="Text font weight: regular/italic/bold")



args, _ = argparser.parse_known_args()


def build_barcode_text(element):
    if not "Category" in element or element["Category"] == "":
        print("Element has unknown category, dropping: ", element)
        exit(-1)

    if not "Code" in element or element["Code"] == "":
        print("Element has unknown code, dropping: ", element)
        exit(-1)

    return (
        chr(36)
        + database_get_component_codes_mapping()[element["Category"]]
        + chr(36)
        + element["Code"]
    )


def build_tape_image(qrcodes, labels):
    widths, heights = zip(*(i.size for i in qrcodes))
    text_widths, text_heights = zip(*(i.size for i in labels))
    separator_width = 5 
    total_width = (
        sum(widths)
        + separator_width * len(qrcodes)
        + sum(text_widths)
        + len(labels) * separator_width)

    tape_height = int(args.tape_height)
    tape = Image.new("RGB", (total_width, tape_height), (255, 255, 255))
    x_offset = 0
    for i in range(0, len(labels)):
        qr = qrcodes[i]
        label = labels[i]
        tape.paste(qr, (x_offset, int((tape_height - qr.size[1]) / 2)))
        x_offset += qr.size[0] + separator_width
        tape.paste(label, (x_offset, int((tape_height - label.size[1]) / 2)))
        x_offset += label.size[0] + separator_width

    return tape


def build_label_text(element):
    label = ""
    if "Label" in element and element["Label"] != "": 
        label = element["Label"]
    elif "Value" in element and element["Value"] != "":
        label = element["Value"]
        if "Unit" in element and element["Unit"] != "":
            label += element["Unit"]
    return label


# https://stackoverflow.com/a/72615170
def text_to_image(text, font_path=None, font_size=24, font_align="center"):
    if font_path is None:
        font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(font_path, font_size)

    timg = Image.new("RGB", (2, 2), (255, 255, 255))
    d = ImageDraw.Draw(timg)

    width = int(d.textlength(text, font)) + 2
    height = font_size

    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, font=font, fill="black", font_align=font_align)
    img.save("r" + text[0] + ".png")
    if width < int(args.tape_height):
        img = img.rotate(90, PIL.Image.NEAREST, expand=1)
    return img


database_load_key_from_json(args.api_key)

qrcodes = []
labels = []

font = None
if args.font:
    for filename in matplotlib.font_manager.findSystemFonts(): 
        try:
            test_font = ImageFont.FreeTypeFont(filename)
            name, weight = test_font.getname()
            if args.font == name:
                if weight.lower() == args.font_weight.lower():
                    font = filename
        except OSError:
            pass

    
    if font == None:
        print("Can't find font \"" + args.font + "\": " + args.font_weight + " - using system default")

first_row = {}

with open(args.input, "r") as file:
    print("Processing file: " + args.input)
    reader = pd.read_csv(file)
    data = json.loads(reader.to_json())
    
    elements = []
    for entry in data:
        for key in data[entry]: 
            if key == "0":
                first_row[entry] = data[entry][key]
                continue 

            if int(key) > len(elements):
                elements.append({})
            elements[int(key) - 1][entry] = data[entry][key]

    for i in range(0, len(elements)):
        elements[i]["BarCode"] = build_barcode_text(elements[i])



if args.qrcode:
    for element in elements: 
        qrcodes.append(generate_qrcode(element["BarCode"]))
        labels.append(text_to_image(build_label_text(element), font, args.font_size))

    image = build_tape_image(qrcodes, labels)
    image.save(args.output)

if args.post:
    print(first_row)
    for i in range(0, len(elements)):
        keys_to_remove = []
        for key in elements[i]:
            if key in first_row and first_row[key] != None and len(first_row[key].strip()) != 0:
                print("Fixing key: ", key, "with: ", first_row[key])
                if "ref:" in first_row[key].lower():
                    data = first_row[key].split(":")
                    if len(data) < 2:
                        print("No table or column provided, expected format: ref:<table>:<column>")
                        exit(-1) 
                    table = data[1] 
                    column = data[2]
                    selector = "FILTER(" + table + ", [" + column + "] = \"" + elements[i][key] + '")'
                    r = database_get_item(table, selector)
                    print("Fixing reference from table: " + table + ", column: " + column)
                    if (len(r) < 1):
                        print("Referenced value not found")
                    elements[i][key] = r[0]["Row ID"]        

                if first_row[key].lower() == "int":
                    elements[i][key] = str(int(elements[i][key]))

                if first_row[key].lower() == "none":
                    keys_to_remove.append(key)
        for key in keys_to_remove: 
            del elements[i][key]

    if database_add_entry("Items", elements):
        print("POST Successful!")
