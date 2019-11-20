#!/usr/bin/python
# -*- coding: UTF-8 -*-
import ctypes

import sys
import platform

from .info.tmake_platform import PlatformInfo

STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
STD_ERROR_HANDLE = -12

COLOR_RED = 1
COLOR_GREEN = 2
COLOR_DARK_GRAY = 3
COLOR_WHITE = 4

TMAKE_VERBOSE = False
MEG_FLAG = 'tmake message: '

TMAKE_LOG_DEBUG = True
TMAKE_LOG_INFO = True
TMAKE_LOG_ERROR = True
TMAKE_LOG_SUCCESS = True



def tmake_print(msg):
    msg = '{0} {1}'.format(MEG_FLAG, msg)
    try:
        # 这里的不用comm_utils里的，不然可能会有未初始化好问题
        if 'Windows' in platform.system():
            msg = msg.decode('utf-8').encode(sys.getfilesystemencoding())
    except Exception:
        pass
    print msg


# debug log
def v(msg):
    if TMAKE_VERBOSE:
        attributes = set_cmd_text_color(COLOR_DARK_GRAY)
        tmake_print(msg)
        reset_color(attributes)


# info log
def i(msg):
    if TMAKE_LOG_INFO:
        attributes = set_cmd_text_color(COLOR_WHITE)
        tmake_print(msg)
        reset_color(attributes)


# error log
def e(msg):
    if TMAKE_LOG_ERROR:
        attributes = set_cmd_text_color(COLOR_RED)
        tmake_print(msg)
        reset_color(attributes)


# success log
def s(msg):
    if TMAKE_LOG_SUCCESS:
        attributes = set_cmd_text_color(COLOR_GREEN)
        tmake_print(msg)
        reset_color(attributes)


def __win_text_color_map(clr):
    if clr == COLOR_RED:
        return 0x0c
    elif clr == COLOR_GREEN:
        return 0x0a
    elif clr == COLOR_DARK_GRAY:
        return 0x08
    elif clr == COLOR_WHITE:
        return 0x0f


def __linux_text_color_map(clr):
    if clr == COLOR_RED:
        return 31
    elif clr == COLOR_GREEN:
        return 32
    elif clr == COLOR_DARK_GRAY:
        return 33
    elif clr == COLOR_WHITE:
        return 37


def text_color_map(clr):
    if PlatformInfo.is_windows_system():
        return __win_text_color_map(clr)
    else:
        return __linux_text_color_map(clr)


# get handle
class _COORD(ctypes.Structure):
    _fields_ = [
        ("X", ctypes.c_short),
        ("Y", ctypes.c_short)]


class _SMALL_RECT(ctypes.Structure):
    _fields_ = [
        ("Left", ctypes.c_short),
        ("Top", ctypes.c_short),
        ("Right", ctypes.c_short),
        ("Bottom", ctypes.c_short)]


class _CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [
        ("dwSize", _COORD),
        ("dwCursorPosition", _COORD),
        ("wAttributes", ctypes.c_ushort),
        ("srWindow", _SMALL_RECT),
        ("dwMaximumWindowSize", _COORD)]


def __set_text_color(color, handle):
    if PlatformInfo.is_windows_system():
        ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)


def set_cmd_text_color(color, handle=None):
    color = text_color_map(color)
    if PlatformInfo.is_windows_system():
        if handle is None:
            handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        buffer_info = _CONSOLE_SCREEN_BUFFER_INFO()
        ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(buffer_info))
        __set_text_color(color, handle)
        return buffer_info.wAttributes
    else:
        print '\033[0;' + str(color) + 'm'


def get_default_buffer_info():
    if PlatformInfo.is_windows_system():
        handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        buffer_info = _CONSOLE_SCREEN_BUFFER_INFO()
        ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(buffer_info))
        return buffer_info.wAttributes
    else:
        return None


def reset_color(attributes, handle=None):
    if PlatformInfo.is_windows_system():
        if handle is None:
            handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        __set_text_color(attributes, handle)
    else:
        print '\033[0m'


"""
# Windows CMD命令行 字体颜色定义 text colors
FOREGROUND_BLACK = 0x00 # black.
FOREGROUND_DARKBLUE = 0x01 # dark blue.
FOREGROUND_DARKGREEN = 0x02 # dark green.
FOREGROUND_DARKSKYBLUE = 0x03 # dark skyblue.
FOREGROUND_DARKRED = 0x04 # dark red.
FOREGROUND_DARKPINK = 0x05 # dark pink.
FOREGROUND_DARKYELLOW = 0x06 # dark yellow.
FOREGROUND_DARKWHITE = 0x07 # dark white.
FOREGROUND_DARKGRAY = 0x08 # dark gray.
FOREGROUND_BLUE = 0x09 # blue.
FOREGROUND_GREEN = 0x0a # green.
FOREGROUND_SKYBLUE = 0x0b # skyblue.
FOREGROUND_RED = 0x0c # red.
FOREGROUND_PINK = 0x0d # pink.
FOREGROUND_YELLOW = 0x0e # yellow.
FOREGROUND_WHITE = 0x0f # white.


# Windows CMD命令行 背景颜色定义 background colors
BACKGROUND_DARKSKYBLUE = 0x30 # dark skyblue.
BACKGROUND_DARKRED = 0x40 # dark red.
BACKGROUND_DARKPINK = 0x50 # dark pink.
BACKGROUND_DARKYELLOW = 0x60 # dark yellow.
BACKGROUND_DARKWHITE = 0x70 # dark white.
BACKGROUND_DARKGRAY = 0x80 # dark gray.
BACKGROUND_BLUE = 0x90 # blue.
BACKGROUND_GREEN = 0xa0 # green.
BACKGROUND_SKYBLUE = 0xb0 # skyblue.
BACKGROUND_RED = 0xc0 # red.
BACKGROUND_PINK = 0xd0 # pink.
BACKGROUND_YELLOW = 0xe0 # yellow.
BACKGROUND_WHITE = 0xf0 # white.

# like-linux
字颜色:30-----------37
30:黑
31:红
32:绿
33:黄
34:蓝色
35:紫色
36:深绿
37:白色
"""
