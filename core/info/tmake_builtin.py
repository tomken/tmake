#!/usr/bin/python
# -*- coding: UTF-8 -*-
# pylint:disable=W0612,W0613
"""
tmake builtin funciton file
"""

import glob
import os

import core

# from tmake_project_parser import parse as pparser
from core.info.tmake_path_info import PathInfo
from core.utils import tmake_utils
import ConfigParser

TMAKE_HOST = core.data.platform.host
TMAKE_TARGET = core.data.arguments.get_opt("-t", "--target")
TMAKE_CONFIG = core.data.arguments.get_opt("-c")
TMAKE_CPU_ARCH = tmake_utils.get_archs()[0]  # build/project的时候会修改这个值

if TMAKE_CONFIG and TMAKE_CONFIG not in core.CONFIG_ALL:
    raise core.TmakeException("build config [-c] must in {}".format(core.CONFIG_ALL))


# 解决ConfigParser大小写不敏感的问题
class CustomConfigParser(ConfigParser.ConfigParser):
    def __init__(self, defaults=None):
        import ConfigParser
        ConfigParser.ConfigParser.__init__(self, defaults=None)

    def optionxform(self, optinostr):
        return optinostr


def tmake_config_write(path, conf_dict):
    """
    将字典类型的配置写入conf文件，覆盖式写入
    :param path: 文件路径，相对路径或者全路径
    :param conf_dict: {"section1":{"ke1":"value1"},"section2":{"ke1":"value1"}}
    :return:
    """
    full_path = tmake_path(path)
    if not isinstance(conf_dict, dict):
        raise core.Exception("input param2 must be a dict!!!")
    ver_conf = CustomConfigParser()
    for key, value in conf_dict.items():
        ver_conf.add_section(key)
        if not isinstance(value, dict):
            raise core.TmakeException("value must be a dict!!!")
        for inner_key, inner_value in value.items():
            ver_conf.set(key, inner_key, inner_value)
    ver_conf.write(open(full_path, "w"))
    core.log.s("write config success: {}\n{}".format(full_path, conf_dict))


def tmake_config(path):
    """解析配置文件，返回字典"""
    full_path = tmake_path(path)
    if not os.path.exists(full_path):
        raise core.TmakeException("file: {} not exist!!!".format(full_path))
    ver_conf = CustomConfigParser()
    ver_conf.readfp(open(full_path, "rb"))
    result_dict = {}
    for section in ver_conf.sections():
        inner_dict = {}
        for item in ver_conf.options(section):
            inner_dict[item] = ver_conf.get(section, item)
        result_dict[section] = inner_dict
    core.log.s("parse success: {}\n{}".format(full_path, result_dict))
    return result_dict


# 针对deps命令的特殊处理，不抛异常，而是返回固定字符串
IS_DEPS_UPDATING = False


def tmake_deps_info(dep_name):
    """
    返回从DEPS.conf中读取的版本信息
    :param dep_name:
    :return: 类似这种格式 xxxMap:9.18.100.34
    """
    # 动态库和静态库同相同的版本。
    fix_dep_name = dep_name.replace(core.SHARED_SUFFIX, "")
    library_deps = core.data.current_project.library_deps
    if fix_dep_name in library_deps:
        if library_deps[fix_dep_name] == "local":
            return fix_dep_name + ":" + library_deps[fix_dep_name]
        else:
            return dep_name + ":" + library_deps[fix_dep_name]
    # deps update命令解析依赖，如果不做特殊处理这里会抛找不到异常了
    elif IS_DEPS_UPDATING:
        return "deps_updating:deps_updating"
    else:
        raise core.TmakeException("cann't find [{}] from DEPS.conf, please check!!!".format(dep_name))


if TMAKE_TARGET is None:
    TMAKE_TARGET = TMAKE_HOST

if TMAKE_CONFIG is None:
    TMAKE_CONFIG = "debug"


def tmake_logv(msg):
    """log for v"""
    core.v(msg)


# script function
def tmake_logs(msg):
    """log for s"""
    core.s(msg)


# script function
def tmake_loge(msg):
    """log for e"""
    core.e(msg)


# script function
def tmake_logi(msg):
    """log for i"""
    core.i(msg)


def tmake_exit(msg):
    """exit lib build"""
    core.e(msg)
    quit()


def tmake_copy(origin_path, target_path):
    """lib复制操作"""
    tmake_utils.copy(origin_path, target_path)


