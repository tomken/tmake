    #!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
print tmake verson
"""

import core


class CommandBuild(core.Command):
    """
    help command
    """
    def help(self):
        """tmake build help"""
        return "<usage>: tmake build [[no-test|nt] | [all-proj-test|apt]] " + \
               " [encrypt=<filepath>]  [-vs custom vs version] "

    def run(self):
        core.s("current version: " + core.TMAKE_VERSION)

def main():
    """plugin main entry"""
    return CommandBuild()

