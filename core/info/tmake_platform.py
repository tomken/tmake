#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
class PlatformInfo file
"""

import platform

from .tmake_constants import *

class PlatformInfo(object):
    """
    tmake PlatformInfo
    """

    def __init__(self):
        self.host = PlatformInfo.get_host()

    @staticmethod
    def get_host():
        if PlatformInfo.is_linux_system():
            return PLATFORM_LINUX
        elif PlatformInfo.is_windows_system():
            return PLATFORM_WINDOWS
        else:
            return PLATFORM_MAC

    @staticmethod
    def is_windows_system():
        """is window system"""
        return 'Windows' in platform.system()

    @staticmethod
    def is_linux_system():
        """is linux system"""
        return 'Linux' in platform.system()

    @staticmethod
    def is_mac_syplstem():
        """is mac system"""
        return not PlatformInfo.is_linux_system() and not PlatformInfo.is_windows_system()

    @staticmethod
    def is_64bit():
        """arm64、x86_64、x86"""
        return platform.machine().endswith('64')

    @staticmethod
    def get_cpu_arch():
        """get cpu arch"""
        if PlatformInfo.is_64bit():
            return "x64"
        else:
            return "x86"