def tmake_path(path):
    """
    get path for project
    """
    # 如果传入的是None，返回空字符串
    if path == None:
        return ""
    ret = path
    if not os.path.isabs(path):
        ret = os.path.join(core.data.current_project.folder, path)
    result = os.path.normpath(ret)
    if result:
        result = tmake_utils.fix_path_style(result)
    return result


def tmake_path_list(path_array):
    """path list"""
    if path_array is None:
        return []
    if not isinstance(path_array, list):
        path_array = [path_array]

    ret = set()
    for path in path_array:
        ret.add(tmake_path(path))
    return list(ret)


def tmake_glob(path, patterns=None, recursive=False):
    """tmake_glob"""
    if path is None:
        return []
    path = tmake_path(path)
    if patterns is None:
        patterns = '*'
    if not isinstance(patterns, list):
        patterns = [patterns]
    ret = []
    for reg in patterns:
        fs_glob = glob.glob(os.path.join(path, reg))
        if fs_glob:
            for file_path in fs_glob:
                if os.path.isfile(file_path):
                    ret.append(tmake_utils.fix_path_style(file_path))
        if recursive and os.path.exists(path):
            files = os.listdir(path)
            for f in files:
                file_path = os.path.join(path, f)
                if os.path.isdir(file_path):
                    tmp_ret = tmake_glob(file_path, patterns, recursive)
                    if tmp_ret:
                        ret.extend(tmp_ret)
    return list(set(ret))


def tmake_remove(all_list, removed_list):
    """remove path in list"""
    if all_list is None:
        return []
    if removed_list is None:
        return all_list
    if not isinstance(removed_list, list):
        removed_list = [removed_list]
    removed_list = set(removed_list)
    all_list = filter(lambda x: x not in removed_list, all_list)
    return all_list


def tmake_settings(tmake_minimum_required=None,
                   project_name=None,
                   valid=True, publish_server=None,
                   deps_download_servers=None,
                   deps_download_notneed_default_server=None,
                   default_download_server=None):
    """tmake_settings"""

    if not valid:
        return

    if project_name is None:
        project_name = "prj"

    core.data.current_project.setting = locals()


def tmake_global_cxx(include_dirs=None, lib_dirs=None,
                      defines=None, c_flags=None, cxx_flags=None,
                      build_vars=None, valid=True, cmake_command=None,
                      xcode_properties=None):
    """tmake_global_cxx"""

    if not valid:
        return

    core.data.current_project.global_config = locals()


def tmake_global_cxx(include_dirs=None, lib_dirs=None,
                     defines=None, c_flags=None, cxx_flags=None,
                     build_vars=None, valid=True, cmake_command=None,
                     xcode_properties=None):
    """tmake_global_cxx"""

    if not valid:
        return

    core.data.current_project.global_config = locals()


def tmake_cxx_library(name=None, version=None, publish=None,
                       deps=None, windows_deps=None, mac_deps=None, linux_deps=None,
                       android_deps=None, ios_deps=None, embedded_deps=None,
                       include_dirs=None, lib_dirs=None, frameworks=None, publish_info=None, framework_properties=None,
                       defines=None, headers=None, srcs=None, c_flags=None,
                       cxx_flags=None, linker_flags=None,
                       link_style=None, link_libs=None, link_all_symbol_libs=None, un_relink_deps=None,
                       exported_headers=None, exported_headers_by_folder=None, tasks=None, valid=True, properties=None,
                       pre_cmake_command=None, post_cmake_command=None, xctest_unit_src = None):
    """tmake_cxx_library"""

    if not valid:
        return
    if not link_style:
        raise core.TmakeException("{}'s link_style can not be null !!!".format(name))
    if link_style.lower() not in core.ALLOW_LINK_STYLE_LIST:
        raise core.TmakeException("link_style must in {}!".format(core.ALLOW_LINK_STYLE_LIST))
    core.data.current_project.libraries[name] = locals()


