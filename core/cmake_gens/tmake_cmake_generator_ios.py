#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""cmake generator ios file"""
import os
from collections import OrderedDict

import core
from core.utils import comm_utils

from .tmake_cmake_generator import CMakeGenerator

CMAKE_IOS_LIPO_TEMPLATE = """
PROJECT({0})
include(CheckIncludeFileCXX)
CMAKE_MINIMUM_REQUIRED(VERSION {1})
ADD_CUSTOM_TARGET(LIPO ALL)
"""

CMAKE_IOS_LIPO_MODULE_TEMPLATE = """
ADD_CUSTOM_TARGET({0}
    COMMAND lipo -create {1} {2} -output {3}
    {4}
)
"""

# ios的只有动态库才能作为framework https://cmake.org/cmake/help/v3.5/prop_tgt/FRAMEWORK.html
# version相关内容 https://cmake.org/cmake/help/v3.0/prop_tgt/MACOSX_FRAMEWORK_INFO_PLIST.html?highlight=macosx_framework_identifier
CMAKE_IOS_FRAMEWORK_PROPERTIES_TEMPLATE = """
set_target_properties({} PROPERTIES
  FRAMEWORK TRUE
  MACOSX_FRAMEWORK_BUNDLE_VERSION "{}"# 配置version
  MACOSX_FRAMEWORK_SHORT_VERSION_STRING "{}" # 配置 short version
  MACOSX_FRAMEWORK_IDENTIFIER {} # 配置bundle id
  {} # 配置info.list
  XCODE_ATTRIBUTE_CODE_SIGN_IDENTITY "iPhone Developer"
)
"""
XCODE_TARGET_PROPERTIES_TPL = """
set_target_properties({} PROPERTIES "{}" "{}")
"""


