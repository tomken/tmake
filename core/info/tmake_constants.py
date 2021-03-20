#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os


TMAKE_VERSION = '1.0.0'

# cmake
MIN_CMAKE_VERSION = '3.1'
DEFAULT_CMAKE_VERSION = '3.13.1'

LINESEP = "\n"
TMAKE_DEFAULT_PATH = os.path.join(os.path.expanduser('~'),
                                  ".tmake")
TMAKE_LIBRARIES_PATH = os.path.join(TMAKE_DEFAULT_PATH,
                                    "libraries")
TMAKE_LOCK_PATH = os.path.join(TMAKE_DEFAULT_PATH,
                               "lock")

# build config
CONFIG_RELEASE = 'release'
CONFIG_DEBUG = 'debug'

# cmake
CMAKE_SCRIPT_FILE_NAME = 'CMakeLists.txt'
CMAKE_CACHE_FILE_NAME = 'CMakeCache.txt'

# C++ library type
CXX_LIBRARY_LINK_STYLE_STATIC = 'STATIC'
CXX_LIBRARY_LINK_STYLE_SHARED = 'SHARED'
CXX_LIBRARY_LINK_STYLE_FRAMEWORK = 'FRAMEWORK'
CXX_LIBRARY_LINK_STYLE_MACOSX_BUNDLE = 'MACOSX_BUNDLE'

ALLOW_LINK_STYLE_LIST = ["static", "dynamic", "framework"]

SHARED_SUFFIX = "_shared"
BINARY_SUFFIX = "_binary"
FRAMEWORK_SUFFIX = "_framework"

BUILD_INSTALL_PREFIX = 'export'
BUILD_OUTPUT_NAME = 'bin'

# platform define
PLATFORM_WINDOWS = 'windows'
PLATFORM_MAC = 'mac'
PLATFORM_LINUX = 'linux'
PLATFORM_ANDROID = 'android'
PLATFORM_IOS = 'ios'
PLATFORM_ALL = [PLATFORM_WINDOWS, PLATFORM_MAC, PLATFORM_LINUX,
                PLATFORM_ANDROID, PLATFORM_IOS]

# CPU define
TARGET_CPU_X86 = 'x86'
TARGET_CPU_X64 = 'x64'

TARGET_CPU_ARMEABI = 'armeabi'
TARGET_CPU_ARMEABI_V7A = 'armeabi-v7a'
TARGET_CPU_ARM64_V8A = 'arm64-v8a'
TARGET_CPU_MIPS = 'mips'
TARGET_CPU_MIPS64 = 'mips64'
TARGET_CPU_X86_64 = 'x86_64'

TARGET_CPU_OS = 'os'
TARGET_CPU_SIMULATOR = 'simulator'
TARGET_CPU_FUSION = 'fusion'
TARGET_CPU_ARMV7 = 'armv7'
TARGET_CPU_I386 = 'i386'
TARGET_CPU_ARM64 = 'arm64'

TARGET_CPU_1286 = "vs2012x86"
TARGET_CPU_1264 = "vs2012x64"
TARGET_CPU_1586 = "vs2015x86"
TARGET_CPU_1564 = "vs2015x64"
TARGET_CPU_WIN32 = 'win32'
TARGET_CPU_WINCE_ARMV7 = 'wince_armv7'
TARGET_CPU_WINCE_ARMV4I = 'wince_armv4i'
TARGET_CPU_WINCE_CE6_ARMV4I = 'wince_ce6_armv4i'

TARGET_CPU_CENTOS32 = 'centos32'
TARGET_CPU_CENTOS64 = 'centos64'
TARGET_CPU_UBUNTU32 = 'ubuntu32'
TARGET_CPU_UBUNTU64 = 'ubuntu64'

ANDROID_DEFAULT_CPU = 'armeabi-v7a'
TARGET_CPU_ALL = [ANDROID_DEFAULT_CPU]

TARGET_WINDOWS_CPU_ALL = [TARGET_CPU_X86, TARGET_CPU_X64, TARGET_CPU_1286, TARGET_CPU_1264, TARGET_CPU_1586,
                          TARGET_CPU_1564, TARGET_CPU_WIN32, TARGET_CPU_WINCE_ARMV7, TARGET_CPU_WINCE_ARMV4I,
                          TARGET_CPU_WINCE_CE6_ARMV4I]

TARGET_LINUX_CPU_ALL = [TARGET_CPU_X86,
                        TARGET_CPU_X64,
                        TARGET_CPU_CENTOS32,
                        TARGET_CPU_CENTOS64,
                        TARGET_CPU_UBUNTU32,
                        TARGET_CPU_UBUNTU64,
                        ]

TARGET_MAC_CPU_ALL = [TARGET_CPU_X86, TARGET_CPU_X64]
TARGET_ANDROID_CPU_32_ALL = [
    TARGET_CPU_ARMEABI, TARGET_CPU_ARMEABI_V7A, TARGET_CPU_MIPS, TARGET_CPU_X86]
TARGET_ANDROID_CPU_64_ALL = [TARGET_CPU_ARM64_V8A,
                             TARGET_CPU_MIPS64, TARGET_CPU_X86_64]
TARGET_ANDROID_CPU_ALL = TARGET_ANDROID_CPU_32_ALL + TARGET_ANDROID_CPU_64_ALL
TARGET_IOS_CPU_ALL = [TARGET_CPU_OS, TARGET_CPU_SIMULATOR, TARGET_CPU_FUSION]

TARGET_ALL_CPU_MAP = {
    PLATFORM_WINDOWS: TARGET_WINDOWS_CPU_ALL,
    PLATFORM_LINUX: TARGET_LINUX_CPU_ALL,
    PLATFORM_MAC: TARGET_MAC_CPU_ALL,
    PLATFORM_ANDROID: TARGET_ANDROID_CPU_ALL,
    PLATFORM_IOS: TARGET_IOS_CPU_ALL
}

GLOBAL_SEPARATED = ','
