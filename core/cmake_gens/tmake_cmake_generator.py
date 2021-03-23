#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
cmake generator file
调试宝典：
1、修改 cmake_helper.py， 注释掉 core.write_entire_file，直接修改原来的CMakeLists.txt查看效果。
2、https://cmake.org/cmake/help/v3.5/prop_tgt/RESOURCE.html 在cmake官网搜索可用的方式。
"""
import os
import subprocess

import core

from core import PlatformInfo
from core.info.tmake_builtin import tmake_path, tmake_glob
from core.info.tmake_path_info import PathInfo
from core.utils import tmake_utils

from multiprocessing import cpu_count

from core.utils import tmake_process_utils as process_utils

from .tmake_cmakelists import recover_cmakelists, copy_bin_to_export, move_header_files, arrange_dir, \
    delete_empty_dir, copy_libs_to_export, change_cmakelists_output

# format info:: 0:name, 1:cmake_min_version, 2:bin, 3:export, 4:target, 5:build_config
CMAKE_HEADER_TEMPLATE = """
PROJECT({0})

include(CheckIncludeFileCXX)

CMAKE_MINIMUM_REQUIRED(VERSION {1})

{6}

SET(EXECUTABLE_OUTPUT_PATH ${{PROJECT_BINARY_DIR}}/{2})
SET(LIBRARY_OUTPUT_PATH ${{PROJECT_BINARY_DIR}}/{2})
SET(CMAKE_INSTALL_PREFIX ${{PROJECT_BINARY_DIR}}/{3})

enable_language(ASM)
set(can_use_assembler TRUE)

SET(BUILD_TARGET {4})
SET(BUILD_CONFIG {5})
"""

CMAKE_CACHE_TEMPLATE = """
set(CCACHE_PROGRAM "{0}")
if(CCACHE_PROGRAM)
    set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE "${{CCACHE_PROGRAM}}")
endif()

if(CCACHE_PROGRAM)
    get_property(RULE_LAUNCH_COMPILE GLOBAL PROPERTY RULE_LAUNCH_COMPILE)
    if(RULE_LAUNCH_COMPILE AND CMAKE_GENERATOR STREQUAL "Xcode")
        # Set up wrapper scripts
        configure_file({1}/tools/launch-c.in launch-c)
        configure_file({2}/tools/launch-cxx.in launch-cxx)
        execute_process(COMMAND chmod a+rx
                                 "${{CMAKE_BINARY_DIR}}/launch-c"
                                 "${{CMAKE_BINARY_DIR}}/launch-cxx"
        )

        # Set Xcode project attributes to route compilation and linking
        # through our scripts
        set(CMAKE_XCODE_ATTRIBUTE_CC         "${{CMAKE_BINARY_DIR}}/launch-c")
        set(CMAKE_XCODE_ATTRIBUTE_CXX        "${{CMAKE_BINARY_DIR}}/launch-cxx")
        set(CMAKE_XCODE_ATTRIBUTE_LD         "${{CMAKE_BINARY_DIR}}/launch-c")
        set(CMAKE_XCODE_ATTRIBUTE_LDPLUSPLUS "${{CMAKE_BINARY_DIR}}/launch-cxx")
    endif()
endif()
"""

# format info:: 0:global_include, 1:global_link_dir, 2:global_definitions, 3:global_c_flags, 4:global_cxx_flags, 5:global_custom
CMAKE_GLOBAL_TEMPLATE = """
ADD_DEFINITIONS(-DTMAKE=1  -D_TMAKE_BUILD_TARGET_EXISTS -D_TMAKE_BUILD_TARGET_${{BUILD_TARGET}} -DTMAKE_${{BUILD_TARGET}} -DTMAKE_${{BUILD_CONFIG}} -D${{BUILD_CONFIG}}=1)
INCLUDE_DIRECTORIES({0})
LINK_DIRECTORIES({1})
ADD_DEFINITIONS({2})

SET(CMAKE_C_FLAGS " ${{CMAKE_C_FLAGS}} {3}")
SET(CMAKE_CXX_FLAGS " ${{CMAKE_CXX_FLAGS}} {4}")
{5}
IF (BUILD_TARGET MATCHES "IOS")
    SET(CMAKE_MACOSX_BUNDLE YES)
    SET(CMAKE_XCODE_ATTRIBUTE_CODE_SIGNING_REQUIRED "NO")
ENDIF()

"""

CMAKE_MODULE_PRE_BUILD_TEMPLATE = """
ADD_CUSTOM_TARGET({0}
   COMMAND {1}
)
ADD_DEPENDENCIES({2} {0})
"""

CMAKE_MODULE_PRE_LINK_OR_POST_BUILD_TEMPLATE = """
ADD_CUSTOM_COMMAND(TARGET {0}
 {1}
 COMMAND {2}
)
"""
SCRIPT_PRE_BUILD = "pre_build"
SCRIPT_PRE_LINK = "pre_link"
SCRIPT_POST_BUILD = "post_build"
SCRIPT_TYPE_LIST = [SCRIPT_PRE_BUILD, SCRIPT_PRE_LINK, SCRIPT_POST_BUILD]

CMAKE_QT_MODULE_TEMPLATE = """set(CMAKE_INCLUDE_CURRENT_DIR ON)
find_package(Qt5 REQUIRED COMPONENTS {0})

