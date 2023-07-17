#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import email


class Request:
    method: str
    path: str
    headers: email.message.Message
    body: bytes

    def __init__(self, method: str, path: str, headers: email.message.Message, body: bytes):
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body
