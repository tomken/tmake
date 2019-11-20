#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
tmake exception
"""

import lib


class TmakeException(Exception):
    """exception class for command"""

    def __init__(self, message):
        lib.e(' TmakeException --> {0}'.format(message))


class SkipException(Exception):
    """exception class for command"""

    def __init__(self, message):
        lib.i('skip info: {0}'.format(message))
        lib.e(' TmakeException --> {0}'.format(message))


class NotExisTmakeException(Exception):
    """exception class for command"""

    def __init__(self, message):
        lib.e(' TmakeException --> {0}'.format(message))
