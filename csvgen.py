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
import re

from sys import exit

from api import *
from qr import *

from PIL import Image, ImageFont, ImageDraw
import PIL

argparser = argparse.ArgumentParser(
    "QRCode and text label generator, with automatically appsheet update"
)
argparser.add_argument(
    "--input", "-i", help="CSV file input with | separator", required=True
)
argparser.add_argument(
    "--qrcode", "-q", help="Generate QRCode image", required=False
)
argparser.add_argument(
    "--qrcode_pixel", "-qs", help="QRCode pixel size", default=2, type=int, required=False
)

argparser.add_argument(
    "--post", "-p", action="store_true", help="POST CSV to database", required=False
)
argparser.add_argument(
    "--only_label", "-ol", action="store_true", help="Generate only labels without QRCodes"
)
argparser.add_argument(
    "--separator", "-sw", type=int, default=10, help="Separator width between elements in pixels"
)
argparser.add_argument("--api_key", "-k", help="JSON file with API keys", required=True)
argparser.add_argument(
    "--tape_height", "-t", type=int, default=76, help="Printer type height in pixels"
)
argparser.add_argument("--font", "-f", help="Text font")
argparser.add_argument(
    "--font_size", "-fs", type=int, default=24, help="Text font size"
)
argparser.add_argument("-font_height_offset", "-fho", type=int, default=0, help="Font offset to fix offset in font")
argparser.add_argument(
    "--font_weight",
    "-fw",
    default="Regular",
    help="Text font weight: regular/italic/bold",
)
argparser.add_argument(
    "--label_format", "-lf", help="Label format, CSV columns may be accessed via ::, example \'Resistor :Value: :Unit:\' will for example produce label like 'Resistor 123 Ohm'"
)


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


def build_tape_image(qrcodes, labels, rotated):
    widths = []
    text_widths = [] 
    if not args.only_label:
        widths, _ = zip(*(i.size for i in qrcodes))
    if not args.label_format == None and not args.label_format.strip() == "": 
        text_widths, _ = zip(*(i.size for i in labels))

    separator_width = args.separator
    
    total_width = (
        sum(widths)
        + sum(text_widths)
    )
    if not args.only_label:
        total_width += separator_width * len(qrcodes)
    if not args.label_format == None and not args.label_format.strip() == "": 
        total_width += len(labels) * separator_width
    tape_height = int(args.tape_height)
    tape = Image.new("RGB", (total_width, tape_height), (255, 255, 255))
    x_offset = 0
    size = len(qrcodes)
    if len(labels) > size:
        size = len(labels)

    for i in range(0, size):
        qr = None
        label = None
        if i < len(qrcodes): 
            qr = qrcodes[i]
        if i < len(labels): 
            label = labels[i]

        if not args.only_label and qr is not None:
            tape.paste(qr, (x_offset, int((tape_height - qr.size[1]) / 2)))
            x_offset += qr.size[0] + separator_width
      
        if label is not None and not args.label_format is None and not args.label_format == "": 
            tape.paste(label, (x_offset, int((tape_height - label.size[1]) / 2) + args.font_height_offset))
            print (label.size[0], label.size[1])
            x_offset += label.size[0] + separator_width

    return tape


def build_label_text(element):
    if args.label_format == None or args.label_format.strip() == "":
        return ""

    label = args.label_format

    placeholders = re.findall(r':(.*?):', args.label_format)
    for placeholder in placeholders:
        key = placeholder.replace(":", "")
        if not key in element:
            print ("Key '" + key + "' not found in element:", element)
        value = element[key] 
        if value == None:
            value = ""
        value = value.strip()
        label = label.replace(":" + key + ":", value)        

    return label 


# https://stackoverflow.com/a/72615170
def text_to_image(text, font_path=None, font_size=24, font_align="center"):
    if font_path is None:
        font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(font_path, font_size)

    timg = Image.new("RGB", (2, 2), (255, 255, 255))
    d = ImageDraw.Draw(timg)
    rotate = False 
    width = int(d.textlength(text, font)) + 2 
    if width < int(args.tape_height):
        height = font_size
        rotate = True
    else:
        height = args.tape_height#font_size
        rotate = False 

    if abs(args.font_height_offset) > 0:
        height += abs(args.font_height_offset)

    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    if rotate: 
        draw.text((0, 0), text, font=font, fill="black", font_align=font_align)
        img = img.rotate(90, PIL.Image.NEAREST, expand=1)
    else:
        draw.text((0, height/2 - font_size/2), text, font=font, fill="black", font_align=font_align)

    return img, rotate


database_load_key_from_json(args.api_key)

qrcodes = []
labels = []
rotated = []

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
        print(
            "Can't find font \""
            + args.font
            + '": '
            + args.font_weight
            + " - using system default"
        )

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
        qrcodes.append(generate_qrcode(element["BarCode"], args.qrcode_pixel))
        label, rotate = text_to_image(build_label_text(element), font, args.font_size)
         
        labels.append(label)
        rotated.append(rotate)

    print("QRCODES: ", len(qrcodes))
    image = build_tape_image(qrcodes, labels, rotated)
    image.save(args.qrcode)

to_post = []

if args.post:
    for i in range(0, len(elements)):
        print("----------------", i, "---------------:", elements[i]["Label"])
        keys_to_remove = []
        if database_get_item(
            "Items", lambda a: a["BarCode"] == elements[i]["BarCode"]
        ):
            continue

        for key in elements[i]:
            if (
                key in first_row
                and first_row[key] != None
                and len(first_row[key].strip()) != 0
            ):
                print("Fixing key: ", key, "with: ", first_row[key])
                if "ref:" in first_row[key].lower():
                    data = first_row[key].split(":")
                    if len(data) < 2:
                        print(
                            "No table or column provided, expected format: ref:<table>:<column>"
                        )
                        exit(-1)
                    table = data[1]
                    column = data[2]
                    r = database_get_item(
                        table, lambda a: a[column] == elements[i][key]
                    )

                    print(
                        "Fixing reference from table: " + table + ", column: " + column
                    )
                    if r is None:
                        print("Referenced value not found")
                        exit(-1)
                    elements[i][key] = r["Row ID"]

                if first_row[key].lower() == "int":
                    elements[i][key] = str(int(elements[i][key]))
               
                if first_row[key].lower() == "none":
                    keys_to_remove.append(key)
            if elements[i][key] == None or str(elements[i][key]).lower() == "none":
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del elements[i][key]

        print("Posting ID: ", i)
        to_post.append(elements[i])
    if database_add_entry("Items", to_post):
        print("POST Successful!")
    else:
        exit(-1)
