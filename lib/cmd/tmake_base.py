#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
tamke command base file
"""
import lib


class Command(object):
    """command base class"""
    def __init__(self):
        self.arguments = None

    def set_argument(self, arguments):
        """replace argments"""
        self.arguments = arguments

    def help(self):
        """get command help"""
        pass

    def param_check(self):
        """check params"""
        pass

    def run(self):
        """run command"""
        raise lib.TmakeException("The method of run must be overwrite!!!")
