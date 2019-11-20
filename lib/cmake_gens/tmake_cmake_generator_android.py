#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""cmake generator android file"""
import os

import re

import abtor
from abtor.abtor_exception import SkipException
from abtor.utils import comm_utils

from .abtor_cmake_generator import AbtorCMakeGenerator

ANDROID_STL_KEY = "ANDROID_STL"
CMAKE_ANDROID_STL_TYPE_KEY = "CMAKE_ANDROID_STL_TYPE"
CMAKE_TOOLCHAIN_FILE_KEY = "CMAKE_TOOLCHAIN_FILE"

TIP_MESSAGE = """\n
The current android platforms API ({}) does not support this CPU ({}) architecture.
If you need to compile the CPU architecture, please adjust the android platforms API
to greater than or equal to 21!
add like this:

abtor_global_ccxx(
    build_vars={{"CMAKE_SYSTEM_VERSION":"21"}}
)
"""


class AbtorCMakeGeneratorAndroid(AbtorCMakeGenerator):
    """cmake generator cmake class for android"""

    def __init__(self, arch):
        AbtorCMakeGenerator.__init__(self, arch)
        self.ndk_path = self.__get_android_ndk()

    def generate(self):
        for binary in self.info.binaries:
            # 解决android 5不能运行问题
            binary.linker_flags += " -fPIE -pie "
        AbtorCMakeGenerator.generate(self)

    def generate_global_common(self):
        # debug版本才加 -g, release版本加-g1
        if abtor.data.build_config == abtor.CONFIG_DEBUG:
            self.info.global_c_flags += " -g "
            self.info.global_cxx_flags += " -g "
        else:
            self.info.global_c_flags += " -g1 "
            self.info.global_cxx_flags += " -g1 "

        self.info.global_c_flags += " -fPIC "
        self.info.global_cxx_flags += " -fPIC "
        self.info.global_c_flags += " -ffunction-sections  -fdata-sections "
        self.info.global_cxx_flags += " -ffunction-sections  -fdata-sections "
        self.info.global_linker_flags += " -Wl,--gc-sections "

        if self.arch in ["armeabi", "armeabi-v7a"]:
            self.info.global_c_flags += " -mthumb "
            self.info.global_cxx_flags += " -mthumb "

        self.info.global_defines.append("PLATFORM_ANDROID")
        if abtor.data.arguments.has_opt("--android_lto"):
            self.info.global_linker_flags += " -flto "
            self.info.cmake_command += "\n"
            self.info.cmake_command += "set(CMAKE_AR ${_ANDROID_TOOL_C_TOOLCHAIN_PREFIX}ar)\n"
            self.info.cmake_command += "set(CMAKE_RANLIB ${_ANDROID_TOOL_C_TOOLCHAIN_PREFIX}ranlib)\n"
        return ""

    def create_build_vars(self):
        self.info.build_vars["CMAKE_SYSTEM_NAME"] = "Android"
        if "CMAKE_SYSTEM_VERSION" not in self.info.build_vars:
            if self.arch in abtor.TARGET_ANDROID_CPU_64_ALL:
                self.info.build_vars["CMAKE_SYSTEM_VERSION"] = "21"
            else:
                self.info.build_vars["CMAKE_SYSTEM_VERSION"] = "14"
        self.check_system_version()
        self.info.build_vars["CMAKE_ANDROID_NDK"] = '"' + self.ndk_path + '" '
        self.info.build_vars["CMAKE_ANDROID_ARCH_ABI"] = self.arch
        # debug模式下ANDROID_STL和CMAKE_ANDROID_STL_TYPE做特殊处理，并且根据ndk版本使用不同toolchain
        # release模式下把ANDROID_STL的键值对替换成CMAKE_ANDROID_STL_TYPE
        has_android_stl = ANDROID_STL_KEY in self.info.build_vars
        has_cmake_android_stl_type = CMAKE_ANDROID_STL_TYPE_KEY in self.info.build_vars
        # debug模式并且是build命令才执行
        if abtor.data.build_config == abtor.CONFIG_DEBUG and abtor.data.arguments.abtor_cmd() == "build":
            if has_android_stl or has_cmake_android_stl_type:
                stl_info = self.info.build_vars[CMAKE_ANDROID_STL_TYPE_KEY] if has_cmake_android_stl_type else \
                    self.info.build_vars[ANDROID_STL_KEY]
                if has_android_stl:
                    self.info.build_vars.pop(ANDROID_STL_KEY)
                if has_cmake_android_stl_type:
                    self.info.build_vars.pop(CMAKE_ANDROID_STL_TYPE_KEY)
                self.info.build_vars[CMAKE_ANDROID_STL_TYPE_KEY] = stl_info
                self.info.build_vars[ANDROID_STL_KEY] = stl_info

            if "CMAKE_ANDROID_NDK_TOOLCHAIN_VERSION" in self.info.build_vars:
                # ANDROID_TOOLCHAIN_NAME
                self.info.build_vars["ANDROID_TOOLCHAIN"] = self.info.build_vars["CMAKE_ANDROID_NDK_TOOLCHAIN_VERSION"]
            else:
                self.info.build_vars["ANDROID_TOOLCHAIN"] = "gcc"
            if "CMAKE_SYSTEM_VERSION" in self.info.build_vars:
                self.info.build_vars["ANDROID_PLATFORM"] = "android-" + self.info.build_vars["CMAKE_SYSTEM_VERSION"]

            ndk_version = self.__get_android_ndk_version()
            if ndk_version:
                self.info.build_vars["ANDROID_ABI"] = self.arch
                major_version = int(ndk_version[0])
                toolchain_path = ""
                if major_version < 12:
                    abtor.log.e('!!!!!!!!ndk version < 12 , cant debug code !!!!!!!! ')
                elif major_version == 12:
                    toolchain_path = os.path.join(comm_utils.get_cmake_download_root(),
                                                  'toolchain/android-cmake/android.toolchain_debug_r12.cmake')
                elif major_version == 13:
                    toolchain_path = os.path.join(comm_utils.get_cmake_download_root(),
                                                  'toolchain/android-cmake/android.toolchain_debug_r13.cmake')
                else:
                    toolchain_path = os.path.join(self.__get_android_ndk(), 'build/cmake/android.toolchain.cmake')
                self.info.build_vars[CMAKE_TOOLCHAIN_FILE_KEY] = '"' + toolchain_path + '" '
            else:
                abtor.log.e('!!!!!!!!ndk version failed to get !!!!!!!! ')
        else:
            if has_android_stl:
                self.info.build_vars[CMAKE_ANDROID_STL_TYPE_KEY] = self.info.build_vars[ANDROID_STL_KEY]
                self.info.build_vars.pop(ANDROID_STL_KEY)

    def __get_android_ndk_version(self):
        ndk_home = self.ndk_path
        if os.path.exists(ndk_home):
            source_property_path = os.path.join(ndk_home, 'source.properties')
            if os.path.exists(source_property_path):
                source_property_file = open(source_property_path)
                line = source_property_file.readline()
                while 1:
                    r = re.match(r'^Pkg\.Revision = (\d+)\.(\d+)\.([0-9a-z-]+)$', line)
                    if r:
                        return r.groups()
                    line = source_property_file.readline()
        return None

    def __get_android_ndk(self):
        """
        参考toolchain的写法
        # Android NDK
        if(NOT ANDROID_NDK)
            if(DEFINED ENV{ANDROID_NDK}
                AND IS_DIRECTORY "$ENV{ANDROID_NDK}")
                    set(ANDROID_NDK "$ENV{ANDROID_NDK}")
            elseif(DEFINED ENV{ANDROID_NDK_HOME}
                    AND IS_DIRECTORY "$ENV{ANDROID_NDK_HOME}")
                set(ANDROID_NDK "$ENV{ANDROID_NDK_HOME}")
            elseif(DEFINED ENV{ANDROID_HOME}
                    AND IS_DIRECTORY "$ENV{ANDROID_HOME}/ndk-bundle")
                set(ANDROID_NDK "$ENV{ANDROID_HOME}/ndk-bundle")
            elseif(CMAKE_HOST_SYSTEM_NAME STREQUAL Linux
                    AND IS_DIRECTORY "$ENV{HOME}/Android/Sdk/ndk-bundle")
                set(ANDROID_NDK "$ENV{HOME}/Android/Sdk/ndk-bundle")
            elseif(CMAKE_HOST_SYSTEM_NAME STREQUAL Darwin
                    AND IS_DIRECTORY "$ENV{HOME}/Library/Android/sdk/ndk-bundle")
                set(ANDROID_NDK "$ENV{HOME}/Library/Android/sdk/ndk-bundle")
            elseif(CMAKE_HOST_SYSTEM_NAME STREQUAL Windows
                    AND IS_DIRECTORY "$ENV{LOCALAPPDATA}/Android/Sdk/ndk-bundle")
                set(ANDROID_NDK "$ENV{LOCALAPPDATA}/Android/Sdk/ndk-bundle")
            else()
                message(FATAL_ERROR "Android NDK unspecified.")
            endif()
        endif()
        """
        """get android ndk path"""
        ndk_path = self._check_ndk_path("ANDROID_NDK", "")
        if not ndk_path:
            ndk_path = self._check_ndk_path("ANDROID_NDK_HOME", "")
        if not ndk_path:
            ndk_path = self._check_ndk_path("ANDROID_HOME", "ndk-bundle")
        if not ndk_path:
            ndk_path = self._check_ndk_path("HOME", "Android/Sdk/ndk-bundle")
        if not ndk_path:
            ndk_path = self._check_ndk_path("HOME", "Library/Android/sdk/ndk-bundle")
        if not ndk_path:
            ndk_path = self._check_ndk_path("LOCALAPPDATA", "Android/Sdk/ndk-bundle")
        if not ndk_path:
            raise abtor.AbtorException("ndk path not found! please check your environment path...")
        ndk_path = ndk_path.replace('\\', '/')
        abtor.log.s("ndk_path = " + ndk_path)
        return ndk_path

    def _check_ndk_path(self, environ_key, sub_path):
        if environ_key in os.environ:
            ndk_path = os.path.join(str(os.environ[environ_key]), sub_path)
            abtor.log.i("check key:{} value:{}".format(environ_key, ndk_path))
            if os.path.isdir(ndk_path):
                return ndk_path
        return ""

    def check_system_version(self):
        if int(self.info.build_vars["CMAKE_SYSTEM_VERSION"]) < 21 \
                and self.arch in abtor.TARGET_ANDROID_CPU_64_ALL:
            arch = abtor.data.arguments.get_opt('-a', '--architecture')
            if arch and arch.lower() == "all":
                # all的64位，抛指定异常跳过，
                info = "the target is [all], but the architecture [{}] " \
                       "is not supported bv android system version [{}]! skip it."
                raise SkipException(info.format(self.arch,
                                                self.info.build_vars["CMAKE_SYSTEM_VERSION"]))
            else:
                abtor.log.e(TIP_MESSAGE.format(self.info.build_vars["CMAKE_SYSTEM_VERSION"], self.arch))
                raise abtor.AbtorException("CMAKE_SYSTEM_VERSION IS ERROR!")


def cmake_plugin_init(arch):
    """cmake plugin entry"""
    return AbtorCMakeGeneratorAndroid(arch)
