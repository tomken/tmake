#!/usr/bin/python
# -*- coding: UTF-8 -*-

import lib

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
