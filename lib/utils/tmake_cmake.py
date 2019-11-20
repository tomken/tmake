#!/usr/bin/python2
# -*- coding: UTF-8 -*-
"""
cmake helper file
"""

import lib

def check_cmake():
    return True

def general_cmake_info(arch, write_file):
    """
    通过指令集来生成CMakeLists.txt
    :param arch:
    :return:
    """
    lib.data.change_project_arch(arch)
    acg_list = []
    __parse_project()
    all_projects = get_project_list(lib.data.project)
    max_deep = get_project_max_deep(all_projects)
    # 通过deep来从深向浅遍历项目
    have_build = set()
    for deep in range(0, max_deep):
        for project in all_projects:
            if project.get_deep() == max_deep - deep and project.folder not in have_build:
                print "start " + project.folder
                have_build.add(project.folder)
                lib.data.current_project = project
                if abtor.data.use_cmakelist:
                    write_file = False
                acg = load_cmake_plugin_and_generate(lib.data.target, arch, write_file)
                acg_list.append(acg)
    return acg_list