#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
tmake help command
"""

import os

import core


class CommandHelp(core.Command):
    """
    tmake help command
    """

    def __init__(self):
        core.Command.__init__(self)
        self.__separated = ','

    def help(self):
        """help"""
        return "show help"

    def param_check(self):
        pass

    def __get_allconfig(self):
        return [core.CONFIG_DEBUG, core.CONFIG_RELEASE]

    def __get_allplatform(self):
        return [core.PLATFORM_WINDOWS,
                core.PLATFORM_MAC,
                core.PLATFORM_LINUX,
                core.PLATFORM_ANDROID,
                core.PLATFORM_IOS]

    def __get_android_arc(self):
        return [core.TARGET_CPU_ARMEABI,
                core.TARGET_CPU_ARMEABI_V7A,
                core.TARGET_CPU_ARM64_V8A,
                core.TARGET_CPU_MIPS,
                core.TARGET_CPU_MIPS64,
                core.TARGET_CPU_X86,
                core.TARGET_CPU_X86_64]

    def __get_ios_arc(self):
        return [core.TARGET_CPU_OS,
                core.TARGET_CPU_SIMULATOR,
                core.TARGET_CPU_FUSION]

    def __get_qnx_arc(self):
        return [core.TARGET_CPU_X86,
                core.TARGET_CPU_ARMV7]

    def __get_mac_arc(self):
        return [core.TARGET_CPU_X86,
                core.TARGET_CPU_X64]

    def run(self):
        """tmake help entry"""
        logstr = "\nThe official website: http://tmake.amap.com/\n"
        logstr += "Usage:\n    tmake command command_paramters  [-D[-D][...]] [-opt] [--opt]"
        cur_dir = os.path.split(os.path.realpath(__file__))[0]
        cmd_list = os.listdir(cur_dir)
        logstr += "\n    ----command list----"
        for cmd_file in cmd_list:
            if cmd_file.startswith("tmake_") and cmd_file.endswith(".py") and "_base" not in cmd_file:
                cmd = cmd_file[6:-3]
                import_cmd = "import core.cmd.tmake_" + cmd
                call_cmd = "core.cmd.tmake_" + cmd + ".main()"
                try:
                    exec (import_cmd)
                except BaseException, e:
                    core.e(e)
                cmd_executor = eval(call_cmd)
                info = cmd_executor.help()
                logstr += "\n      " + cmd + " \t : " + info + "\n"

        logstr += "\n    ----opt----"
        logstr += "\n      -D                 : Define vars, use in tmake.proj. The command format:\"-Dmydef_var=mydef_value\" . You can define multiple, separated by Spaces."
        logstr += "\n                           For example: \"-DBOOL_DEFINE_VAR=True -DTEXT_DEFINE_VAR='hello' -DINT_DEFINE_VAR=800\"" \
                  "\n                                        defines 3 vars: BOOL_DEFINE_VAR, TEXT_DEFINE_VAR, INT_DEFINE_VAR. the vars can use in tmake.proj!" \
                  "\n                           Check the var is defined in tmake.proj, you can use: " \
                  "\n                                        if 'BOOL_DEFINE_VAR' in vars(): " \
                  "\n                                             print \"is defined!\""
        logstr += "\n      -M                 : Define global macro for C/C++ compilation"
        logstr += "\n                           For example: \"-MNOLOG -MVERSION=9\"" \
                  "\n                                        defines 2 macros for every C/C++ source compilation: NOLOG, VERSION=9"
        logstr += "\n      -c, --config       : Optional Settings [%s] , the default value is debug" % (
            self.__getpara(self.__get_allconfig()))
        logstr += "\n      -t, --target       : Optional Settings [%s] , the default value is curr platform" % self.__getpara(
            self.__get_allplatform())
        logstr += "\n      -d, --directory    : Optional Settings project directory , the default value is curr directory"
        logstr += "\n      -a, --architecture : Optional Settings [(android)%s, (ios)%s, (pc)%s, (qnx)%s, all] " \
                  "\n                           multiple separated by \'%s\'  , the \'all\' is contains all the cpu architecture of Current platform " \
                  "\n                           the default value is curr platform architecture" % (
                      self.__getpara(self.__get_android_arc()),
                      self.__getpara(self.__get_ios_arc()), self.__getpara(self.__get_mac_arc()),
                      self.__getpara(self.__get_qnx_arc()), self.__separated)
        logstr += "\n      -l, --alias        : Set alias for target \"embedded\", this option does not work for other targets"
        logstr += "\n      -v, --verbose      : Optional Settings show detail log , the default value is not"
        logstr += "\n      -V, --Verbose      : Optional Settings show more detail log (contain build log), the default value is not"
        core.s(logstr)

    def __getpara(self, alldata):
        result = ''
        for cccc in alldata:
            result += cccc + '|'
        return result[0:(len(result) - 1)]


def main():
    return CommandHelp()
