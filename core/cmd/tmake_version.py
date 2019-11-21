    #!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
print tmake verson
"""

import core


class CommandVersion(core.Command):
    """
    help command
    """
    def help(self):
        """tmake version help"""
        return "show tmake version"

    def run(self):
        core.s("current version: " + core.TMAKE_VERSION)

def main():
    """plugin main entry"""
    return CommandVersion()

