# -*- coding: utf-8 -*-
"""
    emmett.wrappers
    ---------------

    Provides request and response wrappers.

    :copyright: (c) 2014-2019 by Giovanni Barillari
    :license: BSD, see LICENSE for more details.
"""

import re

from http.cookies import SimpleCookie
from urllib.parse import parse_qs

from ..datastructures import Accept, sdict
from ..language.helpers import LanguageAccept
from ..utils import cachedprop
from .helpers import Headers

_regex_accept = re.compile(r'''
    ([^\s;,]+(?:[ \t]*;[ \t]*(?:[^\s;,q][^\s;,]*|q[^\s;,=][^\s;,]*))*)
    (?:[ \t]*;[ \t]*q=(\d*(?:\.\d+)?)[^,]*)?''', re.VERBOSE)


class Wrapper:
    def __getitem__(self, key):
        return getattr(self, key, None)

    def __setitem__(self, key, value):
        setattr(self, key, value)


class ScopeWrapper(Wrapper):
    __slots__ = (
        '_scope', 'scheme', 'path', 'headers', 'host'
    )

    def __init__(self, scope):
        self._scope = scope
        self.scheme = scope['scheme']
        self.path = scope['emt.path']
        self.headers = Headers(scope)
        self.host = self.headers.get('host')

    def __parse_accept_header(self, value, cls=Accept):
        if not value:
            return cls(None)
        result = []
        for match in _regex_accept.finditer(value):
            quality = match.group(2)
            if not quality:
                quality = 1
            else:
                quality = max(min(float(quality), 1), 0)
            result.append((match.group(1), quality))
        return cls(result)

    @cachedprop
    def accept_language(self):
        return self.__parse_accept_header(
            self.headers.get('accept-language'), LanguageAccept)

    @cachedprop
    def cookies(self):
        cookies = SimpleCookie()
        for cookie in self.headers.get('cookie', '').split(';'):
            cookies.load(cookie)
        return cookies

    @cachedprop
    def query_params(self):
        rv = sdict()
        for key, values in parse_qs(
            self._scope['query_string'].decode('ascii'), keep_blank_values=True
        ).items():
            if len(values) == 1:
                rv[key] = values[0]
                continue
            rv[key] = values
        return rv
