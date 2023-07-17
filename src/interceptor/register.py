#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""


BEFORE = []
AFTER = []


def prepend_before_request(fn):
    BEFORE.insert(0, fn)


def append_before_request(fn):
    BEFORE.append(fn)


def prepend_after_response(fn):
    AFTER.insert(0, fn)


def append_after_response(fn):
    AFTER.append(fn)
