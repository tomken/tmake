#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
tmake cmake info py file
"""
import os

import core
from core.info.tmake_path_info import PathInfo
from core.utils import tmake_utils


class CMakeResourceInfo(object):
    """cmake resource info class"""

    def __init__(self):
        self.name = ""
        self.files = {}  # 资源文件
        self.bundles = []  # bundle文件列表
        self.ide_target = {}  # ide相关的资源copy目录


class CMakeScriptTaskInfo:
    """
    用来执行 tmake.proj 中自定义的方法，该方法可以在一个 target 编译前，链接前和编译后三个时机执行
    """

    def __init__(self, module, cond, function_and_list):
        """
        :param module: cxx_module
        :param function_and_list: list类型，第一个元素是方法对象，其余的是参数
        """
        self.cond = cond
        if cond not in core.SCRIPT_TYPE_LIST:
            raise core.TmakeException(
                "tasks'key just can be {} for module {}".format(", ".join(core.SCRIPT_TYPE_LIST),
                                                                module.name))
        if not function_and_list:
            raise core.TmakeException("Value can not be empty for key %s in module %s" % (cond, module.name))
        # check function
        function = function_and_list[0]
        if not callable(function):
            raise core.TmakeException(
                "%s is type of %s, is not callable for tmake_script_task" % (function.__name__, type(function)))

        self.function = function
        self.arguments = function_and_list[1:]

    def execute(self):
        exec_string = 'self.function('
        arguments_length = len(self.arguments)
        for i in range(arguments_length):
            exec_string += 'self.arguments[' + str(i)
            if i == (arguments_length - 1):  # if last item
                exec_string += ']'
            else:
                exec_string += '], '
        exec_string += ')'
        # invoke
        exec exec_string
        core.v('function is {} , args is {} , invoke success'.format(self.function.__name__, self.arguments))


class CMakeTaskInfo(object):
    def __init__(self):
        self.name = ""
        self.config = ""
        self.work_directory = ""
        self.command = ""
        self.args = ""


class CMakeModuleInfo(object):
    """cmake module info class"""

    def __init__(self):
        self.link_style = ""  # STATIC | SHARED | MODULE |WIN32 | MACOSX_BUNDLE
        self.exclude_from_all = ""
        self.name = ""
        self.version = ""
        self.publish = None
        self.defines = []
        self.properties = {}  # SET_TARGET_PROPERTIES(ackor_base PROPERTIES OUTPUT_NAME "ackor_base_s")这种形式使用
        self.framework_properties = {}  # 生成framework需要的属性
        self.include_dirs = []
        self.lib_dirs = []
        self.link_libs = []
        self.link_all_symbol_libs = []  # 用于标记需要全部链接的库
        self.un_relink_deps = []  # 不递归依赖哪些库
        self.deps = []  # 存储的是链接的名字
        self.publish_info = {}
        self.origin_deps = []  # 发布时候用
        self.srcs = []
        self.headers = []
        self.exported_headers = []
        self.exported_headers_by_folder = {}
        self.c_flags = ""
        self.cxx_flags = ""
        self.linker_flags = ""
        self.frameworks = []
        self.plist = ""
        self.pre_cmake_command = ""
        self.post_cmake_command = ""
        self.tasks = {}
        self.xctest_unit_src = []
        self.package_dynamic_lib = []
        self.add_to_zip = {}

        # app专用
        self.app_icon = None
        self.launch_image = None
        # QT 工程专用
        self.qt_project = False  # 是否是QT工程项目
        self.qt_components = []  # 使用到的QT组件
        self.qt_ui = []  # 对应的ui 文件列表
        self.qt_moc_headers = []  # 对应需要moc的头文件

    def __str__(self):
        return "name = {}, version={}, link_style={}".format(self.name, self.version, self.link_style)

class CMakeExternalModuleInfo(object):
    """cmake external module info class"""

    def __init__(self):
        self.name = ""
        self.version = ""
        self.publish = None
        self.path = ""


    def __str__(self):
        return "name = {}, version={}, path={}".format(self.name, self.version, self.path)


class CMakeProjectInfo(object):
    """cmake project info class"""

    def __init__(self):
        self.path_info = None
        self.project_name = ""
        self.build_target = ""
        self.is_project_cmd = "project" == core.data.arguments.tmake_cmd()
        self.is_publish_cmd = "publish" == core.data.arguments.tmake_cmd()
        self.build_config = ""
        self.mini_version = ""
        self.xcode_properties = {}
        self.global_include_dirs = []
        self.global_lib_dirs = []
        self.global_defines = []
        self.global_c_flags = ""
        self.global_cxx_flags = ""
        self.global_linker_flags = ""  # 该参数目前不支持 tmake.proj 全局中配置，只支持通过-FL传递
        self.libraries = []
        self.binaries = []
        self.tasks = []
        self.build_vars = {}
        self.apps = []
        self.resources = []
        self.external_builds = []

        self.cmake_command = ""
        self.cmake_arguments = []
        self.cmake_command_default = ""

        self.platform_deps_key = core.data.target + "_deps"

    def parse(self, project, path_info):
        """
        将项目的属性对应到CMakeProjectInfo上
        :param project:
        :return:
        """
        self.path_info = path_info
        if project.project_name():
            self.project_name = project.project_name()
        else:
            self.project_name = "proj"
        self.build_target = project.target
        self.build_config = project.build_config
        self.mini_version = core.MIN_CMAKE_VERSION

        # project里的全局信息转换到对象里
        if project.global_config:
            self.__set_global_info_by_project(project)

        # 通过-M -F等传递的参数给设置上
        self.set_global_flag_by_cmd()

        # 更新libraries的依赖信息
        for name in project.libraries:
            self.__update_deps(project.libraries[name])

        # 分别设置libraries、binaries、apps
        for name in project.libraries:
            info = CMakeModuleInfo()
            self.__copy_project_attr_to_module(info, project.libraries[name], project)
            self.libraries.append(info)

        for name in project.binaries:
            info = CMakeModuleInfo()
            self.__copy_project_attr_to_module(info, project.binaries[name], project)
            self.binaries.append(info)

        for name in project.apps:
            info = CMakeModuleInfo()
            self.__copy_project_attr_to_module(info, project.apps[name], project)
            self.apps.append(info)

        for name in project.tasks:
            info = CMakeTaskInfo()
            self.__copy_project_attr_to_task(info, project.tasks[name])
            self.tasks.append(info)

        for res in project.resources:
            res_info = CMakeResourceInfo()
            res_info.name = res
            res_dict = project.resources[res]
            for item in res_dict:
                if hasattr(res_info, item) and res_dict[item]:
                    setattr(res_info, item, res_dict[item])
            self.resources.append(res_info)

        for name in project.external_builds:
            info = CMakeExternalModuleInfo()
            self.__copy_project_attr_to_external_module(info, project.external_builds[name])
            self.external_builds.append(info)

        # 已经把global的信息设置到单个模块上了，这里清空掉
        self.global_include_dirs = []
        self.global_lib_dirs = []
        self.global_defines = []
        self.global_c_flags = ""
        self.global_cxx_flags = ""

    def set_global_flag_by_cmd(self):
        # 命令行中-M形式传递的宏参数也设置上
        cmd_defines = core.data.arguments.get_opts_by_prefix("-M")
        if cmd_defines:
            self.global_defines += cmd_defines
        core.v("defines in cmd:{}".format(self.global_defines))
        settings = core.data.arguments.get_opts_by_prefix("-F")
        c_flags = ""
        cxx_flags = ""
        linker_flags = ""
        for setting in settings:
            if "=" not in setting:
                continue
            type = setting[:setting.find("=")]
            value = setting[setting.find("=") + 1:]
            if type == "c_flags":
                c_flags += " {} ".format(value)
            if type == "cxx_flags":
                cxx_flags += " {} ".format(value)
            if type == "linker_flags":
                linker_flags += " {} ".format(value)
        core.v("flag in cmd:{} {} {}".format(c_flags, cxx_flags, linker_flags))
        if c_flags:
            self.global_c_flags += c_flags
        if cxx_flags:
            self.global_cxx_flags += cxx_flags
        if linker_flags:
            self.global_linker_flags += linker_flags

    def __set_global_info_by_project(self, project):
        """
        数组类型的用+=，防止修改原来的
        字典类型的用update方法合并
        :param project:
        :return:
        """
        if project.global_config["c_flags"]:
            self.global_c_flags = project.global_config["c_flags"]
        if project.global_config["cxx_flags"]:
            self.global_cxx_flags = project.global_config["cxx_flags"]
        if project.global_config["defines"]:
            self.global_defines += project.global_config["defines"]
        if project.global_config["include_dirs"]:
            self.global_include_dirs += project.global_config["include_dirs"]
        if project.global_config["lib_dirs"]:
            self.global_lib_dirs += project.global_config["lib_dirs"]
        if project.global_config["xcode_properties"]:
            self.xcode_properties.update(project.global_config["xcode_properties"])
        if project.global_config["cmake_command"]:
            self.cmake_command = project.global_config["cmake_command"]
        if project.global_config["build_vars"]:
            self.build_vars.update(project.global_config["build_vars"])

    def __update_deps(self, library):
        """
        编译完一个项目后，把项目里的library更新到全局依赖里
        :param library:
        :return:
        """
        library_dir = self.path_info.build_installed_path
        library_dirs = [library_dir]
        library_dirs.extend(tmake_utils.fix_path_to_abs(self.global_lib_dirs))
        if library["lib_dirs"]:
            library_dirs.extend(tmake_utils.fix_path_to_abs(library["lib_dirs"]))
        include_dirs = []
        # exported_headers 也放入include_headers里，有的项目只配置了exported_headers
        # 过滤下不是文件夹的，不然如果是文件类型的编译会报警告
        # 只有导出的头文件其他项目才可以使用，如果导出头文件配置了文件类型的话，设置local_export文件夹
        des_dir = self.path_info.get_local_export_include_path(library["name"])
        if library["exported_headers"]:
            headers_folder = tmake_utils.fix_path_to_abs(library["exported_headers"])
            # 清空一下，使用中发现不清可能出现不对的头文件
            tmake_utils.clean(des_dir)
            # 如果是project直接添加，如果是build要复制到local_export里，用那里面的路径
            if self.is_project_cmd:
                for path in headers_folder:
                    if os.path.isdir(path):
                        include_dirs.append(path)
                    else:
                        include_dirs.append(os.path.dirname(path))
            else:
                if not os.path.exists(des_dir):
                    os.makedirs(des_dir)
                include_dirs.append(des_dir)
                for path in headers_folder:
                    if not os.path.exists(path):
                        continue
                    # 因外部输入参数错误，可能导致拷贝根目录，这是不允许的
                    if path == '/':
                        core.e("Cannot copy the root directory, please check exported_headers!")
                        continue
                    if os.path.isdir(path):
                        tmake_utils.copytree(path, des_dir, ignoreHide=True)
                        sub_folder = os.listdir(path)
                        for item in sub_folder:
                            full_path = os.path.join(des_dir, item)
                            if os.path.isdir(full_path):
                                include_dirs.append(full_path)
                    else:
                        import shutil
                        shutil.copy(path, os.path.join(des_dir, os.path.basename(path)))

        if library["exported_headers_by_folder"]:
            tmake_utils.move_files_to_target(des_dir, library["exported_headers_by_folder"])
        # 把导出的c及cpp文件删除一下
        from core.info.tmake_builtin import tmake_glob
        exclude_list = tmake_glob(des_dir, "*.c", True)
        exclude_list += tmake_glob(des_dir, "*.cpp", True)
        print exclude_list
        for item in exclude_list:
            tmake_utils.clean(item)
        core.data.deps_mgr.update_dep_module_lib_dir(library["name"],
                                                      library_dirs,
                                                      include_dirs)

    def __copy_project_attr_to_module(self, info, module, project):
        if "frameworks" in module and module["frameworks"]:
            info.frameworks += module["frameworks"]
        if "plist" in module and module["plist"]:
            info.plist += module["plist"]
        if module["defines"]:
            info.defines += module["defines"]
        if module["include_dirs"]:
            info.include_dirs += module["include_dirs"]
        if module["lib_dirs"]:
            info.lib_dirs += module["lib_dirs"]
        if module["link_libs"]:
            info.link_libs += module["link_libs"]
        if "link_all_symbol_libs" in module and module["link_all_symbol_libs"]:
            info.link_all_symbol_libs += module["link_all_symbol_libs"]
        if "un_relink_deps" in module and module["un_relink_deps"]:
            info.un_relink_deps += module["un_relink_deps"]
        if module["properties"]:
            info.properties = module["properties"]
        if "framework_properties" in module and module["framework_properties"]:
            info.framework_properties = module["framework_properties"]
        if module["srcs"]:
            info.srcs += module["srcs"]
        if module["headers"]:
            info.headers += module["headers"]
        if "exported_headers" in module and module["exported_headers"]:
            info.exported_headers += module["exported_headers"]
        if "exported_headers_by_folder" in module and module["exported_headers_by_folder"]:
            info.exported_headers_by_folder = module["exported_headers_by_folder"]
        if "publish" in module:
            info.publish = module["publish"]
        if "publish_info" in module and module["publish_info"]:
            info.publish_info = module["publish_info"]
        if module["c_flags"]:
            info.c_flags = module["c_flags"]
        if module["cxx_flags"]:
            info.cxx_flags = module["cxx_flags"]
        if module["linker_flags"]:
            info.linker_flags = module["linker_flags"]
        if "version" in module and module["version"]:
            info.version = module["version"]
        if module["pre_cmake_command"]:
            info.pre_cmake_command = module["pre_cmake_command"]
        if module["post_cmake_command"]:
            info.post_cmake_command = module["post_cmake_command"]
        if module["xctest_unit_src"]:
            info.xctest_unit_src = module["xctest_unit_src"]
        if "package_dynamic_lib" in module and module["package_dynamic_lib"]:
            info.package_dynamic_lib = module["package_dynamic_lib"]
        if "add_to_zip" in module and module["add_to_zip"]:
            info.add_to_zip = module["add_to_zip"]
        attr_list = ["launch_image", "app_icon", "qt_project", "qt_components", "qt_ui", "qt_moc_headers"]
        for attr in attr_list:
            if attr in module and module[attr]:
                setattr(info, attr, module[attr])
        if module["tasks"]:
            for (cond, function_and_arguments) in module["tasks"].items():
                info.tasks[cond] = CMakeScriptTaskInfo(self, cond, function_and_arguments)
        info.name = module["name"]
        # 将global的添加上
        info.include_dirs += self.global_include_dirs
        info.lib_dirs += self.global_lib_dirs
        info.defines += self.global_defines
        if self.global_c_flags:
            info.c_flags += " " + self.global_c_flags
        if self.global_cxx_flags:
            info.cxx_flags += " " + self.global_cxx_flags
        if self.global_linker_flags:
            info.linker_flags += " " + self.global_linker_flags
        # exported_headers合并到include_dirs里
        headers_folder = tmake_utils.fix_path_to_abs(info.exported_headers)
        for path in headers_folder:
            if os.path.isdir(path):
                info.include_dirs.append(path)
        if module["deps"]:
            deps = module["deps"]
            deps = tmake_utils.reset_deps(deps)
            for key in deps:
                info.origin_deps.append(key)
                info.deps.extend(core.data.deps_mgr.get_module_deps_lib(key, info.un_relink_deps))
                info.lib_dirs.extend(core.data.deps_mgr.get_module_deps_lib_dir(key))
                info.include_dirs.extend(core.data.deps_mgr.get_module_deps_include(key))
        # 添加deps
        index = 0
        for lib in info.link_libs:
            lib = lib.replace("\\", "/")
            lib_name = lib[lib.rfind('/')+1:]
            suffix = os.path.splitext(lib_name)[1]
            original_name = lib_name
            if suffix:
                original_name = lib_name.replace(suffix, "", 1)
            original_name = original_name.replace("lib", "", 1)
            for name in project.external_builds:
                if original_name == name:
                    if core.data.arguments.tmake_cmd() == "project":
                        path_info = PathInfo(core.data.arch, core.data.arguments.work_path())
                        base_path = os.path.join(path_info.project_path, abcoretor.BUILD_OUTPUT_NAME)
                        lib_path = os.path.join(base_path, name, core.data.build_config, lib_name)
                        lib_path = lib_path.replace("\\", "/")
                    else:
                        base_path = os.path.join(core.data.project.get_build_folder(core.data.arch), core.BUILD_OUTPUT_NAME)
                        lib_path = os.path.join(base_path, name, lib_name)
                        lib_path = lib_path.replace("\\", "/")
                    info.link_libs[index] = lib_path
            index += 1
        info.deps.extend(info.link_libs)
        # 平台的依赖放到最后
        if self.platform_deps_key in module and module[self.platform_deps_key]:
            info.deps.extend(module[self.platform_deps_key])
        # 对link_style进行特殊处理
        if "link_style" in module and module["link_style"]:
            info.link_style = module["link_style"].upper()
        if "DYNAMIC" == info.link_style:
            info.link_style = core.CXX_LIBRARY_LINK_STYLE_SHARED

    def __copy_project_attr_to_external_module(self, info, module):
        if "publish" in module:
            info.publish = module["publish"]
        if "version" in module and module["version"]:
            info.version = module["version"]
        if module["path"]:
            info.path = module["path"]
        if "name" in module:
            info.name = module["name"]

    def __str__(self):
        info = "cmake:\n"
        info += "    name:{}\n".format(self.project_name)
        info += "    target:{}\n".format(self.build_target)
        info += "    build config:{}\n".format(self.build_config)
        return info

    def __copy_project_attr_to_task(self, info, module):
        if module["name"]:
            info.name = module["name"]
        if module["config"]:
            info.config = module["config"]
        if module["work_directory"]:
            info.work_directory = module["work_directory"]
        if module["command"]:
            info.command = module["command"]
        if module["args"]:
            info.args = module["args"]
