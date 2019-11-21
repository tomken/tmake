#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
tmake exception
"""

import core


class TmakeException(Exception):
    """exception class for command"""

    def __init__(self, message):
        core.e(' TmakeException --> {0}'.format(message))


class SkipException(Exception):
    """exception class for command"""

    def __init__(self, message):
        core.i('skip info: {0}'.format(message))
        core.e(' SkipException --> {0}'.format(message))


class NotExisTmakeException(Exception):
    """exception class for command"""

    def __init__(self, message):
        core.e(' TmakeException --> {0}'.format(message))
