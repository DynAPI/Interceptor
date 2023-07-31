#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import re
import functools
import typing as t
from config import config


def is_globby(pat: str) -> bool:
    return "*" in pat or "?" in pat


def translate_globby(pat: str) -> str:
    return re.escape(pat).replace(r"\*", ".*").replace(r"\?", ".")


def get_worth(pat: str):
    if pat == "?":
        return 0
    elif pat == "*":
        return 1
    elif is_globby(pat):
        return 2
    else:
        return 3


class ParsedSection:
    def __init__(self, section: str):
        self.raw = section
        parts = section.split(":")
        self.section = parts[0]
        if self.section != 'permissions' or len(parts) > 3:
            raise KeyError(f"invalid section: {self.section!r}")
        self.path = (parts[1] if len(parts) > 1 else None) or "*"
        if self.path != "*" and not self.path.startswith("/"):
            raise ValueError("Path is not absolute")
        self.path_re = re.compile(translate_globby(self.path), re.IGNORECASE) if self.path else None
        self.roles = [role.lower() for role in parts[2].split(",")] if len(parts) > 2 else None

        self.worth = get_worth(self.path) + ((10 - len(self.roles)) if self.roles else 0)

    def __repr__(self):
        return f"<{type(self).__name__} {self.path}:{','.join(self.roles or [])}>"

    # used for sorting
    def __lt__(self, other: 'ParsedSection'):
        return self.worth < other.worth

    def match_path(self, path) -> t.Optional[bool]:
        if not self.path:
            return None
        return self.path_re.fullmatch(path) is not None

    def match_roles(self, roles: tuple):
        if not self.roles:
            return None
        return any(role.lower() in self.roles for role in roles)


@functools.lru_cache()
def ordered_sections():
    parsed = []
    for section in config.sections():
        try:
            parsed.append(ParsedSection(section))
        except KeyError:
            pass
    return sorted(parsed, reverse=True)


@functools.lru_cache()
def method_check(*, method: str, path: str, roles: tuple) -> bool:
    for section in ordered_sections():
        if section.match_path(path) is not False and section.match_roles(roles) is not False:
            allowed = config.getboolean(section.raw, method, fallback=None)
            if allowed is True:
                return True
    return False
