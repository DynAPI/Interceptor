#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""


BEFORE = []
AFTER = []
TEARDOWN = []


def before_request(fn):
    BEFORE.append(fn)


def after_response(fn):
    AFTER.append(fn)


def teardown_request(fn):
    TEARDOWN.append(fn)
