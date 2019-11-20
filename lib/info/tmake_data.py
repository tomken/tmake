#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys

from .tmake_arguments import ArgumentsInfo
from .tmake_platform import PlatformInfo
from .tmake_environment import EnvironmentInfo

class Data(object):

    def __init__(self):
        self.action_mgr = None
        self.arguments = ArgumentsInfo(sys.argv)
        self.platform = PlatformInfo()
        self.project = None
        self.param = {}
        self.current_project = None
        self.build_config = ""
        self.target = ""
        self.target_alias = None
        self.cmake_path = None
        self.environment = EnvironmentInfo(self.arguments.get_opt("vs"))
        self.arch = ""


GlobalData = Data()