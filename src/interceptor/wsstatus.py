#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
from enum import IntEnum


__all__ = ['WSStatus']


class WSStatus(IntEnum):
    """WS status codes and reason phrases
    """
    def __new__(cls, value, phrase, description=''):
        obj = int.__new__(cls, value)
        obj._value_ = value

        obj.phrase = phrase
        obj.description = description
        return obj

    CLOSE_NORMAL = (1000, 'Normal Closure',
                    ' The connection successfully completed the purpose for which it was created')
    CLOSE_GOING_AWAY = (1001, 'Switching Protocols',
                        'The endpoint is going away, either because of a server failure or because the browser is '
                        'navigating away from the page that opened the connection')
    CLOSE_PROTOCOL_ERROR = (1002, 'Protocol Error',
                            'The endpoint is terminating the connection due to a protocol error')
    CLOSE_UNSUPPORTED = (1003, 'Unsupported Data',
                         ' The connection is being terminated because the endpoint received data of a type it cannot '
                         'accept. (For example, a text-only endpoint received binary data.)')
    # 1004 Reserved
    CLOSED_NO_STATUS = (1005, 'No Status Received',
                        'Indicates that no status code was provided even though one was expected')
    CLOSE_ABNORMAL = (1006, 'Abnormal Closure',
                      ' Indicates that a connection was closed abnormally (that is, with no close frame being sent) '
                      'when a status code is expected')
    UNSUPPORTED_PAYLOAD = (1007, 'Invalid frame payload data',
                           'The endpoint is terminating the connection because a message was received that contained '
                           'inconsistent data (e.g., non-UTF-8 data within a text message)')
    POLICY_VIOLATION = (1008, 'Policy Violation',
                        'The endpoint is terminating the connection because it received a message that violates its '
                        'policy. This is a generic status code, used when codes 1003 and 1009 are not suitable')
    CLOSE_TOO_LARGE = (1009, 'Message Too Big',
                       'The endpoint is terminating the connection because a data frame was received that is too large')
    MANDATORY_EXTENSION = (1010, 'Mandatory Extension',
                           'The client is terminating the connection because it expected the server to negotiate one '
                           'or more extension, but the server didn\'t')
    SERVER_ERROR = (1011, 'Internal Server Error',
                    'The server is terminating the connection because it encountered an unexpected condition that '
                    'prevented it from fulfilling the request')
    SERVICE_RESTART = (1012, 'Service Restart',
                       'The server is terminating the connection because it is restarting')
    TRY_AGAIN_LATER = (1013, 'Try Again Later',
                       'The server is terminating the connection due to a temporary condition, e.g. it is overloaded '
                       'and is casting off some of its clients')
    BAD_GATEWAY = (1014, 'Bad Gateway',
                   'The server was acting as a gateway or proxy and received an invalid response from the upstream '
                   'server. This is similar to 502 HTTP Status Code')
    TLS_HANDSHAKE_FAILED = (1015, 'TLS Handshake Failed',
                            'Indicates that the connection was closed due to a failure to perform a TLS handshake '
                            '(e.g., the server certificate can\'t be verified)')


class WSOPCode:
    CONTINUE = 0x0
    TEXT = 0x1
    BINARY = 0x2
    CLOSE = 0x8
    PING = 0x9
    PONG = 0xA