set(CMAKE_AUTOMOC ON)
"""

CMAKE_MODULE_ADD_RES_TEMPLATE = """
set(RESOURCE_FILES_{}
  {}
)

set_target_properties({} PROPERTIES
  MACOSX_BUNDLE TRUE
  RESOURCE "${{RESOURCE_FILES_{}}}"
)
"""

class CMakeSourceItem(object):
    def __init__(self):
        self.flat_path = ""
        self.paths = []


class CMakeGenerator(object):
    """cmake generator base class"""

    def __init__(self, arch):
        self.arch = arch
        self.path = PathInfo(arch, core.data.current_project.folder)
        self.info = core.CMakeProjectInfo()
        self.info.parse(core.data.current_project, self.path)
        self.cmake_text = ""
        self.cmake_home = tmake_utils.get_cmake_prog()

        self.resources = {}

    def generate(self):
        """
        生成CMakeList内容，存放到self.cmake_text
        """
        if core.data.use_cmakelist:
            self.create_build_vars()
            return

        self.__generate_header()
        self.__generate_global()

        if self.info.cmake_command:
            self.cmake_text += self.info.cmake_command + core.LINESEP + core.LINESEP
        elif self.info.cmake_command_default:
            self.info.cmake_command += " " + self.info.cmake_command_default
            self.cmake_text += self.info.cmake_command + core.LINESEP + core.LINESEP

        for res in self.info.resources:
            self.__generate_resource(res)

        for binary in self.info.binaries:
            self.__generate_module(binary)

        for module in self.info.libraries:
            self.__generate_module(module)

        for app in self.info.apps:
            if self.info.build_target == core.PLATFORM_ANDROID:
                app.link_style = core.CXX_LIBRARY_LINK_STYLE_SHARED
            self.__generate_module(app)

        for external_build in self.info.external_builds:
            self.__generate_external_build(external_build)

        self.create_build_vars()

    def __generate_header(self):
        """
        create CmakeLists.txt's header
        :return: info
        """
        # 设置ccache缓存相关内容
        cache_path = ""
        use_cache = not core.data.arguments.has_opt("--no_cache") and not PlatformInfo.is_windows_system()
        if use_cache:
            cache_result = process_utils.execute_with_msg("which ccache")
            if cache_result:
                cache_list = cache_result.split("\n")
                if os.path.exists(cache_list[0]):
                    cache_path = cache_list[0]
                else:
                    use_cache = False
            else:
                use_cache = False
            if not use_cache:
                core.i("enable ccache, but ccache not install!!!")
        tmake_path = core.data.arguments.tmake_path()
        self.cmake_text += CMAKE_HEADER_TEMPLATE.format(
            self.info.project_name,
            self.info.mini_version,
            core.BUILD_OUTPUT_NAME,  # bin
            core.BUILD_INSTALL_PREFIX,  # export
            self.info.build_target.upper(),
            self.info.build_config.upper(),
            CMAKE_CACHE_TEMPLATE.format(cache_path, tmake_path, tmake_path) if use_cache else ""
        )

    def __generate_global(self):
        """
        create CmakeLists.txt's global part
        :return: info
        """
        common_text = self.generate_global_common()

        self.info.global_c_flags += core.data.current_project.get_feature_headers_flags()
        self.info.global_cxx_flags += core.data.current_project.get_feature_headers_flags()

        self.cmake_text += CMAKE_GLOBAL_TEMPLATE.format(
            tmake_utils.flat_path_list(self.info.global_include_dirs),
            tmake_utils.flat_path_list(self.info.global_lib_dirs),
            tmake_utils.flat_cxx_defines(self.info.global_defines, True),
            self.info.global_c_flags,
            self.info.global_cxx_flags,
            common_text
        )

        # mac/ios可能需要设置xcode属性
        if self.info.build_target in [core.PLATFORM_MAC, core.PLATFORM_IOS]:
            # 提供xcode_properties设置xcode属性
            self.info.xcode_properties.update({"GCC_WARN_ABOUT_RETURN_TYPE":"YES_ERROR"})
            for key, value in self.info.xcode_properties.items():
                self.cmake_text += 'set(CMAKE_XCODE_ATTRIBUTE_{} "{}")\n'.format(key.upper(), value)

    def __generate_resource(self, resource):
        """
        生成资源信息
        :param resource:
        :return:
        """
        source_list = []
        # 设置资源
        for key, value in resource.files.items():
            source_list += value
        # 设置bundle，bundle建立软连接
        clean_bundle = False
        for bundle in resource.bundles:
            bundle_path = tmake_path(bundle)
            # windows 系统不做链接处理
            if PlatformInfo.is_windows_system() or ".xcassets" in bundle_path:
                source_list.append(bundle_path)
            else:
                bundle_name = os.path.basename(bundle_path)
                if not bundle_name.endswith(".bundle"):
                    bundle_name = "{}.bundle".format(bundle_name)
                link_folder = os.path.join(self.path.project_path if self.info.is_project_cmd else self.path.build_path,
                                           "bundle")
                if not os.path.exists(link_folder):
                    os.mkdir(link_folder)
                link_path = os.path.join(link_folder, bundle_name)
                if os.path.exists(link_path) and not clean_bundle:
                    tmake_utils.reset_dir_path(link_path)
                clean_bundle = True
                tmake_utils.copyFiles(tmake_path(bundle), link_path)
                #tmake_utils.set_symlink(tmake_path(bundle), link_path)
                source_list.append(link_path)
        if source_list:
            res = tmake_utils.flat_path_list(tmake_utils.fix_path_to_abs(set(source_list)))
        else:
            res = ""
        item = CMakeSourceItem()
        item.flat_path = res
        item.paths = tmake_utils.fix_path_to_abs(set(source_list))
        self.resources[resource.name] = item

    def __generate_module(self, module):
        """
        create CmakeLists.txt's one of every module
        :return: info
        """
        module_info = ""
        # QT工程独有CmakeList配置
        if module.qt_project:
            module_info += self.__generate_module_qt(module)
        tmp_module_info = self.generate_module_common(module)

        module_info += self.__generate_module_link_dir(module)
        module_info += self.__generate_module_srcs(module)
        module_info += self.__generate_module_properties(module)
        module_info += self.__generate_module_include(module)
        module_info += self.__generate_module_link_lib(module)
        module_info += self.__generate_module_install(module)
        module_info += self.__generate_module_link_flags(module)
        module_info += self.__generate_module_defines(module)
        module_info += self.__generate_module_script_tasks(module)
        module_info += module.pre_cmake_command + core.LINESEP
        module_info += module.post_cmake_command + core.LINESEP
        module_info += tmp_module_info

        # mac/ios可能需要设置xctest属性
        if self.info.build_target in [core.PLATFORM_MAC, core.PLATFORM_IOS]:
            module_info += self.__generate_module_xctest(module)

        self.cmake_text += module_info

    def __generate_external_build(self, module):
        """
        create CmakeLists.txt's one of every module
        :return: info
        """
        module_info = ""
        module_info += "ADD_SUBDIRECTORY({} {})".format(module.path, module.path) + core.LINESEP
        self.cmake_text += module_info

        if core.data.arguments.tmake_cmd() == "project":
            path_info = PathInfo(self.arch, core.data.arguments.work_path())
            base_path = path_info.project_path
        else:
            base_path = core.data.project.get_build_folder(self.arch)
        export_path = os.path.join(base_path, core.BUILD_INSTALL_PREFIX, module.name)
        exectable_output_path = os.path.join(base_path, core.BUILD_OUTPUT_NAME, module.name)
        library_output_path = os.path.join(base_path, core.BUILD_OUTPUT_NAME, module.name)
        export_path = export_path.replace("\\", "/")
        exectable_output_path = exectable_output_path.replace("\\", "/")
        library_output_path = library_output_path.replace("\\", "/")
        recover_cmakelists(module.path)
        change_cmakelists_output(module.path, export_path, exectable_output_path,
                                 library_output_path)

    def __generate_module_qt(self, module):
        qt_components = " ".join(module.qt_components)
        qt_ui = tmake_utils.flat_path_list(module.qt_ui)
        qt_moc_headers = tmake_utils.flat_path_list(module.qt_moc_headers)
        ret_str = CMAKE_QT_MODULE_TEMPLATE.format(qt_components, module.name, qt_moc_headers, qt_ui)
        return ret_str

    def __generate_module_link_flags(self, module):
        """
        生成 CMAKE_EXE_LINKER_FLAGS
        :param module:
        :return:
        """
        link_flags_key = "CMAKE_EXE_LINKER_FLAGS"
        if module.link_style == core.CXX_LIBRARY_LINK_STYLE_SHARED:
            link_flags_key = "CMAKE_SHARED_LINKER_FLAGS"
        elif module.link_style == core.CXX_LIBRARY_LINK_STYLE_STATIC:
            link_flags_key = "CMAKE_STATIC_LINKER_FLAGS"
        info = ""
        # 目前只给android的so类型添加、非project命令 添加特定的linker_flags，这样有未找到的符号编译so不通过
        if module.link_style == core.CXX_LIBRARY_LINK_STYLE_SHARED \
                and self.info.build_target == core.PLATFORM_ANDROID \
                and not self.info.is_project_cmd:
            module.linker_flags = " -Wl,--no-undefined " + module.linker_flags
            module.linker_flags += self.info.global_linker_flags
        # 针对动态库，如果使能linkmap，则增加Map flag
        if core.data.arguments.has_opt("--link_map") \
                and module.link_style == core.CXX_LIBRARY_LINK_STYLE_SHARED:
                    if PlatformInfo.is_windows_system():
                        windows_flag = '\"${CMAKE_SHARED_LINKER_FLAGS}'
                        info += 'set(CMAKE_SHARED_LINKER_FLAGS {} /MAP:{}.map\") {}'.format(windows_flag, module.name, core.LINESEP)
                    else:
                        module.linker_flags += '-Wl,-Map,{}.map'.format(module.name)
        # ios的 framework 默认添加下面的flags，为了一些依赖不打入库中也不报符号找不到错误。
        if module.link_style == core.CXX_LIBRARY_LINK_STYLE_FRAMEWORK \
                and self.info.build_target == core.PLATFORM_IOS:
            module.linker_flags += " -all_load -undefined dynamic_lookup "
        if module.linker_flags:
            # info += "SET({} \"${{{}}} {}\"){}" \
            #     .format(link_flags_key, link_flags_key, module.linker_flags, core.LINESEP)
            # 下个版本再升级的功能，用于给每个模块指定不同的link_flags
            info += "SET_TARGET_PROPERTIES({} PROPERTIES LINK_FLAGS \"{}\"){}".format(module.name,
                                                                                      module.linker_flags,
                                                                                      core.LINESEP)
        return info

    def __generate_module_defines(self, module):
        """
        生成 TARGET_COMPILE_DEFINITIONS
        :param module:
        :return:
        """
        info = ""
        if module.defines:
            info += "TARGET_COMPILE_DEFINITIONS({} PRIVATE {}){}" \
                .format(module.name, ' '.join(module.defines),
                        core.LINESEP)
        return info

    def __generate_module_install(self, module):
        """
        生成 INSTALL
        :param module:
        :return:
        """
        return "INSTALL (TARGETS {} DESTINATION {}){}" \
            .format(module.name, core.BUILD_OUTPUT_NAME, core.LINESEP)

    def __generate_module_link_lib(self, module):
        """
        生成 TARGET_LINK_LIBRARIES
        :param module:
        :return:
        """
        framework_info = ""
        if core.data.target in [core.PLATFORM_IOS, core.PLATFORM_MAC] and module.frameworks:
            for item in module.frameworks:
                framework_info += " \"-framework " + item + "\" "
        info = ""
        dep_info = ""
        link_libs = []
        for item in module.deps:
            if module.link_all_symbol_libs and item in module.link_all_symbol_libs:
                if core.data.target in [core.PLATFORM_IOS, core.PLATFORM_MAC]:
                    link_libs.append("-force_load {}".format(item))
                else:
                    link_libs.append("-Wl,--whole-archive -l{} -Wl,--no-whole-archive".format(item))
            else:
                link_libs.append(item)
        if link_libs:
            dep_info += tmake_utils.order_flat_list(link_libs)
        if framework_info:
            dep_info += framework_info
        if dep_info:
            info += "TARGET_LINK_LIBRARIES({} {}){}" \
                .format(module.name,
                        dep_info,
                        core.LINESEP)
        for item in link_libs:
            lib_name = item.split('/')[-1]
            name = lib_name.split('.')[0]
            if name.startswith('lib'):
                name = name.replace('lib', '')
            for external_build in self.info.external_builds:
                if name == external_build.name:
                    info += "ADD_DEPENDENCIES({} {}){}" \
                        .format(module.name,
                                name,
                                core.LINESEP)

        return info

    def __generate_module_include(self, module):
        """
        生成 TARGET_INCLUDE_DIRECTORIES
        :param module:
        :return:
        """
        return "TARGET_INCLUDE_DIRECTORIES({} {} {}){}" \
            .format(module.name,
                    "PRIVATE",
                    tmake_utils.flat_path_list(tmake_utils.fix_path_to_abs(module.include_dirs)),
                    core.LINESEP)

    def __generate_module_properties(self, module):
        """
        生成 SET_TARGET_PROPERTIES信息
        :param module:
        :return:
        """
        result = ""
        if module.properties:
            info = ""
            for key in module.properties:
                info += key + " \"" + module.properties[key] + "\" "
            result = "SET_TARGET_PROPERTIES({} PROPERTIES {}){}".format(module.name, info, core.LINESEP)
        return result

    def __generate_module_srcs(self, module):
        """
        生成 ADD_EXECUTABLE/ADD_LIBRARY
        :param module:
        :return:
        """
        app_type = ''
        xctest_cmd = ''
        set_target_properties = ''
        if module.link_style in (core.CXX_LIBRARY_LINK_STYLE_STATIC, core.CXX_LIBRARY_LINK_STYLE_SHARED,
                                 "MODULE", core.CXX_LIBRARY_LINK_STYLE_FRAMEWORK):
            add_key = "ADD_LIBRARY"
            if self.info.build_target in [core.PLATFORM_MAC, core.PLATFORM_IOS]\
                and len(module.xctest_unit_src) != 0:
                set_target_properties = 'set_target_properties({} PROPERTIES FRAMEWORK TRUE)\n'\
                        .format(module.name)
        else:
            add_key = "ADD_EXECUTABLE"
            # if core.PLATFORM_WINDOWS == core.data.platform.get_host():
            #     app_type = 'WIN32'
            # else:
            #     app_type =''

            if self.info.build_target in [core.PLATFORM_MAC, core.PLATFORM_IOS]\
                and len(module.xctest_unit_src) != 0:
                xctest_cmd = 'MACOSX_BUNDLE'

        qt_ui = ""
        if module.qt_project:
            qt_ui = "${{{}_ui_wrapped}}".format(module.name)

        # 资源添加到src的最尾部
        res = ""
        if module.name in self.resources:
            res = self.resources[module.name].flat_path

        dep_headers = []
        if self.info.is_project_cmd:
            dep_headers = self.__module_deps_headers(module)
        library_style = module.link_style
        if module.link_style == core.CXX_LIBRARY_LINK_STYLE_FRAMEWORK:
            library_style = core.CXX_LIBRARY_LINK_STYLE_SHARED
        add_cmd =  "{}({} {} {} {} {} {} {} {}){}" \
            .format(add_key,
                    module.name,
                    xctest_cmd,
                    app_type,
                    library_style,
                    module.exclude_from_all,
                    tmake_utils.flat_path_list(
                        tmake_utils.fix_path_to_abs(set(module.srcs + module.headers + dep_headers))),
                    res, qt_ui,
                    core.LINESEP)
        return add_cmd + set_target_properties

    def __generate_module_xctest(self, module):
        """
        生成 xctest 相关配置
        :param module:
        :return:
        """
        if len(module.xctest_unit_src) != 0:
            enable = "enable_testing()\n"
            find_package = "find_package(XCTest REQUIRED)\n"

            xctest_module_name = module.name + "Tests"
            add_key = "xctest_add_bundle"
            xctest_unit_src = ''
            for src in module.xctest_unit_src:
                xctest_unit_src += src + '\n'
            bundle_out = "{}({} {}\n{}){}" \
                .format(add_key,
                        xctest_module_name,
                        module.name,
                        xctest_unit_src,
                        core.LINESEP)
            add_key = "xctest_add_test"
            test_out = "{}({}.{} {}){}" \
                .format(add_key,
                        self.info.project_name,
                        module.name,
                        xctest_module_name,
                        core.LINESEP)
            return enable + find_package + bundle_out + test_out
        else:
            return ''

    def __generate_module_link_dir(self, module):
        """
        生成 LINK_DIRECTORIES
        :param module:
        :return:
        """
        info = ""
        if module.lib_dirs:
            info += "LINK_DIRECTORIES({}){}" \
                .format(tmake_utils.flat_path_list(tmake_utils.fix_path_to_abs(module.lib_dirs)),
                        core.LINESEP)
        return info

    def generate_global_common(self):
        """
        子类选择重写，扩展global中的CMakeText内容
        :return:
        """
        return ""

    def generate_module_common(self, module):
        """
        针对每个module做的处理，子类可以重新实现针对不同module的具体逻辑
        :param module:
        :return:
        """
        cmake_text = ""
        if (self.info.is_project_cmd and core.PLATFORM_WINDOWS == core.data.platform.get_host()) or (
                "wince" in self.arch and core.PLATFORM_WINDOWS == core.data.platform.get_host()):
            # Visual Studio 不支持 $<COMPILE_LANGUAGE:C>
            # cmake 在 生成 Visual Studio 工程时， 只支持 CXX_FLAGS。 C_FLAGS会被忽略(c文件也是使用CXX_FLAGS)。
            if len(module.cxx_flags):
                cmake_text += "target_compile_options({} PRIVATE {}){}".format(module.name, module.cxx_flags,
                                                                               core.LINESEP)
                for src in module.srcs:
                    if src.endswith("stdafx.cpp"):
                        print(src)
                        cmake_text += core.LINESEP + "# Precompile Compile Header" + core.LINESEP
                        cmake_text += "target_compile_options({} PRIVATE /Yu){}".format(module.name, core.LINESEP)
                        cmake_text += "SET(PrecompiledBinary ${CMAKE_CURRENT_BINARY_DIR}/" + module.name + ".dir/${CMAKE_BUILD_TYPE}/" + module.name + ".pch)" + core.LINESEP
                        cmake_text += "SET_SOURCE_FILES_PROPERTIES(" + src + """ PROPERTIES COMPILE_FLAGS "/Yc\\"stdafx.h\\" /Fp\\"${PrecompiledBinary}\\"" OBJECT_OUTPUTS "${PrecompiledBinary}")""" + core.LINESEP + core.LINESEP
                        break
        else:
            if len(module.c_flags):
                cmake_text += "target_compile_options({} PRIVATE $<$<COMPILE_LANGUAGE:C>:{}>){}". \
                    format(module.name, module.c_flags, core.LINESEP)
            if len(module.cxx_flags):
                cmake_text += "target_compile_options({} PRIVATE $<$<COMPILE_LANGUAGE:CXX>:{}>){}". \
                    format(module.name, module.cxx_flags, core.LINESEP)

        # 如果有资源，则指定资源信息
        if module.name in self.resources:
            cmake_text += CMAKE_MODULE_ADD_RES_TEMPLATE.format(module.name,
                                                                     self.resources[module.name].flat_path,
                                                                     module.name, module.name)
        if self.info.is_project_cmd:
            dep_headers = self.__module_deps_headers(module)
            dep_dict = tmake_utils.build_source_group_by_list(dep_headers,
                                                             "Deps",
                                                             core.TMAKE_LIBRARIES_PATH)
            key_list = list(dep_dict.keys())
            tmake_utils.sort_versions(key_list)
            for key in key_list:
                cmake_text += "source_group(\"{}\" FILES {})\n".format(key, dep_dict[key])

            # 针对是否头文件和源文件分开做的处理
            is_together = core.data.arguments.has_opt("--together")
            header_dict = tmake_utils.build_source_group_by_list(module.headers,
                                                                "" if is_together else "Header Files",
                                                                self.path.project_folder)
            source_dict = tmake_utils.build_source_group_by_list(module.srcs,
                                                                "" if is_together else "Source Files",
                                                                self.path.project_folder)
            key_list = list(header_dict.keys() + source_dict.keys())
            tmake_utils.sort_versions(key_list)
            for key in key_list:
                if key in header_dict:
                    cmake_text += "source_group(\"{}\" FILES {})\n".format(key, header_dict[key])
                if key in source_dict:
                    cmake_text += "source_group(\"{}\" FILES {})\n".format(key, source_dict[key])
        return cmake_text

    def __module_deps_headers(self, module):
        """
        获取模块deps里的头文件信息
        :param module:
        :return:
        """
        dep_headers = []  # deps里的头文件
        for item in set(module.include_dirs):
            full_path = tmake_path(item)
            if full_path.startswith(core.TMAKE_LIBRARIES_PATH):
                temp_list = tmake_glob(full_path, ["*.h", "*.hpp"], True)
                dep_headers += temp_list
        return dep_headers

    def make_project(self, cmake_list_path, name):
        """
        call cmake project
        """

        if self.get_cmake_generator_name(name) == '':
            return

        target = core.data.target
        project_folder = self.path.project_path

        command_text = ""
        use_nmake = ""
        if PlatformInfo.is_windows_system():
            vs_tools = core.data.environment.get_vs_tool_path(self.arch)
            if target != core.PLATFORM_ANDROID and target != core.PLATFORM_WINDOWS:
                raise core.TmakeException('unsupported target : ' + target)
            command_text += '"' + vs_tools + '" '
            command_text += "&&"
        command_text += '"' + self.cmake_home + '" '
        command_text += '-H"' + cmake_list_path + '" '
        command_text += '-B"' + project_folder + '" '
        command_text += '-G"' + self.get_cmake_generator_name(name) + '" '
        command_text += use_nmake + self.__build_params()

        core.v(command_text)
        # tmake_utils.do_rm_build_bin_dir(tmake_utils.get_build_path(self.arch))
        # windows用false，其余的用true

        if core.data.use_cmakelist:
            if core.data.arguments.tmake_cmd() == "project":
                path_info = PathInfo(self.arch, core.data.arguments.work_path())
                base_path = path_info.project_path

            else:
                base_path = core.data.project.get_build_folder(self.arch)
            export_path = os.path.join(base_path, core.BUILD_INSTALL_PREFIX)
            exectable_output_path = os.path.join(base_path, core.BUILD_OUTPUT_NAME)
            library_output_path = os.path.join(base_path, core.BUILD_OUTPUT_NAME)

            # pre_command_text = '"' + self.cmake_home + '" ../../../../ ' + " -DCMAKE_INSTALL_PREFIX={}".format(export_path) + \
            #                                                 " -DEXECUTABLE_OUTPUT_PATH={}".format(exectable_output_path) + \
            #                                                 " -DLIBRARY_OUTPUT_PATH={}".format(library_output_path)
            #
            # pre_command_text = tmake_utils.get_cd_command() + " \"" + self.path.project_path + "\" && " + pre_command_text
            #
            # ret = core.subprocess.call(pre_command_text, shell=not PlatformInfo.is_windows_system())
            # if ret != 0:
            #     raise core.TmakeException('Set CMAKE_INSTALL_PREFIX failed! return code is {}'.format(ret))

        ret = subprocess.call(command_text, shell=not PlatformInfo.is_windows_system())
        if core.data.use_cmakelist:
            recover_cmakelists(self.path.project_folder)

        if core.data.use_proj_cmakelist:
            for external_build in self.info.external_builds:
                if external_build.path:
                    path = external_build.path
                    recover_cmakelists(path)

        if ret != 0:
            raise core.TmakeException('build failed! return code is {}'.format(ret))

    def get_cmake_generator_name(self, project_type):
        """
        根据要生成的项目类型确定-G参数的具体内容
        :param project_type:
        :return:
        """
        arc = ''
        if self.arch.lower().endswith(core.TARGET_CPU_X64):
            arc = ' Win64'
        if self.arch.lower().endswith(core.TARGET_CPU_WINCE_ARMV4I):
            arc = ' ' + core.WINCE_CPU_MAP[self.arch]
        if self.arch.lower().endswith(core.TARGET_CPU_WINCE_ARMV7):
            arc = ' ' + core.WINCE_CPU_MAP[self.arch]
        if self.arch.lower().endswith(core.TARGET_CPU_WINCE_CE6_ARMV4I):
            arc = ' ' + core.WINCE_CPU_MAP[self.arch]
        if project_type == 'vs2017':
            return 'Visual Studio 15 2017' + arc
        if project_type == 'vs2015':
            return 'Visual Studio 14 2015' + arc
        if project_type == 'vs2013':
            return 'Visual Studio 12 2013' + arc
        if project_type == 'vs2012':
            return 'Visual Studio 11 2012' + arc
        if project_type == 'vs2010':
            return 'Visual Studio 10 2010' + arc
        if project_type == 'vs2008':
            return 'Visual Studio 9 2008' + arc
        if project_type == 'xcode':
            return 'Xcode'
        if project_type == 'cdt4':
            return 'Eclipse CDT4 - Unix Makefiles'
        if project_type == 'blocks':
            return 'CodeBlocks - Unix Makefiles'
        return ''

    def __build_params(self):
        """
        通过遍历self.info.build_vars 拼接 -D类型参数
        :return:
        """
        command_text = ""
        self.info.build_vars["CMAKE_BUILD_TYPE"] = core.data.build_config.capitalize()
        for (key, value) in self.info.build_vars.items():
            command_text += ' -D' + key + '=' + value + ' '
        return command_text

    def __build_target(self):
        """
        生成MakeFile后执行的命令
        :return:
        """

        target = core.data.target
        command_text = ""

        if target == core.PLATFORM_WINDOWS:
            command_text += ' "' + self.cmake_home + '" --build . --target "install" '
            if not core.data.use_cmakelist:
                command_text += self.get_mp_build_string()
        elif target == core.PLATFORM_IOS:
            pro_name = os.path.join(self.path.build_path, self.info.project_name)
            command_text += " xcodebuild -project "
            command_text += pro_name
            command_text += '.xcodeproj -alltargets -configuration '
            command_text += self.info.build_config.capitalize()
        else:
            command_text += ' "' + self.cmake_home  +'" --build . --target "install/strip" '
            if not PlatformInfo.is_windows_system():
                command_text += self.get_mp_build_string()
        return command_text

    def get_mp_build_string(self):
        mp_args = ""
        if core.data.arguments.has_flag("nmp", "nmp"):
            return mp_args

        try:
            cpu_cnt = int(cpu_count() * 3 / 4)
        except:
            cpu_cnt = 0

        if cpu_cnt <= 0:
            cpu_cnt = 1

        mp_args = " -- -j {} ".format(cpu_cnt)
        core.i("mp_args = " + mp_args)
        return mp_args

    def run_build(self):
        """
        call cmake build
        """

        target = core.data.target
        command_text = ""
        use_nmake = ""
        if PlatformInfo.is_windows_system():
            vs_tools = core.data.environment.get_vs_tool_path(self.arch)
            if target != core.PLATFORM_ANDROID and target != core.PLATFORM_WINDOWS:
                raise core.TmakeException('unsupported target : ' + target)
            command_text += '"' + vs_tools + '" '
            command_text += "&&"
            if core.data.use_cmakelist:
                command_text += tmake_utils.get_cd_command() + " \"" + self.path.project_folder + "\" && "
            else:
                command_text += tmake_utils.get_cd_command() + " \"" + self.path.build_path + "\" && "
            if not core.data.arguments.has_flag("nmp",
                                                 "nmp") and target == core.PLATFORM_WINDOWS and not "wince" in self.arch\
                                                and not core.data.use_cmakelist:
                use_nmake = '-G "NMake Makefiles JOM" '
                jom_exe = os.path.join(core.data.arguments.tmake_path(), "tools", "jom.exe")
                use_nmake += ' -DCMAKE_MAKE_PROGRAM="' + jom_exe + '"'
                core.i("use_nmake = " + use_nmake)
            elif target == core.PLATFORM_WINDOWS and "wince" in self.arch:
                use_nmake = '-G "Visual Studio 9 2008 ' + core.WINCE_CPU_MAP[self.arch] + '"'
            else:
                use_nmake = '-G "NMake Makefiles" '
        if core.data.use_cmakelist:
            command_text += '"' + self.cmake_home + '" ../../../../ ' + use_nmake + self.__build_params()
        else:
            command_text += '"' + self.cmake_home + '" . ' + use_nmake + self.__build_params()
        command_text += "&&"
        command_text += self.__build_target()

        if target == core.PLATFORM_WINDOWS and "wince" in self.arch:
            configuration = ''
            if self.info.build_config == core.CONFIG_DEBUG:
                configuration = 'Debug'
            elif self.info.build_config == core.CONFIG_RELWITHDEBINFO:
                configuration = 'RelWithDebInfo'
            else:
                configuration = 'Release'
            command_text += "&&"
            command_text += 'msbuild.exe ' + self.info.project_name + ".sln " + '/t:ReBuild ' + '/p:Configuration=' + configuration + ' /p:Platform=' + '"' + \
                            core.WINCE_CPU_MAP[self.arch] + '"'
        if core.data.use_cmakelist and target != core.PLATFORM_WINDOWS:
            if core.data.arguments.tmake_cmd() == "project":
                path_info = PathInfo(self.arch, core.data.arguments.work_path())
                base_path = path_info.project_path

            else:
                base_path = core.data.project.get_build_folder(self.arch)
            export_path = os.path.join(base_path, core.BUILD_INSTALL_PREFIX)
            exectable_output_path = os.path.join(base_path, core.BUILD_OUTPUT_NAME)
            library_output_path = os.path.join(base_path, core.BUILD_OUTPUT_NAME)

            pre_command_text = '"' + self.cmake_home + '" ../../../../ ' + " -DCMAKE_INSTALL_PREFIX={}".format(export_path) + \
                                                           " -DEXECUTABLE_OUTPUT_PATH={}".format(exectable_output_path) + \
                                                           " -DLIBRARY_OUTPUT_PATH={}".format(library_output_path)  + \
                                                           use_nmake + self.__build_params()


            pre_command_text = tmake_utils.get_cd_command() + " \"" + self.path.build_path + "\" && " + pre_command_text
            ret = subprocess.call(pre_command_text, shell=True)
            if ret != 0:
                raise core.TmakeException('Set CMAKE_INSTALL_PREFIX failed! return code is {}'.format(ret))

        self.execute_build_command(command_text)

    def execute_build_command(self, command_text):
        """
        execute build command
        """
        command = tmake_utils.get_cd_command() + " \"" + self.path.build_path + "\" && " + command_text
        core.v(command)
        self.__do_rm_build_bin_dir()
        # shell=xx，windows的线上构建报错，不要修改为false
        #ret = core.subprocess.call(command, shell=True)
        ret = subprocess.call(command, shell=True)
        if ret != 0:
            raise core.TmakeException('build failed! return code is {}'.format(ret))
        if core.data.use_cmakelist or core.data.use_proj_cmakelist:
            if core.data.use_cmakelist:
                recover_cmakelists(self.path.project_folder)
            if core.data.arguments.tmake_cmd() == "project":
                src_dir = os.path.join(self.path.project_path, core.BUILD_OUTPUT_NAME)
            else:
                src_dir = os.path.join(self.path.build_path, core.BUILD_OUTPUT_NAME)
            # build folder
            arrange_dir(src_dir, src_dir)
            delete_empty_dir(src_dir)
            # export folder
            dst_dir = os.path.join(self.path.build_path, core.BUILD_INSTALL_PREFIX, core.BUILD_OUTPUT_NAME)
            copy_libs_to_export(src_dir, dst_dir)
            src_dir = os.path.join(self.path.build_path, core.BUILD_INSTALL_PREFIX)
            arrange_dir(src_dir, dst_dir)
            delete_empty_dir(src_dir)

        if core.data.use_proj_cmakelist:
            for external_build in self.info.external_builds:
                if external_build.path:
                    path = external_build.path
                    recover_cmakelists(path)


    def __do_rm_build_bin_dir(self):
        """
        清空输出路径
        :return:
        """
        rm_dirs = [os.path.join(self.path.build_path, "bin"), os.path.join(self.path.build_path, "export")]
        for dir in rm_dirs:
            core.v("do_rm_build_bin_dir: " + dir)
            if os.path.exists(dir):
                tmake_utils.rmtree(dir, True)

    def __generate_module_script_tasks(self, module):
        """
        生成cmake的脚本回调
        """
        cmake_text = ""
        for (cond, task) in module.tasks.items():
            fake_target = module.name + "_" + cond
            # 这里执行task的时候会多拼接上一遍，不过没影响，因为执行的task一般不进行build操作。
            arguments_info = core.data.arguments.clone(["task", module.name, cond, "-a", self.arch])
            arguments_str = ""
            for index, value in enumerate(arguments_info.argv):
                if index > 1:
                    arguments_str += " " + value
            command = "python {} {} {}".format(
                arguments_info.argv[0],
                arguments_info.argv[1],
                arguments_str)
            core.i(command)
            if cond == SCRIPT_PRE_BUILD:
                cmake_text += CMAKE_MODULE_PRE_BUILD_TEMPLATE.format(fake_target,
                                                                           command,
                                                                           module.name)
            else:
                cmake_text += CMAKE_MODULE_PRE_LINK_OR_POST_BUILD_TEMPLATE.format(module.name,
                                                                                        str.upper(cond),
                                                                                        command)
        return cmake_text

    def create_build_vars(self):
        """
        子类重写设置 self.info.build_vars
        :return:
        """
        pass