class CMakeGeneratorIOS(CMakeGenerator):
    """cmake generator cmake class for iOS"""

    def generate_global_common(self):
        if self.info.build_config == core.CONFIG_RELEASE:
            self.info.global_c_flags += " -O3 "
            self.info.global_cxx_flags += " -O3 "
            self.info.global_defines.append("NDEBUG")
        common_cmd = ""
        # iOS的真机类型去掉armv7s指令集的库 [armv7 i386 x86_64 arm64]
        self.info.global_defines.append("PLATFORM_IOS")
        if self.arch == core.TARGET_CPU_OS:
            common_cmd += '\nset(CMAKE_OSX_ARCHITECTURES "armv7;arm64")\n'
        return common_cmd

    def generate(self):
        #用于调换顺序
        remove_default_flags = core.data.current_project.remove_default_flags
        # xcode中显示的支持版本为7.0
        if remove_default_flags == False:
            self.cmake_text += "SET(CMAKE_XCODE_ATTRIBUTE_IPHONEOS_DEPLOYMENT_TARGET \"8.0\")\n"

        # FUSION类型的只是执行lipo命令
        if self.arch == core.TARGET_CPU_FUSION:
            self.generate_cmake_lipo_text()
        else:
            for app in self.info.apps:
                if app.plist:
                    from core.info.tmake_builtin import tmake_path
                    plist_path = tmake_path(app.plist)
                    app.properties["MACOSX_BUNDLE_INFO_PLIST"] = plist_path
            # 添加对ios的支持，下面这种 SET 方法会被flag中配置的覆盖掉
            # SET(CMAKE_XCODE_ATTRIBUTE_IPHONEOS_DEPLOYMENT_TARGET "7.0")
            if remove_default_flags == False:
                for item in (self.info.binaries, self.info.libraries, self.info.apps):
                    for library in item:
                        if self.arch == core.TARGET_CPU_OS:
                            library.c_flags += " -miphoneos-version-min=7.0 "
                            library.cxx_flags += " -miphoneos-version-min=7.0 "
                            library.linker_flags += " -miphoneos-version-min=7.0 "
                        elif self.arch == core.TARGET_CPU_SIMULATOR:
                            library.c_flags += " -mios-simulator-version-min=7.0 "
                            library.cxx_flags += " -mios-simulator-version-min=7.0 "
                            library.linker_flags += " -mios-simulator-version-min=7.0 "
            CMakeGenerator.generate(self)

    def generate_module_common(self, module):
        # 这里设置为NO，生成的符号会小很多的，额外指定CLANG_DEBUG_INFORMATION_LEVEL也可以一定程度减小体积
        has_symbol = "YES"
        symbol_tag = "GCC_GENERATE_DEBUGGING_SYMBOLS"
        if symbol_tag in self.info.xcode_properties:
            has_symbol = self.info.xcode_properties[symbol_tag]
        if core.data.arguments.has_opt("--ios_no_symbol"):
            has_symbol = "NO"

        module_info = XCODE_TARGET_PROPERTIES_TPL.format(module.name,
                                                         "XCODE_ATTRIBUTE_GCC_GENERATE_DEBUGGING_SYMBOLS",
                                                         has_symbol)
        if has_symbol == "YES" and core.data.build_config == core.CONFIG_RELEASE:
            module_info += XCODE_TARGET_PROPERTIES_TPL.format(module.name,
                                                              "XCODE_ATTRIBUTE_CLANG_DEBUG_INFORMATION_LEVEL",
                                                              "Line tables only")
        # 是framework类型的，设置对应属性
        if module.link_style == core.CXX_LIBRARY_LINK_STYLE_FRAMEWORK:
            # 支持设置version/short_version/bundle id
            short_version = "1.0"
            if "MACOSX_FRAMEWORK_SHORT_VERSION_STRING" in module.framework_properties:
                short_version = module.framework_properties["MACOSX_FRAMEWORK_SHORT_VERSION_STRING"]
            bundle_version = "1"
            if "MACOSX_FRAMEWORK_BUNDLE_VERSION" in module.framework_properties:
                bundle_version = module.framework_properties["MACOSX_FRAMEWORK_BUNDLE_VERSION"]
            bundle_id = "com.amap.core.framework"
            if "MACOSX_FRAMEWORK_IDENTIFIER" in module.framework_properties:
                bundle_id = module.framework_properties["MACOSX_FRAMEWORK_IDENTIFIER"]
            plist = ""
            if "MACOSX_FRAMEWORK_INFO_PLIST" in module.framework_properties:
                plist = "MACOSX_FRAMEWORK_INFO_PLIST" + module.framework_properties["MACOSX_FRAMEWORK_INFO_PLIST"]
            module_info += CMAKE_IOS_FRAMEWORK_PROPERTIES_TEMPLATE.format(module.name,
                                                                          bundle_version,
                                                                          short_version,
                                                                          bundle_id,
                                                                          plist)
        # 设置图标
        if module.app_icon:
            module_info += XCODE_TARGET_PROPERTIES_TPL.format(module.name,
                                                              "XCODE_ATTRIBUTE_ASSETCATALOG_COMPILER_APPICON_NAME",
                                                              module.app_icon)
        # 设置启动图片
        if module.launch_image:
            module_info += XCODE_TARGET_PROPERTIES_TPL.format(module.name,
                                                              "XCODE_ATTRIBUTE_ASSETCATALOG_COMPILER_LAUNCHIMAGE_NAME",
                                                              module.launch_image)
        return module_info + CMakeGenerator.generate_module_common(self, module)

    def create_build_vars(self):
        toolchain = '"' + self.__get_ios_cmake_toolchain_file() + '" -GXcode '
        self.info.build_vars["CMAKE_TOOLCHAIN_FILE"] = toolchain
        self.info.build_vars["IOS_PLATFORM"] = self.arch.upper()

    def run_build(self):
        if self.arch == core.TARGET_CPU_FUSION:
            # function类型的是自己单独的命令
            command_text = '"' + self.cmake_home + '"'
            command_text += ' . && "' + self.cmake_home + '" --build . --target all'
            self.execute_build_command(command_text)
        else:
            return CMakeGenerator.run_build(self)

    def __get_ios_cmake_toolchain_file(self):
        return os.path.join(comm_utils.get_cmake_download_root(),
                            'toolchain/ios-cmake/toolchain/iOS.cmake')

    def generate_cmake_lipo_text(self):
        """
        generate cmake for lipo
        """
        # 头信息
        self.cmake_text = CMAKE_IOS_LIPO_TEMPLATE.format(self.info.project_name,
                                                         core.MIN_CMAKE_VERSION)
        target_names = ""
        for module in self.info.libraries:
            # lipo library in outout path
            lib_file_name_list = comm_utils.get_libname_on_platform(self.info.build_target, module.name,
                                                                    module.link_style)
            lib_file_name = lib_file_name_list[0]
            params_dict = OrderedDict()
            params_dict[self.path.get_arch_output_path] = module.name
            params_dict[self.path.get_arch_export_path] = module.name + "_export"
            for call_function, name in params_dict.items():
                os_library_path = os.path.join(call_function(core.TARGET_CPU_OS), lib_file_name)
                simulator_library_path = os.path.join(call_function(core.TARGET_CPU_SIMULATOR), lib_file_name)
                fusion_library_path = os.path.join(call_function(core.TARGET_CPU_FUSION), lib_file_name)
                cmd = ""
                if module.link_style == core.CXX_LIBRARY_LINK_STYLE_FRAMEWORK:
                    cmd = "COMMAND cp {} {}".format(os.path.join(os_library_path, "Info.plist"), fusion_library_path)
                    # sym复制暂时去掉，后面可能会需要
                    # if call_function == self.path.get_arch_output_path:
                    #     cmd += "\nCOMMAND cp -rf {} {}" \
                    #         .format(os.path.join(call_function(core.TARGET_CPU_OS), lib_file_name_list[1]),
                    #                 call_function(abcoretor.TARGET_CPU_FUSION))
                    if not os.path.exists(fusion_library_path):
                        os.makedirs(fusion_library_path)
                    os_library_path = os.path.join(os_library_path, module.name)
                    simulator_library_path = os.path.join(simulator_library_path, module.name)
                    fusion_library_path = os.path.join(fusion_library_path, module.name)
                self.cmake_text += CMAKE_IOS_LIPO_MODULE_TEMPLATE.format(name,
                                                                         os_library_path,
                                                                         simulator_library_path,
                                                                         fusion_library_path,
                                                                         cmd)
                target_names += " " + name
        # add dependencies
        self.cmake_text += "ADD_DEPENDENCIES(LIPO " + target_names + ")"


def cmake_plugin_init(ctx):
    """cmake plugin entry"""
    return CMakeGeneratorIOS(ctx)
