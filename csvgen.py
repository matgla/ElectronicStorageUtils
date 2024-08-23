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
from qr import *

from PIL import Image, ImageFont, ImageDraw
import PIL

argparser = argparse.ArgumentParser(
    "QRCode and text label generator, with automatically appsheet update"
)
argparser.add_argument("--input", "-i", help="CSV file input with | separator")
argparser.add_argument("--output", "-o", help="Output filename")
argparser.add_argument("--qrcode", "-q", help="Generate QRCode image", required=False)
argparser.add_argument("--post", "-p", help="POST CSV to database", required=False)
argparser.add_argument("--api_key", "-k", help="JSON file with API keys", required=True)
argparser.add_argument(
    "--tape_height", "-t", help="Printer type height in pixels", required=True
)

args, _ = argparser.parse_known_args()


def build_barcode_text(element):
    if not type(element.Category) is str:
        print("Element has unknown category, dropping: ", element)
        exit(-1)

    if not type(element.Code) is str:
        print("Element has unknown code, dropping: ", element)
        exit(-1)

    return (
        chr(36)
        + database_get_component_codes_mapping()[element.Category]
        + chr(36)
        + element.Code
    )


def build_tape_image(qrcodes, labels):
    widths, heights = zip(*(i.size for i in qrcodes))
    text_widths, text_heights = zip(*(i.size for i in labels))
    separator_width = 10
    total_width = (
        sum(widths)
        + separator_width * len(qrcodes)
        + sum(text_widths)
        + len(labels) * separator_width
    )

    tape_height = int(args.tape_height)
    tape = Image.new("RGB", (total_width, tape_height), (255, 255, 255))
    x_offset = 0
    for i in range(0, len(labels)):
        qr = qrcodes[i]
        label = labels[i]
        tape.paste(qr, (x_offset, int((tape_height - qr.size[1]) / 2)))
        x_offset += qr.size[0]
        tape.paste(label, (x_offset, 0))  # int((tape_height - label.size[1]) / 2)))
        x_offset += label.size[0]

    return tape


def build_label_text(element):
    label = ""
    if hasattr(element, "Label") and type(element.Label) is str:
        label = element.Label
    elif type(element.Value) is str:
        label = element.Value
        if type(element.Unit) is str:
            label += " " + element.Unit
    return label


# https://stackoverflow.com/a/72615170
def text_to_image(text, font_path=None, font_size=24, font_align="center"):
    if font_path is None:
        font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(font_path, font_size)

    ascent, descent = font.getmetrics()
    width = font.getmask(text).getbbox()[2]
    height = font.getmask(text).getbbox()[3] + descent

    print(width, height)
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, font=font, fill="black", font_align=font_align)
    if box[1] < int(args.tape_height):
        img = img.rotate(90, PIL.Image.NEAREST, expand=1)
    img.save("f.png")
    return img


database_load_key_from_json(args.api_key)

qrcodes = []
labels = []

with open(args.input, "r") as file:
    print("Processing file: " + args.input)
    reader = pd.read_csv(file)
    for i in reader.itertuples():
        if i.Index == 0:
            # first row is mapping for appsheet
            continue
        qrcodes.append(generate_qrcode(build_barcode_text(i)))
        labels.append(text_to_image(build_label_text(i)))

image = build_tape_image(qrcodes, labels)
image.save(args.output)
