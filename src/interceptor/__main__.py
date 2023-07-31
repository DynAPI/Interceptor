#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import logging
import http.server
import socketserver
from interceptorhandler import InterceptorHandler
from config import config


# this is exactly the same that should be in http.server but isn't (in this version yet?)
# so I copied it and it works.
class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.StreamHandler()],
    )


def load_interceptors():
    import os
    import importlib
    path = os.path.abspath("interceptors")
    if not os.path.isdir(path):
        return
    for fn in sorted(os.listdir(path)):
        mn, ext = os.path.splitext(fn)
        if ext != ".py":
            continue
        logging.info(f"Loading interceptor {mn!r}")
        importlib.import_module(f"interceptors.{mn}")


def main():
    HOST, PORT = config.get("interceptor", "host"), config.getint("interceptor", "port")
    THOST, TPORT = config.get("target", "host"), config.getint("target", "port")

    # server = http.server.HTTPServer(server_address=('localhost', port), RequestHandlerClass=InterceptorHandler)
    server = ThreadingHTTPServer(server_address=(HOST, PORT), RequestHandlerClass=InterceptorHandler)
    logging.info(f"THE INTERCEPTOR runs on {HOST}:{PORT} and protects {THOST}:{TPORT}")
    try:
        server.serve_forever(poll_interval=None)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    logging.info("Server stopped")


if __name__ == '__main__':
    import logo_printer  # noqa
    configure_logging()
    load_interceptors()
    exit(main() or 0)
