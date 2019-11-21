#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys

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

def reset_deps(deps):
    new_deps = []
    if deps and isinstance(deps, list):
        for dep in deps:
            dep_name, dep_version, custom_link_name = parse_dep(dep)
            if "windows" in core.data.target and dep_version != "local":
                if core.SHARED_SUFFIX not in dep_name:
                    ret = is_library_exist(dep_name, dep_version, abtor.data.target, abtor.data.arch, "abtor.xml")
                    if not ret:
                        new_name = dep_name + core.SHARED_SUFFIX
                        ret = is_library_exist(new_name, dep_version, abtor.data.target, abtor.data.arch, "abtor.xml")
                        if ret:
                            dep_name = new_name
            if custom_link_name:
                new_deps.append("{}:{}/{}".format(dep_name, dep_version, custom_link_name))
            else:
                new_deps.append("{}:{}".format(dep_name, dep_version))
    return new_deps

def write_entire_file(filepath, content):
    """write file"""
    fof = open(filepath, 'w')
    fof.write(content)
    fof.close()

def get_cmake_prog():
    """get cmake path"""
    if core.data.cmake_path:
        return core.data.cmake_path
    prog = which('cmake')
    if prog != None:
        return prog
    return None

#
# an almost exact copy of the shutil.which() implementation from python3.4
#
def which(cmd, mode=os.F_OK | os.X_OK, path=None):
    """Given a command, mode, and a PATH string, return the path which
    conforms to the given mode on the PATH, or None if there is no such
    file.

    `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
    of os.environ.get("PATH"), or can be overridden with a custom search
    path.

    """

    # Check that a given file can be accessed with the correct mode.
    # Additionally check that `file` is not a directory, as on Windows
    # directories pass the os.access check.
    def _access_check(fn, mode):
        return (os.path.exists(fn) and os.access(fn, mode)
                and not os.path.isdir(fn))

    # If we're given a path with a directory part, look it up directly rather
    # than referring to PATH directories. This includes checking relative to
    # the current directory, e.g. ./script
    if os.path.dirname(cmd):
        if _access_check(cmd, mode):
            return cmd
        return None

    if path is None:
        path = os.environ.get("PATH", os.defpath)
    if not path:
        return None
    path = path.split(os.pathsep)

    if sys.platform == "win32":
        # The current directory takes precedence on Windows.
        if os.curdir not in path:
            path.insert(0, os.curdir)

        # PATHEXT is necessary to check on Windows.
        pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
        # See if the given file matches any of the expected path extensions.
        # This will allow us to short circuit when given "python.exe".
        # If it does match, only test that one, otherwise we have to try
        # others.
        if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
            files = [cmd]
        else:
            files = [cmd + ext for ext in pathext]
    else:
        # On other platforms you don't have things like PATHEXT to tell you
        # what file suffixes are executable, so just pass on cmd as-is.
        files = [cmd]

    seen = set()
    for dir in path:
        normdir = os.path.normcase(dir)
        if normdir not in seen:
            seen.add(normdir)
            for thefile in files:
                name = os.path.join(dir, thefile)
                if _access_check(name, mode):
                    return name
    return None
