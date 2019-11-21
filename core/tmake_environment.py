#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
class environment file
"""
import os

from .tmake_exception import TmakeException
from .tmake_platform import PlatformInfo
from .tmake_log import *


class VSToolInfo(object):
    VS_VERSION_MAP = {"vs2017": 15, "vs2015": 14, "vs2013": 12, "vs2012": 11, "vs2010": 10, "vs2008": 9}
    VS_VERSION_LIST = VS_VERSION_MAP.keys()
    VS_VERSION_LIST.sort(reverse=True)

    def __init__(self):
        self.version = ""
        self.install_root = ""
        self.ide_tool_path = ""

    def __str__(self):
        return str(self.__dict__)

    def get_build_tool_by_arch(self, arch):
        if self.version == "vs2017":
            if arch.lower().endswith(core.TARGET_CPU_X64):
                bin_path = "VC/Auxiliary/Build/vcvars64.bat"
            else:
                bin_path = "VC/Auxiliary/Build/vcvars32.bat"
        else:
            if arch.lower().endswith(core.TARGET_CPU_X64):
                bin_path = "VC/bin/amd64/vcvars64.bat"
            else:
                bin_path = "VC/bin/vcvars32.bat"
        from core.utils import utils
        return utils.fix_path_style(os.path.join(self.install_root, bin_path))


class EnvironmentInfo(object):
    """
    tmake EnvironmentInfo
    """

    def __init__(self, custom_vs):
        # vs信息
        self.__vs_tool_info = VSToolInfo()
        self.__all_vs_tools = []
        self.custom_vs = custom_vs
        if custom_vs and custom_vs not in VSToolInfo.VS_VERSION_MAP.keys():
            raise TmakeException("custom vs tools must in:{}".format(VSToolInfo.VS_VERSION_MAP.keys()))
        self.__init_vs_tools()

    def __show_help(self):
        tip_info = "\n"
        tip_info += "first ensure you have installed Virsual Studio "
        if self.custom_vs:
            tip_info += "of {}".format(self.custom_vs)
        tip_info += "!\n"
        tip_info += "then check your environment, there should hava values like this:\n"
        for key in VSToolInfo.VS_VERSION_MAP.keys():
            tip_info += "VS{}0COMNTOOLS:{} install path or common tools path\n".format(VSToolInfo.VS_VERSION_MAP[key],
                                                                                       key)
        log.e(tip_info)

    def get_vs_tool_path(self, arch):
        """
        获取vs的环境变量文件全路径
        :return:
        """
        vs_build_tool = self.__vs_tool_info.get_build_tool_by_arch(arch)
        if not os.path.exists(vs_build_tool):
            core.e("{} is not exist!".format(vs_build_tool))
            self.__show_help()
            raise TmakeException('in windows platform, tmake need visual studio software, please check!')
        return vs_build_tool

    def get_vs_ide_path(self):
        """
        获取vs的可执行程序全路径，用来打开project
        :return:
        """
        return self.__vs_tool_info.ide_tool_path

    def update_vs_tool_name(self, vs_name):
        """
        project的时候更新vs版本
        :param vs_name:
        :return:
        """
        if not PlatformInfo.is_windows_system():
            return
        if not self.custom_vs:
            self.custom_vs = vs_name
            self.__vs_tool_info = VSToolInfo()
            self.__filter_custom_vs()
            self.__show_vs_version_info()
        elif self.custom_vs != vs_name:
            raise TmakeException("your custom vs version is different with project vs version!")

    def __init_vs_tools(self):
        """
        查找vs的路径
        :return:
        """
        if not PlatformInfo.is_windows_system():
            return
        self.__find_2017_tools()
        for version in VSToolInfo.VS_VERSION_LIST:
            env_key = 'VS{}0COMNTOOLS'.format(VSToolInfo.VS_VERSION_MAP[version])
            common_path = os.getenv(env_key)
            if common_path:
                if "Common7" in common_path:
                    install_folder = common_path[:common_path.find("Common7")]
                else:
                    install_folder = common_path
                log.v("found vs tool in the environment :{}={} ".format(env_key, common_path))
                self.__wrap_vs_info(install_folder, version)
        self.__filter_custom_vs()
        if self.custom_vs and not self.__vs_tool_info.install_root:
            self.__show_help()
            raise TmakeException("can not find Virsual Studio path with custom version: {}".format(self.custom_vs))
        self.__show_vs_version_info()

    def __show_vs_version_info(self):
        for item in self.__all_vs_tools:
            log.v("all vs tools info:\n" + str(item))
        log.v("using vs tool info:\n" + str(self.__vs_tool_info))

    def __wrap_vs_info(self, install_folder, version):
        """
        包装vs信息为对象
        :param install_folder:
        :param version:
        :return:
        """

        vs_tool_info = VSToolInfo()
        vs_tool_info.install_root = install_folder
        vs_tool_info.version = version
        from core.utils import utils
        vs_tool_info.ide_tool_path = utils.fix_path_style(os.path.join(install_folder, "Common7/IDE/devenv.exe"))
        self.__all_vs_tools.append(vs_tool_info)

    def __find_2017_tools(self):
        """
        针对2017的特殊处理
        :return:
        """
        env_key = 'VS{}0COMNTOOLS'.format(VSToolInfo.VS_VERSION_MAP["vs2017"])
        real_path = os.getenv(env_key)
        if real_path and os.path.exists(real_path):
            dir_list = os.listdir(real_path)
            for dir_name in dir_list:
                var_path = os.path.join(real_path, dir_name, "VC/Auxiliary/Build/vcvars32.bat")
                if os.path.isfile(var_path):
                    log.v("found vs tool in the specified path:{} ".format(var_path))
                    self.__wrap_vs_info(os.path.join(real_path, dir_name), "vs2017")
                    break

    def __filter_custom_vs(self):
        """
        从所有的vs环境中过滤自定义的vs版本信息
        :return:
        """
        if not self.__all_vs_tools:
            return
        if not self.custom_vs:
            self.__vs_tool_info = self.__all_vs_tools[0]
        else:
            for item in self.__all_vs_tools:
                if item.version == self.custom_vs:
                    self.__vs_tool_info = item
                    break


"""
  Visual Studio 15 2017
  Visual Studio 14 2015 [arch] = Generates Visual Studio 2015 project files.
                                 Optional [arch] can be "Win64" or "ARM".
  Visual Studio 12 2013 [arch] = Generates Visual Studio 2013 project files.
                                 Optional [arch] can be "Win64" or "ARM".
  Visual Studio 11 2012 [arch] = Generates Visual Studio 2012 project files.
                                 Optional [arch] can be "Win64" or "ARM".
  Visual Studio 10 2010 [arch] = Generates Visual Studio 2010 project files.
                                 Optional [arch] can be "Win64" or "IA64".
  Visual Studio 9 2008 [arch]  = Generates Visual Studio 2008 project files.
                                 Optional [arch] can be "Win64" or "IA64".
  Visual Studio 8 2005 [arch]  = Generates Visual Studio 2005 project files.
                                 Optional [arch] can be "Win64".
  Visual Studio 7 .NET 2003    = Generates Visual Studio .NET 2003 project
                                 files.
  Visual Studio 7              = Deprecated.  Generates Visual Studio .NET
                                 2002 project files.
  Visual Studio 6              = Deprecated.  Generates Visual Studio 6
                                 project files.
"""
