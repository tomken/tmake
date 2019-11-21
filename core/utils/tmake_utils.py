#!/usr/bin/python
# -*- coding: UTF-8 -*-

import core

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
    import_cmd = "import core.cmd.tmake_" + command
    call_cmd = "core.cmd.tmake_" + command + ".main()"
    try:
        exec import_cmd
    except ImportError:
        raise core.TmakeException("The command:" + command + " is not support! Please check your command!")
    
    # 这里不抓取异常，不然外面获取不到
    cmd_executor = eval(call_cmd)
    cmd_executor.set_argument(arguments)
    if arguments.has_opt("help") or arguments.has_flag(None, "help"):
        core.i("help info:\n" + cmd_executor.help())
    else:
        cmd_executor.run()

def get_archs():
    """get cpu archs"""
    arch = core.data.arguments.get_opt('-a', '--architecture')
    if arch is None:
        if core.data.target == core.PLATFORM_ANDROID:
            arch = core.ANDROID_DEFAULT_CPU
        elif core.data.target == core.PLATFORM_IOS:
            arch = core.TARGET_CPU_ALL
        elif core.data.target == core.PLATFORM_LINUX:
            arch = core.TARGET_CPU_UBUNTU64
        elif core.data.target == core.data.platform.host:
            arch = core.PlatformInfo.get_cpu_arch()
        else:
            raise core.TmakeException("no architecture param. please add '-a' or '--architecture' param!")

    archs = arch.split(core.GLOBAL_SEPARATED)

    all_supported_arcs = None
    if core.data.target in core.TARGET_ALL_CPU_MAP:
        all_supported_arcs = core.TARGET_ALL_CPU_MAP[core.data.target]

    # parse all
    if 'all' in archs:
        if len(archs) > 1:
            raise core.TmakeException('\'all\' contains all the architecture, please check and reset!')
        archs = all_supported_arcs
    else:
        # check
        arch_list = ArchHelper(core.data.arguments.work_path()).get_arch_list()
        for arc in archs:
            if arc not in all_supported_arcs and arch not in arch_list:
                all_supported_arcs += arch_list
                raise core.TmakeException('%s is not support , must be in %s' % (arc, all_supported_arcs))

    # filt
    if core.data.target == core.PLATFORM_IOS:
        # fusion depends os and simulator for these commands, so add all
        if core.TARGET_CPU_FUSION in archs and core.data.arguments.tmake_cmd() in ["build", "clean", "project"]:
            archs = core.TARGET_IOS_CPU_ALL
    return archs

def read_all_from_file(full_path):
    fd = open(full_path, 'rb')
    result = fd.read()
    fd.close()
    return result

def fix_path_to_abs(srcs):
    new_srcs = []
    for src in srcs:
        if src == None:
            continue
        new_srcs.append(core.info.tmake_builtin.tmake_path(src))
    return new_srcs

def clean(path):
    """clean build folder"""
    try:
        if os.path.exists(path):
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)
    except Exception as exp:
        core.e(exp)
        core.e('Possible Cause: {} is locked \
        or do not have permission when clean, please check'.format(path))
    core.s("clear {} finished".format(path))
