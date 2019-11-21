#!/usr/bin/python2
# -*- coding: UTF-8 -*-

# 0.2.5.4.26

import traceback
import platform
import sys

import core

log_attributes = core.get_default_buffer_info()


class Main(object):

    def __init__(self):
        core.data.action_mgr = core.ActionManager()

    def run(self):
        try:
            arguments = core.data.arguments
            if not core.data.arguments.tmake_cmd():
                import cmd.tmake_help
                cmd.tmake_help.main().run()
                return
            self.check_python_tools()
            if core.data.arguments.tmake_cmd() != "config":
                self.check_cmake_tools()
            core.exec_tmake_command(arguments)
            # core.s(core.data.arguments.tmake_cmd() + ' success!')
        except Exception as exception:
            traceback.print_exc()
            core.reset_color(log_attributes)
            if not isinstance(exception, core.TmakeException):
                core.e(traceback.format_exc())
                raise core.TmakeException('use `tmake help` to get more information')
            sys.exit(-1)

    def check_python_tools(self):
        """check python tools"""
        version = platform.python_version()
        if not version.startswith("2.7"):
            raise core.TmakeException("please make sure python version is 2.7.x !!!")
    
    def check_cmake_tools(self):
        """check cmake tools"""
        if not core.check_cmake():
            raise core.TmakeException("please install cmake !!!")