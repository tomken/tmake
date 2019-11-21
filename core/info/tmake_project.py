#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
Tmake 项目信息类
支持本地依赖树
"""

import os
import json
import traceback

from collections import OrderedDict
from core.utils import tmake_utils

import core


class ProjectLibrary(object):
    """tmake project library"""

    def __init__(self):
        self.is_local = True
        self.name = ""
        self.version = ""
        self.path = ""
        self.xml_path = ""

        self.include_path = ""
        self.lib_path = ""
        self.package_path = ""

        self.deps_library = []

    def __str__(self):
        info = ""
        if self.is_local:
            info += "local["
            info += self.name
            info += "]"
        else:
            info += "remote["
            info += self.name
            info += ":"
            info += self.version
            info += "]"

        return info

    def parse_deps(self):
        """parse dep library"""
        pass


class ProjectInfo(object):
    """tmake project class"""
    AOP_CONFIG_KEY_WORD = "aop"  # CI_CONFIG.json中aop配置的key

    def __init__(self):
        # path for abotr.proj
        self.path = ""

        # folder for abotr.proj
        self.folder = ""

        # target platform for project
        self.target = ""  # android etc

        # build config for project
        self.build_config = "debug"

        self.target_alias = ""  # Embedded systems, cross-compilation, use the alias

        self.__deep = 1  #

        # dep libraries
        self.deps_libs = []

        self.local_deps_projects = []  # list(ProjectInfo)

        # 依赖的git源码
        self.git_deps = []  # 里面是{"git": "", "tag": ""} 这种数据
        # 依赖的库信息
        self.library_deps = {}  # 里面是{"GNaviUtils": "2.0.0"} 这种数据

        self.libraries = {}
        self.binaries = {}
        self.apps = {}
        self.resources = {}
        self.tasks = {}
        self.external_builds = {}

        self.setting = {}
        self.global_config = {}
        self.remove_default_flags = False
        self.ci_config_file = "CI_CONFIG.json"
        self.modules_key_word = "modules"
        self.feature_key_word = "feature"
        self.feature_prefix = "feature_"
        self.feature_macro_dict = {}
        self.work_path = ""
        self.module_name = ""

        # aop信息
        self.aop_config_dict = {}

    def get_build_base_folder(self):
        """
        get build folder
        e.g. /PROJECT_FOLDER/build/ios/simulator/debug
        """
        return os.path.join(self.folder, "build")

    def get_build_folder(self, arch):
        """
        get build folder
        e.g. /PROJECT_FOLDER/build/ios/simulator/debug
        """
        path = os.path.join(self.get_build_base_folder(),
                            self.target,
                            arch,
                            self.build_config)

        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def project_name(self):
        """get project name"""
        if self.setting.has_key('project_name'):
            return self.setting['project_name']
        else:
            return "proj"

    def __str__(self):
        info = "project:[{}]".format(id(self))

        if self.setting.has_key('project_name'):
            info += str(self.setting['project_name'])
        else:
            info += 'DEFAULT'
        info += '\n'

        for key in self.libraries:
            info += "    library:" + key + "\n"

        for key in self.binaries:
            info += "    binary:" + key + "\n"

        info += "   deep:" + str(self.__deep) + "\n"
        info += self.print_import(1)

        return info

    def print_import(self, level):
        """print import string"""
        info = ""
        # info += level * 4 * ' ' + "path:" + self.path + "\n"
        for project in self.local_deps_projects:
            info += level * 4 * ' ' + "import:" + project.path + "\n"
            info += project.print_import(level + 1)
        return info

    def init_vars(self):
        """ init local vars for parse """
        pass

    def get_deep(self):
        return self.__deep

    def set_deep(self, deep):
        if deep <= self.__deep:
            return
        self.__deep = deep
        for child in self.local_deps_projects:
            child.set_deep(deep + 1)

    def append_dep_project(self, project):
        """append dep project"""
        # print self.path, "=>", project.path
        self.local_deps_projects.append(project)
        # print id(self), id(project)
        # print "import count:" + str(len(self.local_deps_projects)) + "\n"

    def has_module(self, module_name):
        is_find = False
        for item in (self.libraries, self.binaries, self.apps):
            if module_name in item:
                is_find = True
                break
        return is_find

    def parse_ci_config(self, project_path):
        """
        解析CI_CONFIG.json
        :param project_path:  工程路径
        :return:
        """
        self.__parse_ci_config_aop_info(project_path)
        self.__parse_ci_config_feature_info(project_path)

    def __parse_ci_config_aop_info(self, project_path):
        """
        解析CI_CONFIG.json中的aop配置
        :param project_path:  工程路径
        :return:
        """
        core.i("parse aop config... {}".format(project_path))
        self.work_path = project_path
        # 检测ci_config.json文件是否存在
        ci_config_file_path = os.path.join(project_path, self.ci_config_file)
        if not os.path.exists(ci_config_file_path):
            core.e("{} not found in {}, skip!".format(self.ci_config_file, project_path))
            return

        # 加载ci_config.json内容
        try:
            ci_config_dict = json.loads(tmake_utils.read_all_from_file(ci_config_file_path))
        except Exception, e:
            traceback.print_exc()
            raise core.TmakeException("parse [{}] error, {}".format(self.ci_config_file, repr(e)))

        if ProjectInfo.AOP_CONFIG_KEY_WORD in ci_config_dict:
            self.aop_config_dict = ci_config_dict[ProjectInfo.AOP_CONFIG_KEY_WORD]
        else:
            core.i("`{}` not found in {}, skip!".format(self.modules_key_word, self.ci_config_file))
        core.i("parse aop config finished {}".format(project_path))

    def __parse_ci_config_feature_info(self, work_path):
        """
        解析CI_CONFIG.json中的Feature化配置, 生成Feature头文件
        :param work_path:  工作路径
        :return:
        """
        module = core.data.arguments.get_opt('-f')
        if module is None:
            return

        core.i("update feather headers... {}".format(work_path))
        self.work_path = work_path
        # 校验文件
        source_file_path = os.path.join(work_path, self.ci_config_file)
        if not os.path.exists(source_file_path):
            core.e("{} not found in {}, skip!".format(self.ci_config_file, work_path))
            return

        # 解析字典内容
        ci_config_dict = {}
        try:
            ci_config_dict = json.loads(tmake_utils.read_all_from_file(source_file_path))
        except Exception, e:
            traceback.print_exc()
            raise core.TmakeException("parse [{}] error, {}".format(self.ci_config_file, repr(e)))
        core.v("ci_config_dict = {} ...".format(ci_config_dict))

        if self.modules_key_word not in ci_config_dict:
            core.TmakeException("`{}` not found in {}, skip!".format(self.modules_key_word, self.ci_config_file))
            return

        feature_dict, arch_dict, support_arch_dict = self.__get_feature_info(ci_config_dict)
        self.__generate_headers(work_path, feature_dict)

    def __generate_headers(self, dir, feature_dict):
        """
        覆盖式写入宏定义头文件
        :param path: 文件路径，相对路径或者全路径
        :param feature_dict: {"section1":{"ke1":"value1"},"section2":{"ke1":"value1"}}
        :return:
        """
        if not isinstance(feature_dict, dict):
            raise core.TmakeException("Input param2 must be a dict!!!")
        file_path = ""
        try:
            for key, value in feature_dict.items():
                self.feature_macro_dict[key] = value
                file_path = os.path.join(dir, self.modules_key_word, key)
                if not os.path.exists(file_path):
                    os.makedirs(file_path)
                file_path = os.path.join(file_path,  self.feature_key_word + ".h")
                f = open(file_path, "w")
                project_name = dir.split('/')[-1]
                model = "#ifndef __{}__\n".format(project_name.upper() + '_' + self.feature_key_word.upper())
                f.write(model)
                model = "#define __{}__\n\n".format(project_name.upper() + '_' + self.feature_key_word.upper())
                f.write(model)
                macro_list = value.split(",")
                for item in macro_list:
                    if not item:
                        break
                    macro_info = item.split("=")
                    macro_key = macro_info[0].replace("-D", "")
                    macro_value = macro_info[1]
                    if macro_value.upper() == "TRUE":
                        ret = "1"
                    else:
                        ret = "0"
                    model = "#define {} {}\n".format(macro_key, ret)
                    f.write(model)
                f.write("\n")
                model = "#endif\n"
                f.write(model)
                f.close()
                core.s("generate header success: {}".format(file_path))
        except:
            core.TmakeException("generate header failed: {}".format(file_path))

    def get_feature_headers_flags(self):
        flags = ""
        module = ''
        if self.module_name:
            module = self.module_name
        else:
            module = core.data.arguments.get_opt('-f')
        if module is None:
            return flags
        header_path = os.path.join(self.work_path, self.modules_key_word, module, self.feature_key_word + ".h")
        header_path = header_path.replace("\\", "/")
        if not os.path.exists(header_path):
            return flags
        if "qnx" in self.target:
            flags = " -Wp,-include{} ".format(header_path)
        elif "windows" not in self.target:
            flags = " -include {} ".format(header_path)
        else:
            flags = " /FI {} ".format(header_path)
        return flags

    def __get_feature_info(self, feature_dict):
        """
        计算库依赖信息
        :param feature_dict:
        :return:
        """
        result_dict = OrderedDict()
        arch_result_dict = OrderedDict()
        support_arch_result_dict = OrderedDict()
        if self.modules_key_word in feature_dict and feature_dict[self.modules_key_word]:
            dict = feature_dict[self.modules_key_word]
            for key in dict.keys():
                module_dict = dict[key]
                if module_dict and "features" in module_dict:
                    feature_list = module_dict["features"]
                    feature_macro = ""
                    if feature_list:
                        for feature_info in feature_list:
                            if "name" not in feature_info:
                                continue
                            feature_name = feature_info["name"]
                            feature_macro += feature_info["macro"] + ","
                        if feature_macro:
                            feature_macro = feature_macro[0:len(feature_macro)-1]
                            result_dict[key] = feature_macro
                    else:
                        result_dict[key] = ''
                if module_dict and "arch" in module_dict:
                    arch_result_dict[key] = module_dict["arch"]
                if module_dict and "support_arch" in module_dict:
                    support_arch_result_dict[key] = module_dict["support_arch"]
        return result_dict,arch_result_dict,support_arch_result_dict

    def get_feature_macro_dict(self):
        return self.feature_macro_dict
