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
        self._auth_cached = None

    def __str__(self):
        return (f"HTTP-Request from {self.client}"
                f"{self.method} {self.path}"
                f"{self.headers}"
                f"{self.body and self.body[:20]}...")

    @property
    def authorization(self) -> t.Optional[Authorization]:
        if self._auth_cached is not None:
            return self._auth_cached
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
        username, sep, password = base64.b64decode(b64).decode().partition(":")
        if sep is None:
            raise ValueError("Bad credentials")
        self._auth_cached = Authorization(username=username, password=password)
        return self._auth_cached


class Response:
    def __init__(
            self,
            body: t.Union[str, bytes, t.Callable[[], t.Iterable[t.Union[str, bytes]]]],
            status: t.Union[int, HTTPStatus] = 200,
            headers: t.Union[dict, http.client.HTTPMessage] = None
    ):
        self._body = body
        self._status = status
        self._headers = headers

    @classmethod
    def from_http_response(cls, response: http.client.HTTPResponse):
        def fetching() -> t.Iterable[bytes]:
            while response.length > 0:
                yield response.read(1000)

        return cls(
            body=fetching,
            status=response.status,
            headers=response.headers,
        )

    @classmethod
    def from_http_exception(cls, exc: HTTPException):
        import json
        body = json.dumps(dict(
            status=exc.status,
            message=exc.message,
        )).encode()
        return cls(
            body=body,
            status=exc.status,
            headers={
                "Content-Type": "application/json",
                "Content-Length": len(body),
                "Server": "Interceptor",
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
