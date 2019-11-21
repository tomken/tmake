#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
cmake windows generator file
"""
import os

import core
from core.utils import comm_utils
from core.info.tmake_auto_cmake_commands import get_cmake_command
from .tmake_cmake_generator import CMakeGenerator, CMakeSourceItem

PLUGIN_VERSION = "1.0.0"

RELEASE_PDB_FLAG = """
set(CMAKE_EXE_LINKER_FLAGS_RELEASE "${CMAKE_EXE_LINKER_FLAGS_RELEASE} /DEBUG")
set(CMAKE_SHARED_LINKER_FLAGS_RELEASE "${CMAKE_SHARED_LINKER_FLAGS_RELEASE} /DEBUG")
"""

CMAKE_LINKERS_FLAGS = """
set(CMAKE_EXE_LINKER_FLAGS    "${CMAKE_EXE_LINKER_FLAGS} /MANIFEST:NO")
set(CMAKE_MODULE_LINKER_FLAGS "${CMAKE_MODULE_LINKER_FLAGS} /MANIFEST:NO")
set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} /MANIFEST:NO")
"""

class CMakeGeneratorWindows(CMakeGenerator):
    """cmake generator cmake class for Windows"""

    def generate_global_common(self):
        # 解决 Failed to write the updated manifest to the resource of file "bin\GNaviMap.dll". The operation failed.
        # http://blog.sciencenet.cn/blog-419857-649812.html
        # https://github.com/KDAB/GammaRay/issues/458
        self.info.global_defines.append("PLATFORM_WIN32")
        cmake_info = CMAKE_LINKERS_FLAGS
        # 生成pdb
        if self.info.build_config == core.CONFIG_RELEASE and core.data.arguments.tmake_cmd() == "build":
            cmake_info += RELEASE_PDB_FLAG
        return cmake_info

    def generate(self):
        for app in self.info.apps:
            app.link_style = 'WIN32'

        cmd = get_cmake_command(self.arch)
        if cmd:
            self.info.cmake_command_default += " " + cmd
        CMakeGenerator.generate(self)


def cmake_plugin_init(ctx):
    """cmake plugin entry"""
    return CMakeGeneratorWindows(ctx)
