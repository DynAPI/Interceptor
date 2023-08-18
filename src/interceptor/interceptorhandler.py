#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import socket
import logging
import http.server
import http.client

from config import config
from classes import Request, Response
import register
from extra_exceptions import HTTPException


THOST, TPORT = config.get("target", "host"), config.getint("target", "port")
TIMEOUT = config.getfloat("target", "timeout")


class InterceptorHandler(http.server.BaseHTTPRequestHandler):
    x_request: Request = None
    x_response: Response = None
    x_final_response: Response = None
    x_connection: http.client.HTTPConnection = None

    def __getattr__(self, item: str):
        if item.startswith("do_"):
            return self._handle_wrapper
        raise AttributeError(item)

    def _handle_wrapper(self):
        try:
            self._handle_request()
        except ConnectionRefusedError:
            self._handle_http_exception(
                HTTPException(
                    status=http.HTTPStatus.SERVICE_UNAVAILABLE
                )
            )
        except HTTPException as exc:
            self._handle_http_exception(exc)
        except Exception as exc:
            logging.error("_handle_request failed", exc_info=exc)
            self._handle_http_exception(
                HTTPException(
                    status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                    message=f"{exc}"
                )
            )
        finally:
            for handler in register.TEARDOWN:
                try:
                    self._call_handler(handler)
                except Exception as exc:
                    logging.error(f"teardown handler '{handler.__name__}' failed", exc_info=exc)

    def _handle_request(self):
        logging.info(f"Handle Request from {self.client_address[0]}")
        method = self.command
        logging.debug(f"method: {method}")
        path = self.path
        logging.debug(f"path: {path}")
        headers = self.headers
        forwarded_for = headers.get("X-Forwarded-For")
        if forwarded_for is None:
            headers.add_header("X-Forwarded-For", self.client_address[0])
        else:
            headers.replace_header("X-Forwarded-For", f"{forwarded_for}, {self.client_address[0]}")
        logging.debug(f"headers: {headers}")
        content_length = int(headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else None
        logging.debug(f"body: {body and body[:20]}")

        # client_address is localhost if behind nginx or apache2
        self.x_request = Request(client=self.client_address[0], method=method, path=path, headers=headers, body=body)

        logging.info("running interceptors (before)")
        for interceptor in register.BEFORE:
            logging.debug(f"(before) Interceptor: {interceptor.__name__}")
            early_response = self._call_handler(interceptor)
            if early_response is not None:
                logging.info(f"Early Response from {interceptor.__name__}")
                self._handle_response(early_response)
                return

        if headers.get("Upgrade", None) == "websocket":
            logging.info("Upgrading to websocket")
            self._handle_websocket_handshake()
            self._handle_websocket_connection()
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
        self.x_response = response = Response.from_http_response(connection.getresponse())

        logging.info("running interceptors (after)")
        for interceptor in register.AFTER:
            logging.debug(f"(after) Interceptor: {interceptor.__name__}")
            early_response = self._call_handler(interceptor)
            if early_response is not None:
                logging.info(f"Early Response from {interceptor.__name__}")
                self._handle_response(early_response)
                return

        self._handle_response(response)

    def _handle_response(self, response: Response):
        self.x_final_response = response
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

    def _call_handler(self, handler):
        if not hasattr(handler, '__handler_args__'):
            import inspect
            sig = inspect.signature(handler)
            handler.__handler_args__ = list(sig.parameters.keys())
        args = dict(
            self=self,
            request=self.x_request,
            response=self.x_response,
            final_response=self.x_final_response,
            connection=self.x_connection,
        )
        args['kwargs'] = args
        return handler(**{arg: args.get(arg, None) for arg in handler.__handler_args__})

    # Websocket-Implementation

    def _handle_websocket_handshake(self):
        logging.debug("WebSocket Handshake")
        request = self.x_request
        self.x_connection = conn = http.client.HTTPConnection(THOST, TPORT, timeout=TIMEOUT)
        self.x_connection.request(
            method=request.method,
            url=request.path,
            body=request.body,
            headers=request.headers,
        )
        response = conn.getresponse()
        self.send_response_only(response.status)
        for name, value in response.headers.raw_items():
            self.send_header(name, value)
        self.end_headers()

    def _handle_websocket_connection(self):
        import select

        client: socket.socket = self.connection
        server: socket.socket = self.x_connection.sock

        alive = True

        logging.debug("WebSocket Loop")
        while alive:
            read_sockets, write_sockets, error_sockets = select.select(
                [client, server], [], []
            )

            for reader in read_sockets:
                reader: socket.socket
                # print(reader == client, reader == server)
                sender = server if reader is client else client
                data = reader.recv(1024)
                if not data:
                    alive = False
                    break
                logging.debug(f"ws {'<' if reader is client else '>'} {data}")
                sender.sendall(data)

        logging.debug("WebSocket completed")
