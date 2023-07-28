#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import email
import base64
import typing as t
from http import HTTPStatus
import http.client
from exceptions import HTTPException
from collections import namedtuple


Authorization = namedtuple("Authorization", ["username", "password"])


class Request:
    client: str
    method: str
    path: str
    headers: email.message.Message
    body: bytes

    def __init__(self, client: str, method: str, path: str, headers: email.message.Message, body: t.Optional[bytes]):
        self.client = client
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body

    def __str__(self):
        return (f"HTTP-Request from {self.client}"
                f"{self.method} {self.path}"
                f"{self.headers}"
                f"{self.body and self.body[:20]}...")

    @property
    def authorization(self) -> t.Optional[Authorization]:
        header: t.Optional[str] = self.headers.get("Authorization")
        if header is None:
            return None
        auth_scheme, sep, auth_params = header.partition(" ")
        if sep is None:
            raise ValueError("Bad Authorization Header")
        if auth_scheme != "Basic":
            raise NotImplementedError(f"authorization parsing for {auth_scheme} is not supported")
        parts = [p.strip() for p in auth_params.split(",")]
        b64 = parts[0]
        username, sep, password = base64.b64decode(b64).partition(":")
        if sep is None:
            raise ValueError("Bad credentials")
        return Authorization(username=username, password=password)


class Response:
    def __init__(
            self,
            body: t.Union[str, bytes, t.Callable[[], t.Union[str, bytes]]],
            status: t.Union[int, HTTPStatus] = 200,
            headers: t.Union[dict, http.client.HTTPMessage] = None
    ):
        self._body = body
        self._status = status
        self._headers = headers

    @classmethod
    def from_http_response(cls, response: http.client.HTTPResponse):
        def fetching() -> bytes:
            got = 0
            while got < response.length:
                chunk = response.read(1000)
                got += len(chunk)
                yield chunk

        return cls(
            body=fetching,
            status=response.status,
            headers=response.headers,
        )

    @classmethod
    def from_http_exception(cls, exc: HTTPException):
        import json
        return cls(
            body=json.dumps(dict(
                status=exc.status,
                message=exc.message,
            )).encode(),
            status=exc.status,
            headers={
                "Content-Type": "application/json",
                "X-Interceptor": "true",
            }
        )

    @property
    def body(self) -> t.Iterable[bytes]:
        if callable(self._body):
            yield from self._body()
        else:
            yield self._body

    @property
    def status(self) -> int:
        return self._status.value if isinstance(self._status, HTTPStatus) else self._status

    @status.setter
    def status(self, status: t.Union[int, HTTPStatus]):
        self._status = status

    @property
    def headers(self) -> http.client.HTTPMessage:
        if isinstance(self._headers, http.client.HTTPMessage):
            return self._headers
        else:
            headers = http.client.HTTPMessage()
            for name, value in self._headers.items():
                headers.set_raw(name, value)
            self._headers = headers
        return self._headers
