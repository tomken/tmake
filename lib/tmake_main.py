#!/usr/bin/python2
# -*- coding: UTF-8 -*-

# 0.2.5.4.26

import traceback
import platform
import sys

import lib

log_attributes = lib.get_default_buffer_info()


class Main(object):

    def __init__(self):
        pass

    def run(self):
        try:
            arguments = lib.data.arguments
            if not lib.data.arguments.tmake_cmd():
                import cmd.tmake_help
                cmd.tmake_help.main().run()
                return
            self.check_python_tools()
            if lib.data.arguments.tmake_cmd() != "config":
                self.check_cmake_tools()
            lib.exec_tmake_command(arguments)
            # lib.s(lib.data.arguments.tmake_cmd() + ' success!')
        except Exception as exception:
            traceback.print_exc()
            lib.reset_color(log_attributes)
            if not isinstance(exception, lib.TmakeException):
                lib.e(traceback.format_exc())
                raise lib.TmakeException('use `tmake help` to get more information')
            sys.exit(-1)

    def check_python_tools(self):
        """check python tools"""
        version = platform.python_version()
        if not version.startswith("2.7"):
            raise lib.TmakeException("please make sure python version is 2.7.x !!!")
    
    def check_cmake_tools(self):
        """check cmake tools"""
        if not lib.check_cmake():
            raise lib.TmakeException("please install cmake !!!")