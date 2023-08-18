#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import typing as t
from http import HTTPStatus
from http.client import responses


class HTTPException(Exception):
    def __init__(self, status: t.Union[int, HTTPStatus], message: t.Optional[str] = None):
        self._status = status
        self._message = message

    @property
    def status(self) -> int:
        return self._status.value if isinstance(self._status, HTTPStatus) else self._status

    @property
    def message(self) -> str:
        return self._message or responses[self.status]

    def __repr__(self):
        return f"{type(self).__name__}({self.status}, {self.message})"
