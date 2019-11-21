#!/usr/bin/python
# -*- coding: UTF-8 -*-
import subprocess

import sys

import core


# 执行单个进程并输出结果
# 如果有参数，则传入参数应该为字符串的列表
# 返回值为程序returncode和输出结果
# 此接口有如下问题：
#  1.  输出结果只能执行完一次性输出。中间不输出任何东西
#  2.  如果执行的程序中途崩溃，会导致部分输出日志丢失
#  以上两个问题的修复方案：使用 execute_prog_with_sysstdout 替代
def execute_prog_with_output(command, pram_cwd=None):
    code = -1
    ret = ''
    core.v("execute_prog_with_output: " + str(command))
    try:
        process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=pram_cwd)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            ret += line
        process.wait()
        code = process.returncode
    except BaseException as e:
        core.e(' Exception : %s ' % e)
    return code, ret


# execute_prog_with_output的优化版本。
def execute_prog_with_sysstdout(command, pram_cwd=None):
    code = -1
    ret = ''
    core.v("execute_prog_with_sysstdout: " + str(command))
    try:
        process = subprocess.Popen(command, shell=False, stdout=sys.stdout, stderr=sys.stderr, cwd=pram_cwd)
        process.wait()
        code = process.returncode
    except BaseException as e:
        core.e(' Exception : %s ' % e)
    return code, ret


# 执行程序并返回结果
# 输入参数为字符串，可以为多个程序并可加参数，多个命令用 && 分隔
def execute_prog(command):
    core.v("execute_prog: " + str(command))
    return subprocess.call(command, shell=True)


def execute_with_msg(cmd):
    """
    返回命令执行的文本输出
    :param cmd:
    :return:
    """
    core.v("execute_with_msg: " + str(cmd))
    import os
    r = os.popen(cmd)
    text = r.read()
    r.close()
    return text
