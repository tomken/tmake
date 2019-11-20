    #!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
print tmake verson
"""

import lib


class CommandBuild(lib.Command):
    """
    help command
    """
    def help(self):
        """tmake build help"""
        return "<usage>: tmake build [[no-test|nt] | [all-proj-test|apt]] " + \
               " [encrypt=<filepath>]  [-vs custom vs version] "

    def run(self):
        lib.s("current version: " + lib.TMAKE_VERSION)

def main():
    """plugin main entry"""
    return CommandBuild()

