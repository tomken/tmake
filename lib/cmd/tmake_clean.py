    #!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
print tmake verson
"""

import lib


class CommandClean(lib.Command):
    """
    clean command
    """
    def help(self):
        """tmake clean help"""
        return "clean [all] [silent] [deep] , default clean build results of the current project. \
         all: clean local import project. \
         silent: clean with no tip.\
         deep: clean build, local_export, project, publish folder.\
         "

    def run(self):
        lib.s("current version: " + lib.TMAKE_VERSION)

def main():
    """plugin main entry"""
    return CommandClean()

