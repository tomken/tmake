#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
路径相关的类
"""

import os

import core


class PathInfo(object):
    """
    路径相关的类
    """

    def __init__(self, arch, project_folder):
        self.project_folder = project_folder

        self.arch = arch

        # build 根路径 project_floder/build
        self.build_base_path = os.path.join(self.project_folder, "build")

        # project 根路径 project_floder/project
        self.project_base_path = os.path.join(self.project_folder, "project")

        # build 路径 project_floder/build/android/armeabi-v7a/debug
        self.build_path = self.__concat_with_sub_path(self.build_base_path)

        # project 路径 project_floder/project/android/armeabi-v7a/debug
        self.project_path = self.__concat_with_sub_path(self.project_base_path)

        # 生成的文件路径
        self.build_installed_path = os.path.join(self.build_path, core.BUILD_INSTALL_PREFIX, core.BUILD_OUTPUT_NAME)
        self.build_symbol_path = os.path.join(self.build_path, core.BUILD_OUTPUT_NAME)

        # 编译成功信息保存的文件
        self.success_build_status_file_path = os.path.join(self.build_path, 'build_success_status')

        # 生成的project bin地址
        self.project_bin_path = ""
        if core.data.build_config == core.CONFIG_DEBUG:
            self.project_bin_path = os.path.join(self.project_path, 'bin/Debug')
        elif core.data.build_config == core.CONFIG_RELWITHDEBINFO:
            self.project_bin_path = os.path.join(self.project_path, 'bin/RelWithDebInfo')
        else:
            self.project_bin_path = os.path.join(self.project_path, 'bin/Release')

    @staticmethod
    def get_default_path_info():
        from core.info import tmake_builtin
        return PathInfo(tmake_builtin.TMAKE_CPU_ARCH, core.data.current_project.folder)

    def __concat_with_sub_path(self, base_path):
        """
        连接子path
        :param base_path:
        :return:
        """
        path = os.path.join(base_path,
                            core.data.target,
                            self.arch,
                            core.data.build_config)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def get_build_path(self):
        return self.build_path


    def get_arch_output_path(self, arch):
        """
        获取某指令集的build目录
        :param arch:
        :return:
        """
        path = os.path.join(self.build_base_path,
                            core.data.target,
                            arch,
                            core.data.build_config,
                            core.BUILD_OUTPUT_NAME
                            )
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def get_arch_export_path(self, arch):
        """
        获取某指令集的export目录
        :param arch:
        :return:
        """
        path = os.path.join(self.build_base_path,
                            core.data.target,
                            arch,
                            core.data.build_config,
                            core.BUILD_INSTALL_PREFIX,
                            core.BUILD_OUTPUT_NAME)
        if not os.path.exists(path):
            os.makedirs(path)
        return path
