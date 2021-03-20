#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
print tmake verson
"""
import os
import shlex
import subprocess
from core import PlatformInfo
from core.utils.PropertiesParser import PropertiesParser
from core.utils.tmake_cmake import *


class CommandProject(core.Command):
    """
    project command
    """

    def __init__(self):
        core.Command.__init__(self)
        self.param_all = 'all'
        self.param_silent = 'silent'
        self.param_ide_name = ''
        self.template_folder = core.data.arguments.get_opt("-tp")  # android studio项目需要传递模板
        # vs系列及xcode生成对应project文件，用命令打开相关ide
        # cdt4生成对应project文件，但是需要手动的import
        # blocks未验证
        # clion、studio、qtc直接打开CMakeLists.txt文件
        self.supported_list = ['vs2017', 'vs2015', 'vs2013', 'vs2012', 'vs2010', 'vs2008',
                               'xcode', 'cdt4', 'blocks', 'clion', 'studio', 'qtc']

    def help(self):
        """tmake project help"""
        return 'usage : tmake project [{}] [open]'.format("|".join(self.supported_list))

    def run(self):
        arch_list = core.get_archs()
        self.param_check()

        for arch in arch_list:
            # fusion类型的生成project跳过
            if arch == core.TARGET_CPU_FUSION:
                continue

            # 生成CMakeList
            try:
                acg_list = general_cmake_info(arch, False)
            except core.SkipException:
                continue

            # 拼接在一起写入文件
            all_text = ""
            acg = None
            for acg in acg_list:
                all_text += acg.cmake_text
            last_acg = acg_list[-1]
            if not core.data.use_cmakelist:
                cmake_path = os.path.join(last_acg.path.project_path, core.CMAKE_SCRIPT_FILE_NAME)
                core.write_entire_file(cmake_path, all_text)
                cmake_cache_path = os.path.join(last_acg.path.project_path, core.CMAKE_CACHE_FILE_NAME)
            else:
                cmake_path = os.path.join(last_acg.path.project_folder, core.CMAKE_SCRIPT_FILE_NAME)
                cmake_cache_path = os.path.join(last_acg.path.project_folder, core.CMAKE_CACHE_FILE_NAME)

            # 删除cache文件
            if os.path.exists(cmake_cache_path):
                os.remove(cmake_cache_path)

            custom_asset_target = ''
            # studio不需要生成project信息，只修改build.gradle文件。
            if self.param_ide_name.startswith("studio"):
                self.__modify_studio_project_file(acg.info.path_info.project_path)
                # custom_asset_target = os.path.join(tmake_path(self.template_folder), "app/src/main/assets")
            else:
                if not core.data.use_cmakelist:
                    cmake_list_path = last_acg.path.project_path
                else:
                    cmake_list_path = last_acg.path.project_folder
                run_cmake_project(last_acg, cmake_list_path, self.param_ide_name)
            # 复制资源到指定目录
            # self.__copy_assets_to_custom_target(last_acg, custom_asset_target)
            # # 复制动态库
            # comm_utils.cp_exe_deps(acg, acg.info.path_info.project_bin_path)
            # # 打开
            if self.arguments.has_opt('open'):
                self.__open_project(last_acg)

    def param_check(self):

        argv = self.arguments.args()
        if len(argv) > 0:
            if argv[0] not in self.supported_list:
                core.i(self.help())
                raise core.TmakeException('{} is error, must be in {}'.format(argv[0], self.supported_list))
        else:
            core.i(self.help())
            raise core.TmakeException('project failed')
        self.param_ide_name = argv[0]
        core.data.environment.update_vs_tool_name(self.param_ide_name)

    def __open_project(self, last_acg):
        """
        打开项目
        :param last_acg:
        :return:
        """
        project_path = last_acg.path.project_path
        project_name = last_acg.info.project_name
        cmd = ""
        if self.param_ide_name == 'xcode':
            if core.data.use_cmakelist:
                project_name = self.find_project_name(project_path, ".xcodeproj")
            cmd = 'open \"%s\"' % (os.path.join(project_path, project_name + '.xcodeproj'))
        elif self.param_ide_name.startswith("vs20"):
            if core.data.use_cmakelist:
                project_name = self.find_project_name(project_path, ".sln")
            cmd = '\"%s\" \"%s\"' % (
                core.data.environment.get_vs_ide_path(), os.path.join(project_path, project_name + '.sln'))
        elif self.param_ide_name.startswith("blocks"):
            project_path = os.path.join(project_path, '.cbp')
            cmd = self.open_ide_command('codeblocks', '', None, project_path)
        elif self.param_ide_name.startswith("cdt4"):
            core.s("请手动打开eclipse，并导入本地已存在项目，项目路径为： {}".format(project_path))
            return
        elif self.param_ide_name.startswith("clion"):
            project_path = os.path.join(project_path, 'CMakeLists.txt')
            cmd = self.open_ide_command('clion.sh', 'Clion', 'clion', project_path)
        elif self.param_ide_name.startswith("qtc"):
            project_path = os.path.join(project_path, 'CMakeLists.txt')
            cmd = self.open_ide_command('qtcreator', "Qt Creator", 'qtcreator', project_path)
            core.i("如果是带界面的qt项目请把qt使用的cmake配置为： {}".format(core.data.cmake_path))
        elif self.param_ide_name.startswith("studio"):
            if not self.template_folder:
                raise core.TmakeException("stuido project must input -tp. [-tp means android app project]")
            cmd = self.open_ide_command(None, 'Android Studio', None, self.template_folder)
        else:
            cmd = None
            os.startfile(os.path.join(project_path))
        try:
            if cmd:
                # linux及windows的打开方式会卡住控制台，使用subprocess.Popen。mac使用PlatformInfosubprocess.call可以有更多的提示
                if PlatformInfo.is_mac_system():
                    ret = subprocess.call(cmd, shell=True)
                    if ret != 0:
                        raise core.TmakeException('执行 {} 报错，请检查对应软件是否安装？'.format(cmd))
                else:
                    subprocess.Popen(shlex.split(cmd), shell=False)
        except Exception as e:
            raise core.TmakeException('error msg : {}'.format(e))
        core.s('{} open succeed !'.format(self.arguments.work_path()))

    def open_ide_command(self, linux_ide_name, mac_ide_name, windows_ide_name, full_path):
        """
        打开ide的通用方法
        :param linux_ide_name: linux上ide名字
        :param mac_ide_name: -a xx打开的名字，mac上使用
        :param windows_ide_name: windows上ide名字
        :param full_path: 要打开文件的全路径
        :return:
        """
        if PlatformInfo.is_linux_system():
            ide_name = linux_ide_name
        elif PlatformInfo.is_windows_system():
            ide_name = windows_ide_name
        else:
            ide_name = mac_ide_name
        # 设置为None表示某ide不支持该平台
        if ide_name is None:
            raise Exception("{} is not support in this platform.".format(self.param_ide_name))
        if PlatformInfo.is_linux_system() or PlatformInfo.is_windows_system():
            if tmake_utils.is_in_system_path(ide_name):
                cmd = "{} \"{}\"".format(ide_name, full_path)
            else:
                raise Exception("无法打开[{0}]，请检查，你可能需要把[{0}]的父目录设置到环境变量里。".format(ide_name))
        else:
            cmd = 'open \"{}\" {}'.format(full_path, "-a \"{}\"".format(ide_name) if ide_name else "")
        core.s("open cmd: {}".format(cmd))
        return cmd

    def __modify_studio_project_file(self, project_path):
        if not self.template_folder or not self.param_ide_name.endswith("studio"):
            return

        cmake_path = os.path.join(project_path, "CMakeLists.txt")
        gradle_properties = os.path.join(self.template_folder, "gradle.properties")
        properties_parser = PropertiesParser()
        properties_parser.read(gradle_properties)
        properties_parser.add("CMAKE_PATH", cmake_path)
        properties_parser.save()

def main():
    """plugin main entry"""
    return CommandProject()
