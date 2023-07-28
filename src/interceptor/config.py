# -*- coding=utf-8 -*-
r"""

"""
from __main__ import __file__ as main_file
import os
import configparser
from pathlib import Path


config = configparser.ConfigParser(
    allow_no_value=False,
    delimiters=("=", ":"),
    comment_prefixes=("#", ";"),
    inline_comment_prefixes="#",
    strict=True,
    empty_lines_in_values=False,
    interpolation=configparser.ExtendedInterpolation(),
)
config.optionxform = lambda option: option.lower().replace('-', '_')  # 'Hello-World' => 'hello_world'

for location in [
    Path(os.getenv("INTERCEPTOR_CONF") or ""),
    Path(main_file).parent / "interceptor.conf",
    Path().cwd() / "interceptor.conf",
    Path.home() / ".dyninterceptor.conf",
    Path("/") / "etc" / "dynapi" / "interceptor.conf",
]:
    location = location.absolute()
    if location.is_file():
        if config.read([location]):
            print(f"Conf-File: {location}")
            break
else:
    raise FileNotFoundError("interceptor.conf")
