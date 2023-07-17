#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
try:
    import ssl
except ImportError:
    ssl = None
import logging
import http.server
import socketserver
from interceptorhandler import InterceptorHandler
import config


# this is exactly the same that should be in http.server but isn't (in this version yet?)
# so I copied it and it works.
class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass


def load_interceptors():
    import os
    import importlib
    for fn in os.listdir("interceptors"):
        mn, ext = os.path.splitext(fn)
        if ext != ".py":
            continue
        logging.info(f"Loading interceptor {mn!r}")
        importlib.import_module(f"interceptors.{mn}")


def main():
    # server = http.server.HTTPServer(server_address=('localhost', port), RequestHandlerClass=InterceptorHandler)
    server = ThreadingHTTPServer(server_address=(config.HOST, config.PORT), RequestHandlerClass=InterceptorHandler)
    if ssl and hasattr(config, 'SSL_CERT'):
        server.socket = ssl.wrap_socket(server.socket, server_side=True, certfile=config.SSL_CERT, ssl_version=ssl.PROTOCOL_TLS)

    logging.info(f"THE INTERCEPTOR runs on {config.HOST}:{config.PORT} and protects {config.TARGET_HOST}:{config.TARGET_PORT}")
    try:
        server.serve_forever(poll_interval=None)
    except KeyboardInterrupt:
        pass

    server.server_close()
    logging.info("Server stopped")


if __name__ == '__main__':
    import logo_printer  # noqa
    load_interceptors()
    exit(main() or 0)
