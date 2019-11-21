#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
dep library parse
"""

import os
import xml.dom.minidom

import core

ROOT_NAME = "project"
NAME = 'name'
LINK_NAME = 'link_name'
VERSION = 'version'
INCLUDE_DIR = 'include_dir'
LIB_DIR = 'lib_dir'
SYM_LIB_DIR = 'sym_lib_dir'
PACKAGE = 'package'
DEPS = 'deps'
PUBLISH_INFO = 'info'
DEFAULT_INFO_ITEM = 'item'
GIT_DEPS_INFO = 'git_deps'
LIB = 'lib'
AUTHOR = 'author'
GIT_URL = 'git_url'
GIT_COMMIT = 'git_commit'
GIT_BRANCH = 'git_branch'
TIME = 'time'


class RemoteModuleParser(object):
    """dep module class"""

    def __init__(self, name=None, version=None, isLocal=True):
        self.__xmlpath = None
        self.__xmlparentpath = None
        self.is_local = isLocal
        self.done = False
        self.name = name
        self.link_name = name  # 默认也使用name作为link_name，因为外面统一用link_name来链接
        self.version = version
        self.package = None
        self.package_name = ""
        self.package_type = ""
        self.include_dir = ""
        self.lib_dir = ""
        self.sym_lib_dir = ""
        self.depslibs = []  # DepModule
        self.author = ""
        self.git_url = ""
        self.git_commit = ""
        self.git_branch = ""

    def set_xmlpath(self, xmlpath):
        """set module xml path"""
        self.__xmlpath = xmlpath
        self.is_local = False
        self.__xmlparentpath = os.path.split(self.__xmlpath)[0]

    def get_root_path(self):
        return self.__xmlparentpath

    def parse(self):
        """parse module form xml"""
        try:
            dom = xml.dom.minidom.parse(self.__xmlpath)
            root = dom.documentElement
            self.name = self.__singletag_parse(root, NAME, True)
            self.link_name = self.__singletag_parse(root, LINK_NAME, False)
            # 没配置默认用name，配置了空就用空
            if self.link_name is None:
                self.link_name = self.name
            self.version = self.__singletag_parse(root, VERSION, True)
            self.package = self.__singletag_parse(root, PACKAGE, True)
            self.include_dir = self.__singletag_parse(root, INCLUDE_DIR, False)
            self.lib_dir = self.__singletag_parse(root, LIB_DIR, False)
            self.author = self.__singletag_parse(root, AUTHOR, False)
            self.git_url = self.__singletag_parse(root, GIT_URL, False)
            self.git_commit = self.__singletag_parse(root, GIT_COMMIT, False)
            self.git_branch = self.__singletag_parse(root, GIT_BRANCH, False)

            self.sym_lib_dir = None
            try:
                self.sym_lib_dir = self.__singletag_parse(root, SYM_LIB_DIR, False)
            except BaseException, e:
                pass

            namestr = self.package
            namt_arr = namestr.split('.', 1)
            if len(namt_arr) == 2:
                self.package_name = namt_arr[0]
                self.package_type = '.' + namt_arr[1]
            else:
                self.package_name = self.package

            depstag = root.getElementsByTagName(DEPS)
            if depstag != None and len(depstag) > 0:
                for deps in depstag:
                    depslibs = deps.getElementsByTagName(LIB)
                    lens = len(depslibs)
                    if lens > 0:
                        for lib in depslibs:
                            dep_name = lib.getAttribute("name")
                            dep_version = lib.getAttribute("version")
                            # 配置了 name/version 的读取 name/version
                            if dep_name and dep_version:
                                dep = dep_name + ":" + dep_version
                            else:
                                dep = lib.childNodes[0].data
                            self.depslibs.append(dep)
                    else:
                        # dep_manager 可以没有lib属性
                        # self.exitsys('%s parse error: %s is must contains %s' % (self.xmlpath, DEPS, LIB))
                        pass
        except BaseException, e:
            self.__exitsys('%s parse error :  %s' % (self.__xmlpath, e))

    def __check_sub_dir(self, name):
        path = os.path.join(self.__xmlparentpath, name)
        path = os.path.normpath(path)
        if not os.path.isdir(path):
            return False

        return True

    def has_download(self):
        """check module has downloaded"""
        if self.include_dir and not self.__check_sub_dir(self.include_dir):
            return False
        if self.lib_dir and not self.__check_sub_dir(self.lib_dir):
            return False
        done_file = os.path.normpath(os.path.join(self.__xmlparentpath, "{}.done".format(self.name)))
        if not os.path.exists(done_file):
            return False
        return True

    def check(self):
        """check"""
        self.__checkdir()
        self.done = True

    def __checkdir(self):
        if self.include_dir:
            if self.include_dir == '.' or self.include_dir == './':
                self.__exitsys('include_dir is not support . or ./ , It must be a directory')
            self.include_dir = os.path.normpath(os.path.join(self.__xmlparentpath, self.include_dir))
            if not os.path.isdir(self.include_dir):
                self.__exitsys('include_dir is must be a directory')

        if self.lib_dir:
            if self.lib_dir == '.' or self.lib_dir == './':
                self.__exitsys('lib_dir is not support . or ./ , It must be a directory')
            self.lib_dir = os.path.normpath(os.path.join(self.__xmlparentpath, self.lib_dir))
            if not os.path.isdir(self.lib_dir):
                self.__exitsys('lib_dir is must be a directory')

        if self.sym_lib_dir:
            if self.sym_lib_dir == '.' or self.sym_lib_dir == './':
                self.__exitsys('sym_lib_dir is not support . or ./ , It must be a directory')
            self.sym_lib_dir = os.path.normpath(os.path.join(self.__xmlparentpath, self.sym_lib_dir))
            if not os.path.isdir(self.sym_lib_dir):
                self.__exitsys('sym_lib_dir is must be a directory')

        if self.include_dir and self.lib_dir:
            if self.include_dir == self.lib_dir:
                self.__exitsys('include_dir and lib_dir does not support equals')
        if self.lib_dir and self.sym_lib_dir:
            if self.lib_dir == self.sym_lib_dir:
                self.__exitsys('lib_dir and sym_lib_dir does not support equals')

    def __singletag_parse(self, root, tag_name, isexit):
        try:
            nodelist = root.getElementsByTagName(tag_name)
            lens = len(nodelist)
            if lens == 1:
                child_nodes = nodelist[0].childNodes
                chnodes_len = len(child_nodes)
                if chnodes_len > 0:
                    node0 = child_nodes[0]
                    if node0 is not None:
                        return node0.data
                    else:
                        return None
                else:
                    return ""

            elif isexit:
                if lens > 1:
                    self.__exitsys('%s singletag_parse %s error, \
                    Multiple tag %s is not support' % (self.__xmlpath, tag_name, tag_name))
                else:
                    self.__exitsys('%s singletag_parse %s error, \
                    no tag %s is not support' % (self.__xmlpath, tag_name, tag_name))
            else:
                return None
        except BaseException, exp:
            self.__exitsys('%s singletag_parse %s error ' % (self.__xmlpath, tag_name))

    def __exitsys(self, message):
        raise core.TmakeException('{}:{}'.format(self.__xmlparentpath, message))

    def print_info(self):
        """trace log"""
        core.v('---->abs xml path : %s ' % os.path.join(self.__xmlpath))
        core.i(">>>>>>>>> the project info:")
        core.i("name        : " + str(self.name))
        core.i("link_name   : " + str(self.link_name))
        core.i("version     : " + str(self.version))
        core.i("author      : " + str(self.author))
        core.i("git_url     : " + str(self.git_url))
        core.i("git_branch  : " + str(self.git_branch))
        core.i("git_commit  : " + str(self.git_commit))
        core.i("include_dir : " + str(self.include_dir))
        core.i("lib_dir     : " + str(self.lib_dir))
        core.i("sym_lib_dir : " + str(self.sym_lib_dir))
        core.i("package     : " + str("{}.zip".format(self.package_name)))

    def __str__(self):
        return "id={}, name={}, link_name={}, version={}, deps={}, include={}".format(id(self),
                                                                                      self.name,
                                                                                      self.link_name,
                                                                                      self.version,
                                                                                      self.depslibs,
                                                                                      self.include_dir)


# eg
if __name__ == "__main__":
    PATH = os.path.join(os.getcwd(), 'tmake.xml')
    # core.v(PATH)
    # DEP_MODULE = DepModule(PATH)
    # DEP_MODULE.parse()
    # DEP_MODULE.tracelog('')