def tmake_cxx_library(name=None, version=None, publish=None,
                      deps=None, windows_deps=None, mac_deps=None, linux_deps=None,
                      android_deps=None, ios_deps=None, embedded_deps=None,
                      include_dirs=None, lib_dirs=None, frameworks=None, publish_info=None, framework_properties=None,
                      defines=None, headers=None, srcs=None, c_flags=None,
                      cxx_flags=None, linker_flags=None,
                      link_style=None, link_libs=None, link_all_symbol_libs=None, un_relink_deps=None,
                      exported_headers=None, exported_headers_by_folder=None, tasks=None, valid=True, properties=None,
                      pre_cmake_command=None, post_cmake_command=None, xctest_unit_src = None):
    """tmake_cxx_library"""
    if not valid:
        return
    if not link_style:
        raise core.TmakeException("{}'s link_style can not be null !!!".format(name))

    core.data.current_project.libraries[name] = locals()


def tmake_cxx_binary(name=None, version=None, publish=None, defines=None,
                      deps=None, windows_deps=None, mac_deps=None, linux_deps=None,
                      android_deps=None, ios_deps=None, embedded_deps=None,
                      include_dirs=None, lib_dirs=None, frameworks=None, publish_info=None,
                      qt_project=False, qt_components=None,
                      qt_ui=None, qt_moc_headers=None,
                      headers=None, srcs=None,
                      c_flags=None, cxx_flags=None, linker_flags=None, tasks=None,
                      valid=True, link_libs=None, properties=None, un_relink_deps=None,
                      pre_cmake_command=None, post_cmake_command=None, xctest_unit_src = None,
                      package_dynamic_lib = None, add_to_zip = None,
                      link_all_symbol_libs = None):
    """tmake_cxx_binary"""

    if not valid:
        return

    core.data.current_project.binaries[name] = locals()


def tmake_cxx_binary(name=None, version=None, publish=None, defines=None,
                     deps=None, windows_deps=None, mac_deps=None, linux_deps=None,
                     android_deps=None, ios_deps=None, embedded_deps=None,
                     include_dirs=None, lib_dirs=None, frameworks=None, publish_info=None,
                     qt_project=False, qt_components=None,
                     qt_ui=None, qt_moc_headers=None,
                     headers=None, srcs=None,
                     c_flags=None, cxx_flags=None, linker_flags=None, tasks=None,
                     valid=True, link_libs=None, properties=None, un_relink_deps=None,
                     pre_cmake_command=None, post_cmake_command=None, xctest_unit_src = None,
                     package_dynamic_lib = None, add_to_zip = None,
                     link_all_symbol_libs = None):
    """tmake_cxx_binary"""

    if not valid:
        return

    core.data.current_project.binaries[name] = locals()


def tmake_cxx_app(name=None, defines=None,
                  deps=None, windows_deps=None, mac_deps=None, linux_deps=None,
                  android_deps=None, ios_deps=None, embedded_deps=None,
                  include_dirs=None, lib_dirs=None, frameworks=None, plist=None,
                  qt_project=False, qt_components=None,
                  qt_ui=None, qt_moc_headers=None,
                  headers=None, srcs=None,
                  c_flags=None, cxx_flags=None, linker_flags=None, tasks=None,
                  valid=True, link_libs=None, properties=None,
                  pre_cmake_command=None, post_cmake_command=None,
                  version=None,
                  app_icon=None, launch_image=None, xctest_unit_src = None,
                  link_all_symbol_libs = None):
    """tmake_cxx_binary"""

    if not valid:
        return

    core.data.current_project.apps[name] = locals()


def tmake_cxx_resources(name=None, files=None, bundles=None, ide_target=None):
    """tmake_cxx_resources"""
    if files is not None and not isinstance(files, dict):
        files = {"Resource": files}
    core.data.current_project.resources[name] = locals()


def tmake_host_tester_task(name, command, config=None, work_directory=None,
                           args=None, pass_regular_expression=None,
                           timeout=None, valid=True):
    """tester task"""

    if not valid:
        return
    core.data.current_project.tasks[name] = locals()

def tmake_traverse(path, parent_project=None):
    fs = os.listdir(path)
    for f1 in fs:
        tmp_path = os.path.join(path, f1)
        if os.path.isdir(tmp_path):
            tmake_traverse(tmp_path, parent_project)
        else:
            if f1 == "core.proj":
                core.data.current_project = parent_project
                new_project = core.project_parse(tmp_path, parent_project)

def tmake_import_all(paths=None, valid=True):
    """project import all"""

    if not valid:
        return

    parent_project = core.data.current_project
    # print "import:" + project.path
    parent_project.local_deps_project_paths = locals()
    for path in paths:
        # 重置当前项目为parent_project
        tmake_traverse(path, parent_project)
    core.data.current_project = parent_project
    # import完成目录切换回来
    os.chdir(parent_project.folder)

