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


def generate_qrcode(text):
    qr = qrcode.QRCode(version=1, box_size=2)

    qr.add_data(text)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")
