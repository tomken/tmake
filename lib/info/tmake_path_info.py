#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
路径相关的类
"""

import os

import lib


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

        # local_export 根路径 project_floder/local_export
        self.local_export_base_path = os.path.join(self.project_folder, "local_export")

        # publish 根路径 project_floder/publish
        self.publish_base_path = os.path.join(self.project_folder, "publish")

        # package 跟路径 project_floder/packages
        self.package_base_path = os.path.join(self.project_folder, "packages")

        # build 路径 project_floder/build/android/armeabi-v7a/debug
        self.build_path = self.__concat_with_sub_path(self.build_base_path)

        # project 路径 project_floder/project/android/armeabi-v7a/debug
        self.project_path = self.__concat_with_sub_path(self.project_base_path)

        # local_export 路径 project_floder/local_export/android/armeabi-v7a/debug
        self.local_export_path = self.__concat_with_sub_path(self.local_export_base_path)

        # publish 路径 project_floder/publish/android/armeabi-v7a/debug
        self.publish_path = self.__concat_with_sub_path(self.publish_base_path)

        # 生成的文件路径
        self.build_installed_path = os.path.join(self.build_path, lib.BUILD_INSTALL_PREFIX, lib.BUILD_OUTPUT_NAME)
        self.build_symbol_path = os.path.join(self.build_path, lib.BUILD_OUTPUT_NAME)

        # 编译成功信息保存的文件
        self.success_build_status_file_path = os.path.join(self.build_path, 'build_success_status')

        # 生成的project bin地址
        self.project_bin_path = ""
        if lib.data.build_config == lib.CONFIG_DEBUG:
            self.project_bin_path = os.path.join(self.project_path, 'bin/Debug')
        elif lib.data.build_config == lib.CONFIG_RELWITHDEBINFO:
            self.project_bin_path = os.path.join(self.project_path, 'bin/RelWithDebInfo')
        else:
            self.project_bin_path = os.path.join(self.project_path, 'bin/Release')

    @staticmethod
    def get_default_path_info():
        from lib.info import tmake_builtin
        return AbtorPathInfo(tmake_builtin.ABTOR_CPU_ARCH, lib.data.current_project.folder)

    def __concat_with_sub_path(self, base_path):
        """
        连接子path
        :param base_path:
        :return:
        """
        path = os.path.join(base_path,
                            lib.data.target,
                            self.arch,
                            lib.data.build_config)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def get_build_path(self):
        return self.build_path

    def get_local_export_include_path(self, project_name):
        """
        获取export的include路径
        :param project_name:
        :return:
        """
        return os.path.join(self.local_export_path, project_name, 'include')

    def get_local_export_lib_path(self, project_name):
        """
        获取export的lib路径
        :param project_name:
        :return:
        """
        return os.path.join(self.local_export_path, project_name, 'libs')

    def get_local_export_libsys_path(self, project_name):
        """
        获取export的libs_sym路径
        :param project_name:
        :return:
        """
        return os.path.join(self.local_export_path, project_name, 'libs_sym')

    def get_auto_publish_path(self, project_name):
        """
        获取publish路径
        :param project_name:
        :return:
        """
        return os.path.join(self.publish_path, project_name, 'publish')

    def get_auto_abtor_xml_path(self, project_name):
        """
        获取abtor xml文件夹
        :param project_name:
        :return:
        """
        return os.path.join(self.publish_path, project_name, 'abtor_xml')

    def get_arch_output_path(self, arch):
        """
        获取某指令集的build目录
        :param arch:
        :return:
        """
        path = os.path.join(self.build_base_path,
                            lib.data.target,
                            arch,
                            lib.data.build_config,
                            lib.BUILD_OUTPUT_NAME
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
                            lib.data.target,
                            arch,
                            lib.data.build_config,
                            lib.BUILD_INSTALL_PREFIX,
                            lib.BUILD_OUTPUT_NAME)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def get_package_zip_path(self, name):
        """
        获取要保存的zip文件全路径
        :param name:
        :return:
        """
        if not os.path.exists(self.package_base_path):
            os.makedirs(self.package_base_path)
        file_name = '{}_{}_{}_{}.zip'.format(name, lib.data.target, self.arch, lib.data.build_config)
        full_path = os.path.join(self.package_base_path, file_name)
        return full_path
