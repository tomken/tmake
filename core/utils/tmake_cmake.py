#!/usr/bin/python2
# -*- coding: UTF-8 -*-
"""
cmake helper file
"""

import core

from core.utils.tmake_project_parser import get_project_list, get_project_max_deep

from core.actions.tmake_action import *

def check_cmake():
    return True

def __parse_project():
    """
    解析project，不成功给出提示
    :return:
    """
    if not core.data.parse_project():
        core.e("work path = " + str(core.data.arguments.work_path()))
        raise core.TmakeException('project parse failed, please ensure work path is right!')


def general_cmake_info(arch, write_file):
    """
    通过指令集来生成CMakeLists.txt
    :param arch:
    :return:
    """
    core.data.change_project_arch(arch)
    acg_list = []
    __parse_project()
    all_projects = get_project_list(core.data.project)
    max_deep = get_project_max_deep(all_projects)
    # 通过deep来从深向浅遍历项目
    have_build = set()
    for deep in range(0, max_deep):
        for project in all_projects:
            if project.get_deep() == max_deep - deep and project.folder not in have_build:
                print "start " + project.folder
                have_build.add(project.folder)
                core.data.current_project = project
                if core.data.use_cmakelist:
                    write_file = False
                acg = load_cmake_plugin_and_generate(core.data.target, arch, write_file)
                acg_list.append(acg)
    return acg_list

def load_cmake_plugin_and_generate(target, arch, write_to_file=True):
    """
    load cmake plugin and generate CMakeList.txt
    """
    import_cmd = "import core.cmake_gens.tmake_cmake_generator_" + target
    call_cmd = "core.cmake_gens.tmake_cmake_generator_" + target + ".cmake_plugin_init(arch)"
    print ">>>:" + import_cmd
    # try:
    import core.cmake_gens.tmake_cmake_generator_mac
        # exec import_cmd
    # except ImportError:
    #    raise core.TmakeException("The target:" + target + " is not support! Please check your -t params!")
    acg = eval(call_cmd)
    core.data.action_mgr.run_befor_action(TMAKE_ACTION_CMAKE_LISTS, core.data, acg)
    acg.generate()
    core.data.action_mgr.run_after_action(TMAKE_ACTION_CMAKE_LISTS, core.data, acg)
    if write_to_file:
        core.write_entire_file(os.path.join(acg.path.build_path, CMAKE_SCRIPT_FILE_NAME), acg.cmake_text)
    core.data.action_mgr.run_befor_action(TMAKE_ACTION_PUBLISH_PROJECT, core.data, acg)
    return acg

def run_cmake_project(acg, cmake_list_path, name):
    """call cmake project"""
    core.data.action_mgr.run_befor_action(TMAKE_ACTION_CMAKE_PROJECT, core.data, acg)
    acg.make_project(cmake_list_path, name)
    core.data.action_mgr.run_after_action(TMAKE_ACTION_CMAKE_PROJECT, core.data, acg)
