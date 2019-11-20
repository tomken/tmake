#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""cmake generator mac file"""
import os

import lib
from lib.info.tmake_builtin import tmake_path
from .tmake_cmake_generator import CMakeGenerator, CMakeSourceItem

PLUGIN_VERSION = "1.0.0"

CMAKE_IOS_RESOURCE_TEMPLATE = """
set({} {})
set_source_files_properties(${{{}}} PROPERTIES MACOSX_PACKAGE_LOCATION {})
"""


class CMakeGeneratorOSX(CMakeGenerator):
    """cmake generator cmake class for OSX"""

    def generate(self):
        self.info.global_c_flags += " -g  "
        self.info.global_cxx_flags += " -g "
        self.info.global_defines.append("PLATFORM_MAC")
        for app in self.info.apps:
            app.link_style = abtor.CXX_LIBRARY_LINK_STYLE_MACOSX_BUNDLE
            if app.plist:
                plist_path = abtor_path(app.plist)
                app.properties["MACOSX_BUNDLE_INFO_PLIST"] = plist_path
        CMakeGenerator.generate(self)

    def create_build_vars(self):
        arch = 'i386' if self.arch == abtor.TARGET_CPU_X86 else 'x86_64'
        self.info.build_vars["CMAKE_OSX_ARCHITECTURES"] = arch

    def generate_module_common(self, module):
        module.include_dirs.append("/usr/local/include")
        return CMakeGenerator.generate_module_common(self, module)

    def generate_global_common(self):
        self.info.global_defines.append("PLATFORM_MAC")
        return ""

def cmake_plugin_init(arch):
    """cmake plugin entry"""
    return CMakeGeneratorOSX(arch)
