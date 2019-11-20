#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import os

import lib

from .tmake_arguments import ArgumentsInfo
from .tmake_platform import PlatformInfo
from .tmake_environment import EnvironmentInfo
from .tmake_project import ProjectInfo

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

    def __parse_project_deps(self, project, is_root):
        """
        解析项目依赖，从最底层的项目开始解析
        :param project:
        :return:
        """
        for proj in project.local_deps_projects:
            self.__parse_project_deps(proj, False)
        # abtor.data.deps_mgr.parse(project, is_root)

    def change_project_arch(self, arch):
        from lib.info import tmake_builtin
        tmake_builtin.ABTOR_CPU_ARCH = arch
        self.arch = arch
        if "projsmap" in self.param:
            del self.param["projsmap"]
        # self.deps_mgr.clear()
        # self.deps_mgr.update_arch(arch)

    def parse_project(self):
        """parse tmake.proj"""
        # load WORK_PATH
        script = os.path.join(lib.data.arguments.work_path(), "abtor.proj")
        if os.path.exists(script):
            lib.v("project path=" + script)
            lib.data.project = lib.utils.tmake_project_parser.parse(script)
            self.__parse_project_deps(lib.data.project, True)
            # 依赖关系处理完毕逻辑
            # lib.data.deps_mgr.parse_finish()
            return True
        # 处理只有CMakeLists.txt的场景
        script = os.path.join(lib.data.arguments.work_path(), "CMakeLists.txt")
        if os.path.exists(script):
            lib.data.use_cmakelist = True
            lib.v("project path=" + script)

            lib.data.project = lib.abtor_project_parser.parse(script)
            if lib.data.arguments.abtor_cmd() == "project":
                path_info = AbtorPathInfo(self.arch, lib.data.arguments.work_path())
                base_path = path_info.project_path
            else:
                base_path = lib.data.project.get_build_folder(self.arch)
            export_path = os.path.join(base_path, lib.BUILD_INSTALL_PREFIX)
            exectable_output_path = os.path.join(base_path, lib.BUILD_OUTPUT_NAME)
            library_output_path = os.path.join(base_path, lib.BUILD_OUTPUT_NAME)
            export_path = export_path.replace("\\", "/")
            exectable_output_path = exectable_output_path.replace("\\", "/")
            library_output_path = library_output_path.replace("\\", "/")
            recover_cmakelists(lib.data.arguments.work_path())
            change_cmakelists_output(lib.data.arguments.work_path(), export_path, exectable_output_path, library_output_path)
            return True
        return False

    def new_project(self):
        """new project"""
        project = ProjectInfo()
        return project

GlobalData = Data()