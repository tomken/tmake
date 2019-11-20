    #!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
print tmake verson
"""

import lib


class CommandVersion(lib.Command):
    """
    help command
    """
    def help(self):
        """tmake version help"""
        return "show tmake version"

    def run(self):
        lib.s("current version: " + lib.TMAKE_VERSION)

def main():
    """plugin main entry"""
    return CommandVersion()

