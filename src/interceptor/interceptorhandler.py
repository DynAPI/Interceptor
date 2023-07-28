#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import http.server
import http.client
import logging

from config import config
from classes import Request, Response
import register


class InterceptorHandler(http.server.BaseHTTPRequestHandler):
    def __getattr__(self, item: str):
        if item.startswith("do_"):
            return self._handle_request
        raise AttributeError(item)

    def _handle_request(self):
        logging.info(f"Handle Request from {self.client_address[0]}")
        method = self.command
        logging.debug("method:", method)
        path = self.path
        logging.debug("path:", path)
        headers = self.headers
        forwarded_for = headers.get("X-Forwarded-For")
        if forwarded_for is None:
            headers.add_header("X-Forwarded-For", self.client_address[0])
        else:
            headers.replace_header("X-Forwarded-For", f"{forwarded_for}, {self.client_address[0]}")
        logging.debug("headers:", headers)
        content_length = int(headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else None
        logging.debug("body:", body and body[:20])

        req = Request(method=method, path=path, headers=headers, body=body)

        logging.info("running interceptors (before)")
        for interceptor in register.BEFORE:
            interceptor(req)

        logging.debug("Building Connection...")
        connection = http.client.HTTPConnection(config.TARGET_HOST, config.TARGET_PORT, timeout=config.TIMEOUT)
        logging.debug("Making Request")
        connection.request(
            method=method,
            url=path,
            body=body,
            headers={k: v for k, v in headers.raw_items()}
        )
        logging.debug("Waiting for response...")
        response = connection.getresponse()

        logging.info("running interceptors (after)")
        for interceptor in register.AFTER:
            interceptor(req, response)

        logging.debug("sending response...")
        self.send_response_only(response.status)
        logging.debug("sending headers...")
        for key, value in response.getheaders():
            self.send_header(key, value)
        self.end_headers()
        logging.debug("sending body...")
        got = 0
        while got < response.length:
            chunk = response.read(1000)
            got += len(chunk)
            self.wfile.write(chunk)
        logging.debug("request completed")
