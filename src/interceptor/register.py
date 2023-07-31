#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import logging


BEFORE = []
AFTER = []
TEARDOWN = []


def before_request(fn):
    logging.info(f"register.before_request({fn.__module__}.{fn.__qualname__})")
    BEFORE.append(fn)


def after_response(fn):
    logging.info(f"register.after_response({fn.__module__}.{fn.__qualname__})")
    AFTER.append(fn)


def teardown_request(fn):
    logging.info(f"register.teardown_request({fn.__module__}.{fn.__qualname__})")
    TEARDOWN.append(fn)
