#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys

class ArgumentsInfo(object):
    """tmake argument info class"""

    def __init__(self, argv):
        self.argv = argv
        self.__script_file = argv[0]
        if len(argv) < 3:
            self.__work_path = os.getcwd()
            self.__tmake_path = argv[1]
            self.__tmake_cmd = ""
            self.__tmake_argv = []
            return

        self.__tmake_path = argv[1]
        self.__tmake_cmd = argv[2]
        self.__tmake_argv = argv[3:]

        self.__init_work_path()

    def __init_work_path(self):
        """
        通过参数初始化work_path
        :return:
        """
        self.__work_path = self.get_opt('d', 'directory')
        # 对相对路径的支持，把相对路径修正为绝对路径
        if self.__work_path and not os.path.isabs(self.__work_path):
            self.__work_path = os.path.abspath(os.path.join(os.getcwd(), self.__work_path))
            for i in range(0, len(self.__tmake_argv)):
                item = self.__tmake_argv[i]
                if (item == "-d" or item == "--directory") and len(self.__tmake_argv) > i + 1:
                    self.__tmake_argv[i + 1] = self.__work_path
                    break
        # 如果没设置路径默认为当前路径
        if not self.__work_path:
            self.__work_path = os.getcwd()
        from core.utils import utils
        self.__work_path = utils.fix_path_style(self.__work_path)

    def args(self):
        """return tmake command args"""
        return self.__tmake_argv

    def __get_opt_value(self, short_name, long_name):
        if short_name != None and len(short_name) == 0:
            short_name = None

        if long_name != None and len(long_name) == 0:
            long_name = None

        if short_name != None and short_name[0] != '-':
            short_name = '-' + short_name

        if long_name != None and long_name[0] != '-':
            long_name = '--' + long_name

        opt_exists = False
        opt_value = None
        for i in range(0, len(self.__tmake_argv)):
            if opt_exists:
                opt_value = self.__tmake_argv[i]
                break
            if short_name != None:
                if self.__tmake_argv[i] == short_name:
                    opt_exists = True
            if long_name != None:
                vs_arr = self.__tmake_argv[i].split('=')
                if len(vs_arr) == 1:
                    if vs_arr[0] == long_name:
                        opt_exists = True
                elif len(vs_arr) == 2:
                    if vs_arr[0] == long_name:
                        opt_exists = True
                        opt_value = vs_arr[1]
                        break
        return (opt_exists, opt_value)

    def get_opts_by_prefix(self, pre):
        """
        $ -DMACRO1 -DMACRO2=Value
        get_opts_by_prefix('-D')
        """
        opts = []
        for opt in self.__tmake_argv:
            if opt.startswith(pre):
                opts.append(opt[len(pre):])
        return opts

    def get_opt(self, short_name=None, long_name=None):
        """
        $ -k name --key name
        getOpt('-k', '--key')
        getOpt('k', 'key')
        getOpt('k')
        """
        (flag_found, flag_value) = self.__get_opt_value(short_name, long_name)
        if not flag_found:
            return None
        return flag_value

    def has_opt(self, name):
        """
        has_opt('silent')
        """
        return name in self.__tmake_argv

    def has_flag(self, short_name=None, long_name=None):
        """
        $ -k --key
        has_flag('k')
        has_flag('-k')
        has_flag(longName='--k')
        """
        (flag_found, flag_value) = self.__get_opt_value(short_name, long_name)
        if not flag_found:
            return False
        if flag_value and len(flag_value) > 0 and flag_value[0] != '-':
            return False
        return True

    def tmake_path(self):
        """tmake scripit dir"""
        return self.__tmake_path

    def work_path(self):
        """tmake work dir"""
        return self.__work_path

    def tmake_cmd(self):
        """tmake command string"""
        return self.__tmake_cmd

    def clone(self, append_cmd):
        """
        对当前arguments对象的复制，通常从一个命令调用另外一个命令时候需要
        :param append_cmd:
        :return:
        """
        temp_list = []
        pass
        temp_list.append(self.__script_file)
        temp_list.append(self.__tmake_path)
        temp_list += append_cmd
        if not self.get_opt("d"):
            temp_list.append("-d")
            temp_list.append(self.__work_path)
        temp_list.extend(self.__tmake_argv)
        result = []
        from core.utils import comm_utils
        for val in temp_list:
            # 路径中有空格的要加括号括起来
            if " " in val and not val.startswith("\""):
                val = "\"" + val + "\""
            result.append(comm_utils.fix_path_style(val))
        return ArgumentsInfo(result)
