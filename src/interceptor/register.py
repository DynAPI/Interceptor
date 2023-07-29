#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import logging


BEFORE = []
AFTER = []
TEARDOWN = []


def before_request(fn):
    logging.info(f"register.before_request({fn.__name__})")
    BEFORE.append(fn)


def after_response(fn):
    logging.info(f"register.after_response({fn.__name__})")
    AFTER.append(fn)


def teardown_request(fn):
    logging.info(f"register.teardown_request({fn.__name__})")
    TEARDOWN.append(fn)
