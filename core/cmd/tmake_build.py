    #!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
print tmake verson
"""

import json

import core

from core.utils.tmake_cmake import *

class CommandBuild(core.Command):
    """
    help command
    """
    def help(self):
        """tmake build help"""
        return "<usage>: tmake build [[no-test|nt] | [all-proj-test|apt]] " + \
               " [encrypt=<filepath>]  [-vs custom vs version] "

    def run(self):
        """plugin main entry"""
        self.param_check()
        arch_list = core.get_archs()
        for arch in arch_list:
            self.arch = arch
            try:
                self.acg_list = general_cmake_info(arch, True)
            except core.SkipException:
                continue
            self.build()
            acg = self.acg_list[-1]
            if not self.no_test:
                if not acg.info.tasks:
                    core.v("There is no task to run.")
                elif core.data.target != core.data.platform.host:
                    info = ""
                    for item in acg.info.tasks:
                        info += " " + item.name
                    core.v("There have task[{}] to run, but host and target is not same, skip!".format(info))
                else:
                    self.__run_test(acg.info.tasks)

    def param_check(self):
        self.no_test = self.arguments.has_opt("nt") or self.arguments.has_opt("no-test")

    def build(self):
        for acg in self.acg_list:
            # fusion类型，并且libraries数量为0的直接返回
            if acg.arch == core.TARGET_CPU_FUSION and not len(acg.info.libraries):
                continue
            run_cmake_build(acg)
            self.post_build_cp_lib(acg)
            tmake_utils.cp_exe_deps(acg, acg.info.path_info.build_symbol_path)
            if core.data.use_cmakelist or (core.data.use_proj_cmakelist and acg.info.external_builds):
                delete_src_file(acg.info.path_info.build_symbol_path)
                delete_src_file(os.path.join(acg.info.path_info.build_path, core.BUILD_INSTALL_PREFIX))
                delete_empty_dir(acg.info.path_info.build_symbol_path)
                delete_empty_dir(os.path.join(acg.info.path_info.build_path, core.BUILD_INSTALL_PREFIX))
            self.save_success_build_info(acg)

    def post_build_cp_lib(self, acg):
        # IOS平台的symbol_path会根据config添加子目录，将子目录下的文件都拷贝到symbol_path下
        if acg.info.build_target == core.PLATFORM_IOS or "wince" in self.arch:
            symbol_path = acg.path.build_symbol_path
            if acg.info.build_config == core.CONFIG_DEBUG:
                subdir_name = "Debug"
            elif acg.info.build_config == core.CONFIG_RELWITHDEBINFO:
                subdir_name = "RelWithDebInfo"
            else:
                subdir_name = "Release"
            # move xxx/bin/Debug to xxx/Debug
            subdir = os.path.join(symbol_path, subdir_name)
            if os.path.exists(subdir):
                temp_dir = os.path.join(acg.path.build_path, subdir_name)
                shutil.move(subdir, temp_dir)
                # rm xxx/bin
                shutil.rmtree(symbol_path)
                # move xxx/Debug to xxx/bin
                shutil.move(temp_dir, symbol_path)
        if acg.info.build_target == core.PLATFORM_WINDOWS and "wince" in self.arch:
            export_path = acg.path.build_installed_path
            symbol_path = acg.path.build_symbol_path
            if os.path.exists(export_path):
                shutil.rmtree(export_path)
            shutil.copytree(symbol_path, export_path)

        library_names = []
        if core.data.use_cmakelist or (core.data.use_proj_cmakelist and acg.info.external_builds):
            if abtcoreor.data.arguments.tmake_cmd() == "project":
                libs_dir = os.path.join(core.data.project.get_build_folder(self.arch), core.BUILD_OUTPUT_NAME)
            else:
                libs_dir = os.path.join(core.data.project.get_build_folder(self.arch), core.BUILD_OUTPUT_NAME)
            libs_info = get_libs_info(libs_dir)
            library_list = []
            for item in libs_info:
                bfind = False
                for library in acg.info.libraries:
                    if item.split(":")[0] == library.name:
                        bfind = True
                        break
                if bfind:
                    continue
                library_info = LibraryInfo()
                library_info.name = item.split(":")[0]
                library_info.link_style = item.split(":")[1]
                library_info.deps = []
                library_info.exported_headers = []
                library_list.append(library_info)

            for library in acg.info.libraries:
                library_names.append(library.name)
            acg.info.libraries += library_list
        for library in acg.info.libraries:
            #headers
            if library.name not in library_names and (core.data.use_cmakelist or (core.data.use_proj_cmakelist and acg.info.external_builds)):
                src_dir = os.path.join(acg.path.build_path, core.BUILD_INSTALL_PREFIX)
                #dst_dir = acg.path.get_local_export_include_path(library.name)
                dst_dir = os.path.join(acg.path.local_export_path, library.name)
                src_dir = src_dir.replace("\\", "/")
                dst_dir = dst_dir.replace("\\", "/")
                move_header_files(src_dir, dst_dir)
                delete_libs(dst_dir)
                delete_empty_dir(dst_dir)
            libs = tmake_utils.get_libname_on_platform(core.data.target, library.name, library.link_style)
            # lib
            des_dir = acg.path.get_local_export_lib_path(library.name)
            if os.path.exists(des_dir):
                shutil.rmtree(des_dir)
            if not os.path.exists(des_dir):
                os.makedirs(des_dir)
            for lib in libs:
                lib_path = os.path.join(acg.path.build_installed_path, lib)
                if os.path.exists(lib_path):
                    # IOS平台编译的export库没有strip(去掉符号)， 这里会强制去符号
                    # mac平台编译的export动态库，调用strip时会失败。这里会再次调用一次
                    if (core.data.target == core.PLATFORM_IOS
                        or core.data.target == core.PLATFORM_MAC) \
                            and library.link_style == abtcoreor.CXX_LIBRARY_LINK_STYLE_SHARED:
                        tmake_utils.stripSymbols(lib_path)
                    tmake_utils.copy(lib_path, os.path.join(des_dir, lib))
                else:
                    core.e(
                        '{} is not generate , Make sure that no functions or variables are exported ! '.format(
                            lib_path))
            # libsys
            des_dir = acg.path.get_local_export_libsys_path(library.name)
            if os.path.exists(des_dir):
                shutil.rmtree(des_dir)
            if not os.path.exists(des_dir):
                os.makedirs(des_dir)
            for lib in libs:
                lib_path = os.path.join(acg.path.build_symbol_path, lib)
                if os.path.exists(lib_path):
                    tmake_utils.copy(lib_path, os.path.join(des_dir, lib))
                else:
                    core.e(
                        '{} is not generate , Make sure that no functions or variables are exported ! '.format(
                            lib_path))

    def save_success_build_info(self, acg):
        alllibs = []
        for library in acg.info.libraries:
            core.v("save success build info of :" + library.name)
            a = {'m': library.name, 'deps': library.deps, 'eh': library.exported_headers, 'ls': library.link_style}
            alllibs.append(a)

        config = {
            't': core.data.target,
            'c': core.data.build_config,
            'a': self.arch,
            'l': alllibs
        }
        jsonc = json.dumps(config)
        json.dump(jsonc, open(acg.path.success_build_status_file_path, 'w'))

    def __run_test(self, task_list):
        """
        对 tmake_host_tester_task 的支持
        :param task_list:
        :return:
        """
        task_name_list = []
        for task in task_list:
            # 配置了并且跟当前编译的config不一致的情况下就跳过
            if task.config and task.config != core.data.build_config:
                core.v("skip task {}.".format(task.name))
                continue
            task_name_list.append(task.name)
        if task_name_list:
            argus = self.arguments.clone(["run", core.GLOBAL_SEPARATED.join(task_name_list)])
            core.exec_tmake_command(argus)


def main():
    """
    build的核心逻辑
    :return:
    """
    return CommandBuild()