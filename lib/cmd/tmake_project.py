    #!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
print tmake verson
"""

import lib


class CommandProject(lib.Command):
    """
    project command
    """

    def __init__(self):
        lib.Command.__init__(self)
        self.param_all = 'all'
        self.param_silent = 'silent'
        self.param_ide_name = ''
        self.template_folder = lib.data.arguments.get_opt("-tp")  # android studio项目需要传递模板
        # vs系列及xcode生成对应project文件，用命令打开相关ide
        # cdt4生成对应project文件，但是需要手动的import
        # blocks未验证
        # clion、studio、qtc直接打开CMakeLists.txt文件
        self.supported_list = ['vs2017', 'vs2015', 'vs2013', 'vs2012', 'vs2010', 'vs2008',
                               'xcode', 'cdt4', 'blocks', 'clion', 'studio', 'qtc']

    def help(self):
        """tmake project help"""
        return 'usage : tmake project [{}] [open]'.format("|".join(self.supported_list))

    def run(self):
        lib.s("current version: " + lib.TMAKE_VERSION)

def main():
    """plugin main entry"""
    return CommandProject()

