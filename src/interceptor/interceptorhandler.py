#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import logging
import http.server
import http.client
import traceback

from config import config
from classes import Request, Response
import register
from exceptions import HTTPException


THOST, TPORT = config.get("target", "host"), config.getint("target", "port")
TIMEOUT = config.getfloat("target", "timeout")


class InterceptorHandler(http.server.BaseHTTPRequestHandler):
    request: Request = None
    response: Response = None

    def __getattr__(self, item: str):
        if item.startswith("do_"):
            return self._handle_wrapper
        raise AttributeError(item)

    def _handle_wrapper(self):
        try:
            self._handle_request()
        except HTTPException as exc:
            self._handle_http_exception(exc)
        except Exception as exc:
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            self._handle_http_exception(
                HTTPException(
                    status=500,
                    message=f"{exc}"
                )
            )
        finally:
            for handler in register.TEARDOWN:
                try:
                    handler(self.request, self.response)
                except Exception as exc:
                    print(f"teardown handler '{handler.__name__}' failed")
                    traceback.print_exception(type(exc), exc, exc.__traceback__)

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

        # client_address is localhost if behind neginx or apache2
        self.request = request = Request(client=self.client_address[0], method=method, path=path, headers=headers, body=body)

        logging.info("running interceptors (before)")
        for interceptor in register.BEFORE:
            early_response = interceptor(request)
            if early_response is not None:
                logging.info(f"Early Response from {interceptor.__name__}")
                self._handle_response(early_response)
                return

        logging.debug("Building Connection...")
        connection = http.client.HTTPConnection(THOST, TPORT, timeout=TIMEOUT)
        logging.debug("Making Request")
        connection.request(
            method=method,
            url=path,
            body=body,
            headers={k: v for k, v in headers.raw_items()}
        )
        logging.debug("Waiting for response...")
        response = Response.from_http_response(connection.getresponse())

        logging.info("running interceptors (after)")
        for interceptor in register.AFTER:
            early_response = interceptor(request, response)
            if early_response is not None:
                logging.info(f"Early Response from {interceptor.__name__}")
                self._handle_response(early_response)
                return

        self._handle_response(response)

    def _handle_response(self, response: Response):
        self.response = response
        logging.debug("sending response...")
        self.send_response_only(response.status)
        logging.debug("sending headers...")
        for name, value in response.headers.raw_items():
            self.send_header(name, value)
        self.end_headers()
        logging.debug("sending body...")
        for chunk in response.body:
            sent = 0
            while sent < len(chunk):
                sent += self.wfile.write(chunk[sent:])
        logging.debug("request completed")

    def _handle_http_exception(self, exc: HTTPException):
        self._handle_response(
            Response.from_http_exception(exc)
        )
