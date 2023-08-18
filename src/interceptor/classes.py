#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import os
import email
import base64
import typing as t
from collections import namedtuple
from http import HTTPStatus
import http.client
from extra_exceptions import HTTPException
from wsstatus import WSOPCode


Authorization = namedtuple("Authorization", ["username", "password"])

# Security Measurement cause everything is loading into the RAM at once
if "WEBSOCKET_MESSAGE_MAX_SIZE" in os.environ:
    WS_MESSAGE_MAX_SIZE = int(os.getenv("WEBSOCKET_MESSAGE_MAX_SIZE"))
else:
    # 1024 * 1024 * 100 ~= 100Mb
    WS_MESSAGE_MAX_SIZE = 104_857_600


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


class WebsocketMessage:
    opcode: int
    length: int
    masks: t.Optional[t.Tuple[int, int, int, int]]
    body: t.Union[str, bytes]

    def __init__(
            self,
            opcode: int,
            length: int,
            masks: t.Optional[t.Tuple[int, int, int, int]],
            body: t.Union[str, bytes],
    ):
        self.opcode = opcode
        self.length = length
        self.masks = masks
        self.body = body

    def __repr__(self):
        return (f"{bytes((self.opcode,)).hex()} - {self.length}\n"
                f"{self.body}")

    @property
    def masked(self) -> bool:
        return self.masks is not None

    @property
    def is_continue(self) -> bool:
        return self.opcode == WSOPCode.CONTINUE

    @property
    def is_text(self) -> bool:
        return self.opcode == WSOPCode.TEXT

    @property
    def is_binary(self) -> bool:
        return self.opcode == WSOPCode.BINARY

    @property
    def is_close(self) -> bool:
        return self.opcode == WSOPCode.CLOSE

    @property
    def is_ping(self) -> bool:
        return self.opcode == WSOPCode.PING

    @property
    def is_pong(self) -> bool:
        return self.opcode == WSOPCode.PONG

    @classmethod
    def from_stream(cls, stream: t.BinaryIO):
        r"""
        0     1      2      3      4 5 6 7   8 	    9 A B C D E F
        FIN   RSV1   RSV2   RSV3   Opcode    Mask   Payload length
        Extended payload length (optional 2bytes or 8bytes)
        Masking key (optional 4bytes)
        Payload data
        """
        import struct
        h1 = ord(stream.read(1))
        opcode = h1 & 0b00001111
        h2 = ord(stream.read(1))
        masked = h2 & 0b10000000
        length = h2 & 0b01111111
        if length == 126:
            length = struct.unpack(">H", stream.read(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", stream.read(8))[0]
        if WS_MESSAGE_MAX_SIZE is not None and length > WS_MESSAGE_MAX_SIZE:
            raise RuntimeError("Websocket message is over the limit")
        masks = [mask for mask in stream.read(4)] if masked else None
        body = stream.read(length)
        if masks:  # unmask the message
            body = bytes((byte ^ masks[i % 4]) for i, byte in enumerate(body))
        if opcode == WSOPCode.TEXT:
            body = body.decode(encoding='utf-8')
        return cls(
            opcode=opcode,
            length=length,
            masks=masks,
            body=body,
        )
