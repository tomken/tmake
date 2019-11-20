#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys

import lib

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
        self.__init_current_info()

    def __init_current_info(self):
        # default target to host
        self.target = self.arguments.get_opt('-t', '--target')
        if self.target is None:
            self.target = self.platform.host

        # process project build config
        self.build_config = self.arguments.get_opt('-c', '--config')
        if self.build_config is None:
            self.build_config = lib.CONFIG_DEBUG

        # default target alias none
        self.target_alias = self.arguments.get_opt('-l', '--alias')

        # 对全局的-v -V的支持
        if self.arguments.has_flag("v"):
            log.TMAKE_VERBOSE = True
        if self.arguments.has_flag("V"):
            os.putenv('VERBOSE', '1')

        #设置log输出类型
        log_d = self.arguments.has_flag('logd')
        log_i = self.arguments.has_flag('logi')
        log_e = self.arguments.has_flag('loge')
        log_s = self.arguments.has_flag('logs')

        if log_d:
            log.TMAKE_LOG_DEBUG = True
            log.TMAKE_LOG_INFO = False
            log.TMAKE_LOG_ERROR = False
            log.TMAKE_LOG_SUCCESS = False


        if log_i:
            log.TMAKE_LOG_INFO = True
            if log_d == False:
                log.TMAKE_LOG_DEBUG = False
            log.TMAKE_LOG_ERROR = False
            log.TMAKE_LOG_SUCCESS = False

        if log_e:
            log.TMAKE_LOG_ERROR = True
            if log_d == False:
                log.TMAKE_LOG_DEBUG = False
            if log_i == False:
                log.TMAKE_LOG_INFO = False
            log.TMAKE_LOG_SUCCESS = False

        if log_s:
            log.TMAKE_LOG_SUCCESS = True
            if log_d == False:
                log.TMAKE_LOG_DEBUG = False
            if log_i == False:
                log.TMAKE_LOG_INFO = False
            if log_e == False:
                log.TMAKE_LOG_ERROR = False

GlobalData = Data()