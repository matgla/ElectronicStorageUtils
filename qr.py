#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# qr.py
#
# Copyright (c) 2024 Mateusz Stadnik <matgla@live.com>
#
# Distributed under the terms of the MIT License.
#

import qrcode


def generate_qrcode(text, qrcode_pixel):
    tmp = qrcode.QRCode(version=1, box_size=qrcode_pixel, border=2, error_correction=qrcode.constants.ERROR_CORRECT_L) 
    tmp.add_data(text)
    tmp.make(fit=True)
    return tmp.make_image(fill_color="black", back_color="white")
