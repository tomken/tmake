#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""cmake generator linux file"""

import core
from core import PlatformInfo
from core.info.tmake_auto_cmake_commands import get_cmake_command

from .tmake_cmake_generator import CMakeGenerator


class CMakeGeneratorLinux(CMakeGenerator):
    """cmake generator cmake class for Linux"""

    def generate_global_common(self):
        # chang self.info for Linux
        self.info.global_defines.append("PLATFORM_UBUNTU")
        self.info.global_defines.append("PLATFORM_LINUX")
        self.info.global_c_flags += " -fPIC -g "
        self.info.global_cxx_flags += " -fPIC -g "
        # if self.arch == core.TARGET_CPU_X86 and PlatformInfo.is_64bit():
        #     self.info.global_c_flags += ' -m32 '
        #     self.info.global_cxx_flags += ' -m32 '
        # elif self.arch == core.TARGET_CPU_X64 and not PlatformInfo.is_64bit():
        #     self.info.global_c_flags += ' -m64 '
        #     self.info.global_cxx_flags += ' -m64 '
        return ""

    def generate(self):
        cmd = get_cmake_command(self.arch)
        if cmd:
            self.info.cmake_command_default += " " + cmd
        CMakeGenerator.generate(self)

    def generate_module_common(self, module):
        cmake_text = ""
        stdafx_path = ""
        for h in module.srcs:
            if h.endswith("stdafx.cpp"):
                h = h[:-3] + 'h'
                stdafx_path = h
                break
        if stdafx_path:
            cmake_text += core.LINESEP + "# Precompile Compile Header" + core.LINESEP
            cmake_text += "SET(GCH_CXX_FLAGS ${CMAKE_CXX_FLAGS})" + core.LINESEP + core.LINESEP
            cmake_text += "GET_PROPERTY(_all_include_directories TARGET {} PROPERTY INCLUDE_DIRECTORIES)".format(module.name)
            cmake_text += """
FOREACH(inc ${_all_include_directories})
    LIST(APPEND GCH_CXX_FLAGS "-I${inc}")
ENDFOREACH(inc)
"""

            cmake_text += """
GET_DIRECTORY_PROPERTY(_all_definitions COMPILE_DEFINITIONS)
FOREACH(def ${_all_definitions})
    LIST(APPEND GCH_CXX_FLAGS "-D${def}")
ENDFOREACH(def)

"""

            cmake_text += "GET_PROPERTY(_all_definitions TARGET {} PROPERTY COMPILE_DEFINITIONS)".format(module.name)
            cmake_text += """
FOREACH(def ${_all_definitions})
    LIST(APPEND GCH_CXX_FLAGS "-D${def}")
ENDFOREACH(def)

"""
            cmake_text += "GET_PROPERTY(_all_compile_options TARGET {} PROPERTY COMPILE_OPTIONS)".format(module.name)
            cmake_text += """
MESSAGE("_all_compile_options: ${_all_compile_options}")
IF (_all_compile_options)
    SET(_all_options "")
    FOREACH(opt ${_all_compile_options})
        SET(_all_options "${_all_options} ${opt}")
    ENDFOREACH()
    MESSAGE("_all_options: ${_all_options}")

    STRING(REGEX REPLACE ".*COMPILE_LANGUAGE:CXX>:(.*)>" \\\\1 _language_cxx_options ${_all_options})
    MESSAGE("_language_cxx_options: ${_language_cxx_options}")
    SEPARATE_ARGUMENTS(_language_cxx_options)

    FOREACH(opt ${_language_cxx_options})
        LIST(APPEND GCH_CXX_FLAGS "${opt}")
    ENDFOREACH(opt)
ENDIF()
"""
            cmake_text += """
IF(${CMAKE_BUILD_TYPE} STREQUAL "Release")
    LIST(APPEND GCH_CXX_FLAGS "-DNDEBUG")
ENDIF()

SEPARATE_ARGUMENTS(GCH_CXX_FLAGS)

MESSAGE("GCH_CXX_FLAGS: ${GCH_CXX_FLAGS}")

SET(HAS_HASH_STYLE_FLAG False)
FOREACH(flag ${GCH_CXX_FLAGS})
    STRING(REGEX MATCH "--hash-style" HASH_STYLE_FLAG ${flag})
    IF (HASH_STYLE_FLAG)
        SET(HAS_HASH_STYLE_FLAG True)
    ENDIF()
ENDFOREACH(flag)
MESSAGE("HAS_HASH_STYLE_FLAG: ${HAS_HASH_STYLE_FLAG}")

IF (NOT ${HAS_HASH_STYLE_FLAG})
"""
            cmake_text += "    target_compile_options({} PRIVATE -Winvalid-pch -include stdafx.h){}".format(module.name,
                                                                                                        core.LINESEP)
            cmake_text += "    ADD_CUSTOM_COMMAND(OUTPUT " + stdafx_path + ".gch COMMAND ${CCACHE_PROGRAM} ${CMAKE_CXX_COMPILER} ${GCH_CXX_FLAGS} " + stdafx_path + ")" + core.LINESEP
            cmake_text += "    ADD_CUSTOM_TARGET({}_gch DEPENDS {}.gch){}".format(module.name, stdafx_path, core.LINESEP)
            cmake_text += "    ADD_DEPENDENCIES({} {}_gch){}".format(module.name, module.name, abtcoreor.LINESEP)
            cmake_text += "ENDIF()" + core.LINESEP + core.LINESEP

        if self.arch == "x64" or self.arch == "x86" or self.arch == "centos32" or self.arch == "centos64":
            self.info.global_include_dirs.append("/usr/local/include")
        return CMakeGenerator.generate_module_common(self, module) + cmake_text


def cmake_plugin_init(ctx):
    """cmake plugin entry"""
    return CMakeGeneratorLinux(ctx)
