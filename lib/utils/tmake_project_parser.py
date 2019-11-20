#!/usr/bin/python2
# -*- coding:UTF-8 -*-
"""
tmake project parser
"""

from lib.info.tmake_builtin import *


def get_project_max_deep(project_list):
    """
    获取所有项目的最大深度
    :param project_list:
    :return:
    """
    max_deep = 0
    for project in project_list:
        if project.get_deep() > max_deep:
            max_deep = project.get_deep()
    return max_deep


def get_project_list(project):
    """
    递归获得所有项目的集合，配合层深来从最深层遍历
    :param project:
    :return:
    """
    all_projects = set()
    all_projects.add(project)
    if project.local_deps_projects:
        for item in project.local_deps_projects:
            all_projects |= get_project_list(item)
    return all_projects

def get_feature_name():
    feature_name = lib.data.arguments.get_opt('f')
    return feature_name


def parse(path, parent_project=None, module_name=None):
    """parse entry"""


    lib.v("project path=" + path)
    if not os.path.isabs(path):
        full_path = abtor_path(path)
    else:
        full_path = path

    # 直接用CMakeLists.txt
    lib.data.use_cmakelist = False
    if "CMakeLists.txt" in full_path:
        lib.data.use_cmakelist = True

    # 如果没有写文件名默认添加abtor.proj
    if "abtor.proj" not in full_path and not lib.data.use_cmakelist:
        full_path = os.path.join(full_path, "abtor.proj")

    new_project = __get_project(full_path)
    if new_project is not None:
        # This project is a deeper project dependencies,
        # the depth of the project than the deep dependence on + 1
        if parent_project is not None:
            parent_project.append_dep_project(new_project)
            new_project.set_deep(parent_project.get_deep() + 1)

        return new_project

    new_project = lib.data.new_project()
    new_project.path = full_path
    new_project.folder = os.path.dirname(full_path)
    __add_project(new_project)

    new_project.target = lib.data.target
    new_project.build_config = lib.data.build_config
    new_project.target_alias = lib.data.target_alias

    if parent_project is not None:
        new_project.set_deep(parent_project.get_deep() + 1)

    lib.data.current_project = new_project

    feature = ''
    if module_name:
        feature = module_name
    else:
        feature = lib.data.arguments.get_opt("-f")
    new_project.module_name = feature

    if not lib.data.use_cmakelist:
        lib.i("Being parsed: {}".format(full_path))
        proj_file = open(full_path)
        body = proj_file.read()
        proj_defines = lib.data.arguments.get_opts_by_prefix("-D")
        work_path = os.path.dirname(full_path)
        new_project.parse_ci_config(work_path)
        feature_macro_dict = new_project.get_feature_macro_dict()
        feature_key = feature
        if feature_macro_dict and feature_key and feature_key in feature_macro_dict:
            feature_value = feature_macro_dict[feature_key]
            macro_list = feature_value.split(",")
            for item in macro_list:
                item = item.replace("-D", "")
                proj_defines.append(item)
        # 命令行形式给proj文件设置值
        for item in proj_defines:
            if "=" in item:
                definition = parse_definition(item)
                exec definition

    # 这里重新给abtor_builtin里的发生变化的常量赋值
    from lib.info import tmake_builtin
    ABTOR_CPU_ARCH = tmake_builtin.ABTOR_CPU_ARCH
    # 获取当前命令
    ABTOR_CURRENT_CMD = lib.data.arguments.tmake_cmd()

    # 设置支持的路径参数及默认import的内容
    import sys
    path_utils = PathInfo(ABTOR_CPU_ARCH, new_project.folder)

    # 兼容旧的，添加ABTOR_WORK_PATH常量
    ABTOR_WORK_PATH = path_utils.project_folder
    os.chdir(ABTOR_WORK_PATH)

    if not lib.data.use_cmakelist:
        # 解析DEPS.conf，初始化abtor_deps变量，import配置项目
        deps_path = os.path.join(path_utils.project_folder, "DEPS.conf")
        if os.path.exists(deps_path):
            deps_dict = abtor_config(deps_path)
            if feature:
                section = feature+"_version"
                if section in deps_dict:
                    abtor_deps = deps_dict[section]
                else:
                    abtor_deps = deps_dict["version"]
                    #abtor.AbtorException("Section `{}` not in DEPS.conf".format(feature))
            else:
                abtor_deps = deps_dict["version"]
            if "local_project" in deps_dict:
                local_project_module_name = {}
                if feature:
                    section = feature + "_local_project"
                    if section in deps_dict:
                        local_project = deps_dict[section]
                    else:
                        local_project = deps_dict["local_project"]
                        #abtor.AbtorException("Section `{}` not in DEPS.conf".format(feature))

                    section = feature + "_local_project_module_name"
                    if section in deps_dict:
                        local_project_module_name = deps_dict[section]
                else:
                    local_project = deps_dict["local_project"]


                lib.data.current_project.library_deps = abtor_deps
                for key, value in local_project.items():
                    if key in abtor_deps and abtor_deps[key] == "local":
                        abtor_customer_version({key: abtor_deps[key]})
                        module_name = ''
                        if key in local_project_module_name:
                            module_name = local_project_module_name[key]
                        abtor_import([value], module_name)
                    elif key in abtor_deps and abtor_deps[key] == "local all":
                        abtor_customer_version({key: "local"})
                        abtor_import_all([value])
            # 自动添加git_deps内容
            if "git_deps" in deps_dict and deps_dict["git_deps"] \
                    and lib.data.arguments.abtor_cmd() in ["build", "project", "publish"]:
                from lib.utils.git_util import AbtorGitCheckout
                git_deps = AbtorGitCheckout(ABTOR_WORK_PATH, deps_dict["git_deps"],
                                            deps_dict.get('git_force_pull', None)).init_git_project()
                lib.data.current_project.git_deps = git_deps

        try:
            exec body
        except BaseException, e:
            import traceback
            traceback.print_exc()
            etype, value, tb = sys.exc_info()
            line_no = "unknown"
            while tb is not None:
                filename = tb.tb_frame.f_code.co_filename
                if filename == "<string>":
                    line_no = tb.tb_lineno
                tb = tb.tb_next
            raise lib.TmakeException("parser [abtor.proj] error, please check the file:" \
                                       "\nfile path: {} \nline number: {}  \nerror type: {}".format(full_path,
                                                                                                    line_no,
                                                                                                    e.message))
        proj_file.close()
        lib.i("Parsing is complete. {}".format(full_path))

    if parent_project:
        parent_project.append_dep_project(new_project)

    return new_project




def is_num(value):
    try:
        float(value)
        return True
    except ValueError:
        pass
    try:
        int(value)
        return True
    except ValueError:
        pass
    return False


def parse_definition(definition):
    result = definition.split("=")
    key = result[0]
    value = result[1]
    if value == "True" or value == "False" or is_num(value):
        assign = definition + ";"
    else:
        if (value.startswith("'") or value.startswith("\"")) \
                and (value.endswith("'") or value.endswith("\"")):
            assign = '{}={};'.format(key, value)
        else:
            assign = '{}=\'{}\';'.format(key, value)
    return assign


def __get_project(path):
    if not lib.data.param.has_key('projsmap'):
        return None
    projsmap = lib.data.param['projsmap']
    if projsmap.has_key(path):
        return projsmap[path]
    return None


def __add_project(project):
    if not lib.data.param.has_key('projsmap'):
        projsmap = {}
        lib.data.param['projsmap'] = projsmap
    projsmap = lib.data.param['projsmap']
    projsmap[project.path] = project
