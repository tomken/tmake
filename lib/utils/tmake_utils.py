#!/usr/bin/python
# -*- coding: UTF-8 -*-

import lib

from .tmake_arch_helper import ArchHelper

def fix_path_style(path):
    """
    把\\及\类型的路径修复为/
    :param path:
    :return:
    """
    if not path:
        return ""
    temp_path = path.replace("\\\\", "/")
    return temp_path.replace("\\", "/")

def exec_tmake_command(arguments):
    """execCommand"""
    command = arguments.tmake_cmd()
    import_cmd = "import lib.cmd.tmake_" + command
    call_cmd = "lib.cmd.tmake_" + command + ".main()"
    try:
        exec import_cmd
    except ImportError:
        raise lib.TmakeException("The command:" + command + " is not support! Please check your command!")
    
    # 这里不抓取异常，不然外面获取不到
    cmd_executor = eval(call_cmd)
    cmd_executor.set_argument(arguments)
    if arguments.has_opt("help") or arguments.has_flag(None, "help"):
        lib.i("help info:\n" + cmd_executor.help())
    else:
        cmd_executor.run()

def get_archs():
    """get cpu archs"""
    arch = lib.data.arguments.get_opt('-a', '--architecture')
    if arch is None:
        if lib.data.target == lib.PLATFORM_ANDROID:
            arch = lib.ANDROID_DEFAULT_CPU
        elif lib.data.target == lib.PLATFORM_IOS:
            arch = lib.TARGET_CPU_ALL
        elif lib.data.target == lib.PLATFORM_LINUX:
            arch = lib.TARGET_CPU_UBUNTU64
        elif lib.data.target == lib.data.platform.host:
            arch = lib.PlatformInfo.get_cpu_arch()
        else:
            raise lib.TmakeException("no architecture param. please add '-a' or '--architecture' param!")

    archs = arch.split(lib.GLOBAL_SEPARATED)

    all_supported_arcs = None
    if lib.data.target in lib.TARGET_ALL_CPU_MAP:
        all_supported_arcs = lib.TARGET_ALL_CPU_MAP[lib.data.target]

    # parse all
    if 'all' in archs:
        if len(archs) > 1:
            raise lib.TmakeException('\'all\' contains all the architecture, please check and reset!')
        archs = all_supported_arcs
    else:
        # check
        arch_list = ArchHelper(lib.data.arguments.work_path()).get_arch_list()
        for arc in archs:
            if arc not in all_supported_arcs and arch not in arch_list:
                all_supported_arcs += arch_list
                raise lib.TmakeException('%s is not support , must be in %s' % (arc, all_supported_arcs))

    # filt
    if lib.data.target == lib.PLATFORM_IOS:
        # fusion depends os and simulator for these commands, so add all
        if lib.TARGET_CPU_FUSION in archs and lib.data.arguments.tmake_cmd() in ["build", "clean", "project"]:
            archs = lib.TARGET_IOS_CPU_ALL
    return archs