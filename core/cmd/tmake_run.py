#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import re
import string

import core

from core.utils.tmake_cmake import *
from core.utils import tmake_process_utils as process_utils

class CommandRun(core.Command):
    """
    tmake run command class
    tmake run [test_name|all] [-d directory] [-t target] [-a arc] [-c config] [-v|-V]
    不传默认为 all
    """

    def __init__(self):
        core.Command.__init__(self)
        self.finish_binary_set = []
        self.binary_set = []
        self.run_all = False
        self.arch = ""
        self.acg = None

    def help(self):
        return "usage: tmake run [test_name|all] , all is run all tesk task program for all projects ," \
               " multiple binary separated by \'%s\' " % core.GLOBAL_SEPARATED

    def param_check(self):
        argv = self.arguments.args()
        if len(argv) > 0:
            if "all" == argv[0]:
                self.run_all = True
            else:
                self.binary_set = argv[0].split(core.GLOBAL_SEPARATED)
                for binary in self.binary_set:
                    if len(binary) <= 0:
                        raise core.TmakeException('param %s is error , please check !' % argv[0])
                if "all" in self.binary_set:
                    raise core.TmakeException('\'all\' is run all tests task program for all projects , '
                                               '%s Spaced not required' % tmake.GLOBAL_SEPARATED)
        else:
            self.run_all = True

    def __common_log_info(self):
        """
        说明当前环境的log信息
        :return:
        """
        return ' in %s , The current environment [%s-%s-%s]' % (
            self.arguments.work_path(), core.data.target, self.arch,
            core.data.build_config)

    def run(self):
        self.param_check()
        arch_list = core.get_archs()
        for arch in arch_list:
            self.arch = arch
            # 生成CMakeList
            acg_list = general_cmake_info(self.arch, False)
            self.acg = acg_list[0]
            for task in self.acg.info.tasks:
                if self.run_all or task.name in self.binary_set:
                    self.execute_task(task)

    def execute_task(self, task):
        if core.data.target == core.data.platform.host:
            core.v('curr run name : %s' % task)
            args = []
            command = string.strip(task.command)
            cwd = task.work_directory
            args += task.args
            core.v('command : {} , cwd : {} , args : {}'.format(command, cwd, args))
            if len(command) <= 0:
                raise core.TmakeException(
                    '[Possible error] tmake_host_tester_task : {} command property configuration error !!!'.format(
                        task))
            cmd_check = re.split(' *', command)
            core.v('pre   cmd_check : {}'.format(cmd_check))
            cmd_check[0] = os.path.join(self.acg.path.build_symbol_path, cmd_check[0])
            if core.data.platform.host == core.PLATFORM_WINDOWS:
                cmd_check[0] += '.exe'
            core.v('post  cmd_check : {}'.format(cmd_check))
            if not os.path.exists(cmd_check[0]):
                raise core.TmakeException('%s is not exist %s , please first build !' % (cmd_check[0],
                                                                                          self.__common_log_info()))
            if len(cwd) <= 0:
                cwd = None
            elif not os.path.isabs(cwd):
                cwd = os.path.abspath(os.path.join(self.acg.path.project_folder, cwd))
            cmd_check += args
            core.i('\n----> exec {} ......'.format(cmd_check))
            self.env_set()
            ret, msg = process_utils.execute_prog_with_sysstdout(cmd_check, cwd)
            if ret == 0:
                core.s('{} test success!\n'.format(task.name))
            else:
                raise core.TmakeException('{} test error! {}  message : {}\n'.format(task.name, ret, msg))
        else:
            raise core.TmakeException('%s and %s do not match , please do not add -t parameter' % (
                core.data.target, core.data.platform.host))

    def env_set(self):
        if core.data.target == 'linux':
            os.putenv('LD_LIBRARY_PATH', os.path.join(self.acg.path.build_path, 'export/bin'))
        elif core.data.target == 'mac':
            os.putenv('DYLD_LIBRARY_PATH', os.path.join(self.acg.path.build_path, 'export/bin'))
        elif core.data.target == 'android':
            os.putenv('LD_LIBRARY_PATH', './')
        elif core.data.target == 'ios':
            os.putenv('DYLD_LIBRARY_PATH', os.path.join(self.acg.path.build_path, 'export/bin'))


def main():
    return CommandRun()