def tmake_import(paths=None, module_name=None, valid=True):
    """project import"""

    if not valid:
        return

    parent_project = core.data.current_project
    # print "import:" + project.path
    parent_project.local_deps_project_paths = locals()
    for path in paths:
        # 重置当前项目为parent_project
        core.data.current_project = parent_project
        new_project = core.project_parse(path, parent_project, module_name)
    core.data.current_project = parent_project
    # import完成目录切换回来
    os.chdir(parent_project.folder)

def tmake_customerVersion(dict_params):
    """focse library name"""
    if dict_params:
        core.log.e("custom version: {}".format(dict_params))
    core.data.deps_mgr.add_conflict_solution(dict_params)


def tmake_customer_version(dict_params):
    """focse library name"""
    if dict_params:
        core.log.e("custom version: {}".format(dict_params))
    core.data.deps_mgr.add_conflict_solution(dict_params)


def tmake_include_dir(name, version=None):
    """
    get deps library include folder
    """
    out_dir = ""
    if version and 'local' not in version:
        out_dir = os.path.join(core.TMAKE_LIBRARIES_PATH,
                               name,
                               version,
                               core.data.target,
                               TMAKE_CPU_ARCH,
                               'include')
    else:
        project = tmake_utils.get_project_by_module_name(core.data.current_project, name)
        if not project:
            return out_dir
        path_info = PathInfo(TMAKE_CPU_ARCH, project.folder)
        out_dir = path_info.get_local_export_include_path(name)
    info_fmt = 'tmake_include_dir name :{} , version :{} , include_dir : {}'
    core.log.v(info_fmt.format(name, version, out_dir))
    return out_dir


# script function
def tmake_tmake_dir(name, version=None, symbol=False):
    """
    get deps library lib folder
    """
    out_dir = ""
    if version:
        if symbol:
            lib = 'libs_sym'
        else:
            lib = 'libs'
        out_dir = os.path.join(core.TMAKE_LIBRARIES_PATH,
                               name,
                               version,
                               core.data.target,
                               TMAKE_CPU_ARCH,
                               lib)
    else:
        project = tmake_utils.get_project_by_module_name(core.data.current_project, name)
        if not project:
            return out_dir
        path_info = PathInfo(TMAKE_CPU_ARCH, project.folder)
        if symbol:
            out_dir = path_info.get_local_export_libsys_path(name)
        else:
            out_dir = path_info.get_local_export_tmake_path(name)
    info_fmt = 'tmake_tmake_dir name :{} , version :{} , tmake_dir : {}'
    core.log.v(info_fmt.format(name, version, out_dir))
    return out_dir


# script function
def tmake_source_init(source_dict=None):
    """
    初始化代码，该方法不再需要手动调用，build、project的时候会自动调用
    """
    support_cmd = ["build", "project"]
    if core.data.arguments.tmake_cmd() not in support_cmd:
        core.log.e("tmake_source_init only work in cmd: :{}".format(",".join(support_cmd)))
        return
    workspace = core.data.current_project.folder
    core.log.i("current project path : {}".format(workspace))
    from core.utils.git_util import GitCheckout
    GitCheckout(workspace, source_dict).init_git_project()


def tmake_set_deps_tree_callback(callback_fun, callback_params):
    """
    设置解析回调，返回树状类型
    :param callback_fun:
    :param callback_params:
    :return:
    """
    core.data.deps_mgr.callback_fun = (callback_fun, callback_params, True, None)


def tmake_set_deps_callback(callback_fun, callback_params, exclude_rule=None):
    """
    设置解析回调，返回平铺类型
    :param callback_fun:
    :param callback_params:
    :param exclude_rule:
    :return:
    """
    core.data.deps_mgr.callback_fun = (callback_fun, callback_params, False, exclude_rule)


def tmake_library_deps(library_name):
    """
    获取库的所有依赖，在 deps_callback 中使用
    """
    return core.data.deps_mgr.library_deps(library_name)

def tmake_remove_default_flags():
    """tmake_cxx_library"""
    core.data.current_project.remove_default_flags = True

def tmake_external_build(name=None, version=None, publish=None, path=None, valid=True):
    """tmake_external_build"""
    if not valid:
        return
    core.data.current_project.external_builds[name] = locals()
    core.data.use_libProj_cmakelist = True
