#!/usr/bin/python
# -*- coding: UTF-8 -*-

from core.utils.tmake_cmake import *


class CommandUtil(core.Command):
    def __init__(self):
        core.Command.__init__(self)
        self.command = ''

    def help(self):
        return "utils"

    def param_check(self):
        argv = self.arguments.args()
        if len(argv) > 0:
            self.command = argv[0]

    def run(self):
        self.param_check()
        if self.command == 'remove_bom':
            self.remove_bom()

    def remove_bom(self):
        import codecs
        from core.info.tmake_builtin import tmake_glob
        all_file = tmake_glob(self.arguments.work_path(), "*.h", True)
        all_file += tmake_glob(self.arguments.work_path(), "*.c", True)
        all_file += tmake_glob(self.arguments.work_path(), "*.cpp", True)
        all_file += tmake_glob(self.arguments.work_path(), "*.hpp", True)
        count = 0
        for item in all_file:
            with open(item) as f:
                data = f.read()
                if data[:3] != codecs.BOM_UTF8:
                    continue
                data = data[3:]
                with open(item, 'w') as fin:
                    fin.write(data)
                count += 1
        core.s('成功处理 {} 个文件的bom头信息.'.format(count))


def main():
    return CommandUtil()
