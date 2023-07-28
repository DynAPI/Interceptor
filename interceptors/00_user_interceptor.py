#!/usr/bin/python3
import register
from classes import Request


@register.before_request
def check_api_key(request: Request):
    user = request.headers.get("x-user")
    if user is None:
        request.headers.add_header("x-user", request.authorization.username)
    else:
        request.headers.replace_header("x-user", request.authorization.username)
    # check = ...
    # if not check:
    #     raise HTTPException(HTTPException.FORBIDDEN, "missing apo-key")
    #     raise HTTPException(HTTPException.FORBIDDEN)