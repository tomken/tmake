    #!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
print tmake verson
"""

import core
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
                cmake_path = os.path.join(last_acg.path.project_path, CMAKE_SCRIPT_FILE_NAME)
                core.write_entire_file(cmake_path, all_text)
                cmake_cache_path = os.path.join(last_acg.path.project_path, CMAKE_CACHE_FILE_NAME)
            else:
                cmake_path = os.path.join(last_acg.path.project_folder, CMAKE_SCRIPT_FILE_NAME)
                cmake_cache_path = os.path.join(last_acg.path.project_folder, CMAKE_CACHE_FILE_NAME)

            # 删除cache文件
            if os.path.exists(cmake_cache_path):
                os.remove(cmake_cache_path)

            custom_asset_target = ''
            # studio不需要生成project信息，只修改build.gradle文件。
            if self.param_ide_name.startswith("studio"):
                self.__modify_studio_project_file(acg.info.path_info.project_path)
                custom_asset_target = os.path.join(tmake_path(self.template_folder), "app/src/main/assets")
            else:
                if not core.data.use_cmakelist:
                    cmake_list_path = last_acg.path.project_path
                else:
                    cmake_list_path = last_acg.path.project_folder
                run_cmake_project(last_acg, cmake_list_path, self.param_ide_name)
            # 复制资源到指定目录
            self.__copy_assets_to_custom_target(last_acg, custom_asset_target)
            # 复制动态库
            comm_utils.cp_exe_deps(acg, acg.info.path_info.project_bin_path)
            # 打开
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


def main():
    """plugin main entry"""
    return CommandProject()

